"""Permutation-equivariant molecular interaction and thermodynamic decoders."""

from __future__ import annotations

import math
from dataclasses import asdict, dataclass
from typing import Literal

import torch
from torch import Tensor, nn


@dataclass
class ModelOutputs:
    log_gamma: Tensor
    log_psat: Tensor
    nonideality_tokens: Tensor | None = None
    excess_gibbs_rt: Tensor | None = None
    pair_interactions: Tensor | None = None


@dataclass
class DirectVLEOutputs:
    pressure_kpa: Tensor
    temperature_k: Tensor
    y: Tensor


@dataclass(frozen=True)
class ThermoFormerConfig:
    """Architecture hyperparameters and explicit ablation switches."""

    feature_dim: int | None = None
    hidden_dim: int = 192
    layers: int = 3
    heads: int = 6
    feedforward_multiplier: int = 4
    dropout: float = 0.0
    pair_hidden_dim: int = 0
    pure_hidden_dim: int = 0
    film_scale: float = 0.1
    use_transformer: bool = True
    use_mixture_token: bool = True
    use_film: bool = True
    use_composition_context: bool = True
    interaction_mode: Literal["full", "pairwise", "independent"] = "full"
    activity_mode: Literal["excess_gibbs", "direct_gamma", "ideal"] = "excess_gibbs"
    decoder_mode: Literal["thermodynamic", "direct_vle"] = "thermodynamic"

    def __post_init__(self) -> None:
        integer_values = (
            self.hidden_dim,
            self.layers,
            self.heads,
            self.feedforward_multiplier,
            self.pair_hidden_dim,
            self.pure_hidden_dim,
        )
        if self.feature_dim is not None:
            integer_values = (self.feature_dim, *integer_values)
        if any(not isinstance(value, int) or isinstance(value, bool) for value in integer_values):
            raise ValueError("ThermoFormer dimensions, layers, and heads must be integers")
        numeric_values = (self.dropout, self.film_scale)
        if any(
            not isinstance(value, (int, float))
            or isinstance(value, bool)
            or not math.isfinite(value)
            for value in numeric_values
        ):
            raise ValueError("dropout and film_scale must be finite numbers")
        if any(
            not isinstance(value, bool)
            for value in (
                self.use_transformer,
                self.use_mixture_token,
                self.use_film,
                self.use_composition_context,
            )
        ):
            raise ValueError("ThermoFormer ablation switches must be booleans")
        if self.feature_dim is not None and self.feature_dim < 1:
            raise ValueError("feature_dim must be positive when specified")
        if self.hidden_dim < 1:
            raise ValueError("hidden_dim must be positive")
        if self.heads < 1 or self.hidden_dim % self.heads:
            raise ValueError("hidden_dim must be divisible by a positive heads value")
        if self.use_transformer and self.layers < 1:
            raise ValueError("layers must be positive when the Transformer is enabled")
        if self.layers < 0 or self.feedforward_multiplier < 1:
            raise ValueError("layers cannot be negative and feedforward_multiplier must be positive")
        if not 0.0 <= self.dropout < 1.0:
            raise ValueError("dropout must be in [0, 1)")
        if self.pair_hidden_dim < 0 or self.pure_hidden_dim < 0 or self.film_scale < 0.0:
            raise ValueError("head dimensions and film_scale cannot be negative")
        if self.interaction_mode not in ("full", "pairwise", "independent"):
            raise ValueError("interaction_mode must be full, pairwise, or independent")
        if self.activity_mode not in ("excess_gibbs", "direct_gamma", "ideal"):
            raise ValueError("activity_mode must be excess_gibbs, direct_gamma, or ideal")
        if self.decoder_mode not in ("thermodynamic", "direct_vle"):
            raise ValueError("decoder_mode must be thermodynamic or direct_vle")

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class PureVaporPressure(nn.Module):
    """Monotonic learned Clausius-Clapeyron branch in kPa."""

    def __init__(self, hidden_dim: int, head_hidden_dim: int | None = None) -> None:
        super().__init__()
        head_hidden_dim = head_hidden_dim or hidden_dim
        self.parameter_head = nn.Sequential(
            nn.Linear(hidden_dim, head_hidden_dim),
            nn.GELU(),
            nn.Linear(head_hidden_dim, 2),
        )
        output = self.parameter_head[-1]
        nn.init.zeros_(output.weight)
        with torch.no_grad():
            output.bias.copy_(torch.tensor([12.0, 2.4]))

    def forward(self, molecular_tokens: Tensor, temperature_k: Tensor) -> Tensor:
        raw = self.parameter_head(molecular_tokens)
        intercept = raw[..., 0]
        inverse_temperature = 1000.0 * torch.nn.functional.softplus(raw[..., 1]) + 1.0
        temperature = temperature_k.clamp_min(100.0).expand(molecular_tokens.shape[:2])
        return intercept - inverse_temperature / temperature


class ThermoFormer(nn.Module):
    """Binary/ternary interaction model with distinct gamma and Psat branches.

    Activity coefficients are derived from a learned dimensionless excess-Gibbs
    potential. This makes the component outputs thermodynamically coupled and
    anchors the present pure component at ``gamma=1`` by construction.
    """

    def __init__(self, config: ThermoFormerConfig) -> None:
        super().__init__()
        self.config = config
        if config.feature_dim is None:
            raise ValueError("ThermoFormerConfig.feature_dim must be resolved before model construction")
        feature_dim = config.feature_dim
        hidden_dim = config.hidden_dim
        self.molecular_encoder = nn.Sequential(
            nn.Linear(feature_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, hidden_dim),
            nn.LayerNorm(hidden_dim),
        )
        full_interaction = config.interaction_mode == "full"
        if full_interaction and config.use_mixture_token:
            self.mixture_token = nn.Parameter(torch.zeros(1, 1, hidden_dim))
        else:
            self.register_parameter("mixture_token", None)
        if full_interaction and config.use_transformer:
            layer = nn.TransformerEncoderLayer(
                d_model=hidden_dim,
                nhead=config.heads,
                dim_feedforward=config.feedforward_multiplier * hidden_dim,
                dropout=config.dropout,
                activation="gelu",
                batch_first=True,
                norm_first=True,
            )
            self.interaction: nn.Module | None = nn.TransformerEncoder(
                layer,
                num_layers=config.layers,
                enable_nested_tensor=False,
            )
        else:
            self.interaction = None
        self.film = nn.Sequential(
            nn.Linear(hidden_dim + 3, hidden_dim),
            nn.GELU(),
            nn.Linear(hidden_dim, 2 * hidden_dim),
        )
        self.condition_projection: nn.Module | None = None
        if not config.use_film:
            self.condition_projection = nn.Sequential(
                nn.Linear(hidden_dim + 3, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, hidden_dim),
                nn.LayerNorm(hidden_dim),
            )
        pair_hidden_dim = config.pair_hidden_dim or hidden_dim
        self.pair_potential: nn.Module | None = None
        self.component_potential: nn.Module | None = None
        self.direct_activity_head: nn.Module | None = None
        self.vapor_pressure: PureVaporPressure | None = None
        self.direct_state_head: nn.Module | None = None
        self.direct_y_head: nn.Module | None = None
        if config.decoder_mode == "thermodynamic":
            if config.interaction_mode == "independent":
                self.component_potential = nn.Sequential(
                    nn.Linear(hidden_dim, pair_hidden_dim),
                    nn.GELU(),
                    nn.Linear(pair_hidden_dim, 1),
                )
            else:
                self.pair_potential = nn.Sequential(
                    nn.Linear(3 * hidden_dim, pair_hidden_dim),
                    nn.GELU(),
                    nn.Linear(pair_hidden_dim, 1),
                )
            if config.activity_mode == "direct_gamma":
                self.direct_activity_head = nn.Sequential(
                    nn.Linear(2 * hidden_dim, pair_hidden_dim),
                    nn.GELU(),
                    nn.Linear(pair_hidden_dim, 1),
                )
            self.vapor_pressure = PureVaporPressure(
                hidden_dim,
                config.pure_hidden_dim or hidden_dim,
            )
        else:
            self.direct_state_head = nn.Sequential(
                nn.Linear(hidden_dim + 3, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, 1),
            )
            self.direct_y_head = nn.Sequential(
                nn.Linear(2 * hidden_dim + 2, hidden_dim),
                nn.GELU(),
                nn.Linear(hidden_dim, 1),
            )

    def pure_log_psat(self, molecules: Tensor, temperature_k: Tensor) -> Tensor:
        if self.vapor_pressure is None:
            raise RuntimeError("Direct-VLE models do not contain a vapor-pressure decoder")
        molecular_tokens = self.molecular_encoder(molecules)
        return self.vapor_pressure(molecular_tokens, temperature_k)

    def _structural_context(self, molecular_tokens: Tensor, mask: Tensor) -> tuple[Tensor, Tensor]:
        batch = molecular_tokens.shape[0]
        masked_mean = (molecular_tokens * mask.unsqueeze(-1)).sum(1, keepdim=True)
        masked_mean = masked_mean / mask.sum(-1, keepdim=True).clamp_min(1.0).unsqueeze(-1)
        learned_mixture = (
            self.mixture_token.expand(batch, -1, -1)
            if self.mixture_token is not None
            else masked_mean
        )
        if self.interaction is None:
            return molecular_tokens * mask.unsqueeze(-1), learned_mixture
        if self.mixture_token is None:
            interacted = self.interaction(molecular_tokens, src_key_padding_mask=~mask.bool())
            mixture = (interacted * mask.unsqueeze(-1)).sum(1, keepdim=True)
            mixture = mixture / mask.sum(-1, keepdim=True).clamp_min(1.0).unsqueeze(-1)
            return interacted * mask.unsqueeze(-1), mixture
        sequence = torch.cat([learned_mixture, molecular_tokens], dim=1)
        padding = torch.cat(
            [torch.zeros(batch, 1, dtype=torch.bool, device=mask.device), ~mask.bool()],
            dim=1,
        )
        interacted = self.interaction(sequence, src_key_padding_mask=padding)
        return interacted[:, 1:] * mask.unsqueeze(-1), interacted[:, :1]

    def _nonideality_tokens(
        self,
        components: Tensor,
        mixture: Tensor,
        temperature_k: Tensor,
        pressure_kpa: Tensor,
        x: Tensor,
        mask: Tensor,
    ) -> tuple[Tensor, Tensor]:
        normalized_x = x * mask
        normalized_x = normalized_x / normalized_x.sum(-1, keepdim=True).clamp_min(1e-8)
        composition_context = (normalized_x.unsqueeze(-1) * components).sum(1, keepdim=True)
        if self.config.interaction_mode != "full":
            context = components
        elif self.config.use_composition_context:
            composition_context = 0.5 * (composition_context + mixture)
            context = composition_context.expand_as(components)
        else:
            composition_context = mixture
            context = composition_context.expand_as(components)
        temperature = ((temperature_k - 350.0) / 150.0).expand_as(x).unsqueeze(-1)
        pressure = torch.log(pressure_kpa.clamp_min(1e-6) / 101.325).expand_as(x).unsqueeze(-1)
        condition = torch.cat([context, temperature, pressure, x.unsqueeze(-1)], dim=-1)
        if self.config.use_film:
            scale, shift = self.film(condition).chunk(2, dim=-1)
            tokens = components * (
                1.0 + self.config.film_scale * torch.tanh(scale)
            ) + shift
        else:
            if self.condition_projection is None:
                raise RuntimeError("Condition concatenation projection is unavailable")
            tokens = self.condition_projection(condition)
        return tokens * mask.unsqueeze(-1), composition_context

    def _excess_gibbs(
        self,
        tokens: Tensor,
        context: Tensor,
        x: Tensor,
        mask: Tensor,
    ) -> tuple[Tensor, Tensor | None]:
        if self.config.interaction_mode == "independent":
            if self.component_potential is None:
                raise RuntimeError("Independent component potential is unavailable")
            unary = self.component_potential(tokens).squeeze(-1) * mask
            total = (x * (1.0 - x) * unary).sum(-1, keepdim=True)
            return total, None
        if self.pair_potential is None:
            raise RuntimeError("Pair interaction potential is unavailable")
        total = torch.zeros(x.shape[0], 1, dtype=x.dtype, device=x.device)
        component_count = x.shape[1]
        pair_interactions = torch.zeros(
            x.shape[0], component_count, component_count, dtype=x.dtype, device=x.device
        )
        for first in range(component_count):
            for second in range(first + 1, component_count):
                pair_mask = (mask[:, first] * mask[:, second]).unsqueeze(-1)
                pair_context = (
                    context.squeeze(1)
                    if self.config.interaction_mode == "full"
                    else 0.5 * (tokens[:, first] + tokens[:, second])
                )
                pair = torch.cat(
                    [
                        tokens[:, first] + tokens[:, second],
                        torch.abs(tokens[:, first] - tokens[:, second]),
                        pair_context,
                    ],
                    dim=-1,
                )
                interaction = self.pair_potential(pair) * pair_mask
                pair_interactions[:, first, second] = interaction.squeeze(-1)
                pair_interactions[:, second, first] = interaction.squeeze(-1)
                total = total + (x[:, first] * x[:, second]).unsqueeze(-1) * interaction
        return total, pair_interactions

    def forward(
        self,
        molecules: Tensor,
        temperature_k: Tensor,
        pressure_kpa: Tensor,
        x: Tensor,
        mask: Tensor,
    ) -> ModelOutputs:
        if self.config.decoder_mode != "thermodynamic":
            raise RuntimeError("Use predict_direct for a direct-VLE model")
        if molecules.shape[1] not in (2, 3):
            raise ValueError("ThermoFormer supports binary and ternary mixtures only")
        molecular_tokens = self.molecular_encoder(molecules)
        if self.vapor_pressure is None:
            raise RuntimeError("Thermodynamic decoder is unavailable")
        log_psat = self.vapor_pressure(molecular_tokens, temperature_k) * mask
        components, mixture = self._structural_context(molecular_tokens, mask)

        if self.config.activity_mode == "ideal":
            return ModelOutputs(
                log_gamma=torch.zeros_like(x) * mask,
                log_psat=log_psat,
                nonideality_tokens=components,
                excess_gibbs_rt=torch.zeros(x.shape[0], 1, dtype=x.dtype, device=x.device),
                pair_interactions=None,
            )

        outer_grad_enabled = torch.is_grad_enabled()
        with torch.enable_grad():
            x_variable = x if x.requires_grad else x.detach().clone().requires_grad_(True)
            tokens, context = self._nonideality_tokens(
                components,
                mixture,
                temperature_k,
                pressure_kpa,
                x_variable,
                mask,
            )
            if self.config.activity_mode == "direct_gamma":
                if self.direct_activity_head is None:
                    raise RuntimeError("Direct activity decoder is unavailable")
                activity_context = context.expand_as(tokens)
                raw_log_gamma = self.direct_activity_head(
                    torch.cat([tokens, activity_context], dim=-1)
                ).squeeze(-1)
                log_gamma = raw_log_gamma * (1.0 - x_variable) * mask
                excess_gibbs = None
                pair_interactions = None
            else:
                excess_gibbs, pair_interactions = self._excess_gibbs(
                    tokens, context, x_variable, mask
                )
                composition_gradient = torch.autograd.grad(
                    excess_gibbs.sum(),
                    x_variable,
                    create_graph=outer_grad_enabled,
                    retain_graph=outer_grad_enabled,
                )[0]
                weighted_gradient = (x_variable * composition_gradient * mask).sum(-1, keepdim=True)
                log_gamma = (excess_gibbs + composition_gradient - weighted_gradient) * mask

        if not outer_grad_enabled:
            log_gamma = log_gamma.detach()
            tokens = tokens.detach()
            if excess_gibbs is not None:
                excess_gibbs = excess_gibbs.detach()
            if pair_interactions is not None:
                pair_interactions = pair_interactions.detach()
        return ModelOutputs(
            log_gamma=log_gamma,
            log_psat=log_psat,
            nonideality_tokens=tokens,
            excess_gibbs_rt=excess_gibbs,
            pair_interactions=pair_interactions,
        )

    def predict_direct(
        self,
        molecules: Tensor,
        temperature_k: Tensor,
        pressure_kpa: Tensor,
        x: Tensor,
        mask: Tensor,
        *,
        direction: Literal["isothermal", "isobaric"],
    ) -> DirectVLEOutputs:
        """Predict a bounded bubble state without gamma, Psat, or VLE equations."""
        if self.config.decoder_mode != "direct_vle":
            raise RuntimeError("predict_direct requires decoder_mode='direct_vle'")
        if direction not in ("isothermal", "isobaric"):
            raise ValueError("direction must be isothermal or isobaric")
        if self.direct_state_head is None or self.direct_y_head is None:
            raise RuntimeError("Direct-VLE heads are unavailable")
        molecular_tokens = self.molecular_encoder(molecules)
        components, mixture = self._structural_context(molecular_tokens, mask)
        model_temperature = (
            temperature_k if direction == "isothermal" else torch.full_like(temperature_k, 350.0)
        )
        model_pressure = (
            torch.full_like(pressure_kpa, 101.325) if direction == "isothermal" else pressure_kpa
        )
        tokens, _ = self._nonideality_tokens(
            components, mixture, model_temperature, model_pressure, x, mask
        )
        normalized_x = x * mask
        normalized_x = normalized_x / normalized_x.sum(-1, keepdim=True).clamp_min(1e-8)
        pooled = (normalized_x.unsqueeze(-1) * tokens).sum(1)
        temperature_feature = (model_temperature - 350.0) / 150.0
        pressure_feature = torch.log(model_pressure.clamp_min(1e-6) / 101.325)
        direction_feature = torch.full_like(
            temperature_feature, 1.0 if direction == "isothermal" else -1.0
        )
        raw_state = self.direct_state_head(
            torch.cat([pooled, temperature_feature, pressure_feature, direction_feature], dim=-1)
        )
        predicted_pressure = torch.exp(
            math.log(101.325) + raw_state.clamp(min=-5.0, max=5.0)
        )
        predicted_temperature = 150.0 + 1350.0 * torch.sigmoid(raw_state)
        global_context = pooled.unsqueeze(1).expand_as(tokens)
        component_direction = direction_feature.expand_as(x).unsqueeze(-1)
        y_logits = self.direct_y_head(
            torch.cat(
                [tokens, global_context, x.unsqueeze(-1), component_direction], dim=-1
            )
        ).squeeze(-1)
        y = torch.softmax(y_logits.masked_fill(~mask.bool(), -1e9), dim=-1) * mask
        return DirectVLEOutputs(
            pressure_kpa=(predicted_pressure if direction == "isothermal" else pressure_kpa),
            temperature_k=(temperature_k if direction == "isothermal" else predicted_temperature),
            y=y,
        )
