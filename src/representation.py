"""Versioned molecular representations with deterministic, non-pickle caches."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def rdkit_descriptor_definition_path() -> Path:
    return PROJECT_ROOT / "assets" / "rdkit_descriptors.json"


def functional_group_vocabulary_path() -> Path:
    return PROJECT_ROOT / "assets" / "functional_groups.json"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class RDKit2DEncoder:
    """Deterministic raw values for the frozen ThermoFormer RDKit-24 set."""

    _DESCRIPTORS = (
        ("MolWt", 500.0),
        ("MolLogP", 10.0),
        ("TPSA", 200.0),
        ("NumHDonors", 10.0),
        ("NumHAcceptors", 20.0),
        ("NumRotatableBonds", 20.0),
        ("RingCount", 10.0),
        ("NumAromaticRings", 10.0),
        ("NumAliphaticRings", 10.0),
        ("FractionCSP3", 1.0),
        ("HeavyAtomCount", 100.0),
        ("NHOHCount", 20.0),
        ("NOCount", 20.0),
        ("NumHeteroatoms", 50.0),
        ("NumValenceElectrons", 500.0),
        ("MolMR", 200.0),
        ("MaxPartialCharge", 2.0),
        ("MinPartialCharge", 2.0),
        ("NumRadicalElectrons", 5.0),
        ("BertzCT", 2000.0),
        ("BalabanJ", 10.0),
        ("Chi0v", 50.0),
        ("Kappa1", 50.0),
        ("LabuteASA", 500.0),
    )

    _MODEL_SIZE = "raw24_v1"

    def __init__(self, cache_path: Path, definition_path: Path | None = None) -> None:
        self.cache_path = cache_path
        self.definition_path = definition_path or rdkit_descriptor_definition_path()
        payload = json.loads(self.definition_path.read_text(encoding="utf-8"))
        self.feature_names = tuple(str(name) for name in payload["descriptors"])
        expected = tuple(name for name, _ in self._DESCRIPTORS)
        if self.feature_names != expected:
            raise ValueError("RDKit descriptor asset does not match the frozen RDKit-24 set")
        self.definition_sha256 = _sha256(self.definition_path)

    def _load_cache(self) -> dict[str, np.ndarray]:
        if not self.cache_path.exists():
            return {}
        with np.load(self.cache_path, allow_pickle=False) as cache:
            if str(cache["model"].item()) != "rdkit_2d":
                return {}
            if str(cache["model_size"].item()) != self._MODEL_SIZE:
                return {}
            if str(cache["definition_sha256"].item()) != self.definition_sha256:
                return {}
            smiles = cache["smiles"].astype(str).tolist()
            features = np.asarray(cache["features"], dtype=np.float32)
        if features.ndim != 2 or len(smiles) != len(features):
            raise ValueError(f"Invalid RDKit descriptor cache: {self.cache_path}")
        return {smile: features[index] for index, smile in enumerate(smiles)}

    @classmethod
    def _describe(cls, smiles: str) -> np.ndarray:
        from rdkit import Chem
        from rdkit.Chem import Descriptors

        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise ValueError(f"RDKit could not parse SMILES: {smiles}")
        values = []
        for name, _ in cls._DESCRIPTORS:
            descriptor = getattr(Descriptors, name)
            value = float(descriptor(molecule))
            values.append(value if np.isfinite(value) else 0.0)
        return np.asarray(values, dtype=np.float32)

    def _save_cache(self, features: dict[str, np.ndarray]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(features)
        np.savez_compressed(
            self.cache_path,
            smiles=np.asarray(ordered),
            features=np.stack([features[smile] for smile in ordered]).astype(np.float32),
            model=np.asarray("rdkit_2d"),
            model_size=np.asarray(self._MODEL_SIZE),
            descriptor_names=np.asarray(self.feature_names),
            definition_sha256=np.asarray(self.definition_sha256),
        )

    def encode(self, smiles: Sequence[str]) -> dict[str, np.ndarray]:
        requested = sorted({value.strip() for value in smiles if value.strip()})
        if not requested:
            raise ValueError("At least one non-empty SMILES is required")
        cached = self._load_cache()
        missing = [value for value in requested if value not in cached]
        for value in missing:
            cached[value] = self._describe(value)
        if missing:
            self._save_cache(cached)
        return {smile: cached[smile] for smile in requested}


class FunctionalGroupEncoder:
    """Audited SMARTS occurrence counts with a versioned, immutable vocabulary."""

    _MODEL_SIZE = "thermoformer_functional_groups_v1"

    def __init__(self, cache_path: Path, vocabulary_path: Path | None = None) -> None:
        from rdkit import Chem

        self.cache_path = cache_path
        self.vocabulary_path = vocabulary_path or functional_group_vocabulary_path()
        payload = json.loads(self.vocabulary_path.read_text(encoding="utf-8"))
        groups = payload.get("groups", [])
        self.feature_names = tuple(str(group["name"]) for group in groups)
        if not self.feature_names or len(set(self.feature_names)) != len(self.feature_names):
            raise ValueError("Functional-group vocabulary names must be non-empty and unique")
        self.smarts = tuple(str(group["smarts"]) for group in groups)
        self.patterns = tuple(Chem.MolFromSmarts(value) for value in self.smarts)
        invalid = [name for name, pattern in zip(self.feature_names, self.patterns) if pattern is None]
        if invalid:
            raise ValueError(f"Invalid functional-group SMARTS: {', '.join(invalid)}")
        self.vocabulary_sha256 = _sha256(self.vocabulary_path)

    def _load_cache(self) -> dict[str, np.ndarray]:
        if not self.cache_path.exists():
            return {}
        with np.load(self.cache_path, allow_pickle=False) as cache:
            if str(cache["model"].item()) != "functional_groups":
                return {}
            if str(cache["model_size"].item()) != self._MODEL_SIZE:
                return {}
            if str(cache["vocabulary_sha256"].item()) != self.vocabulary_sha256:
                return {}
            names = tuple(cache["feature_names"].astype(str).tolist())
            if names != self.feature_names:
                return {}
            smiles = cache["smiles"].astype(str).tolist()
            features = np.asarray(cache["counts"], dtype=np.float32)
            presence = np.asarray(cache["presence"], dtype=np.uint8)
        expected = (len(smiles), len(self.feature_names))
        if features.shape != expected or presence.shape != expected:
            raise ValueError(f"Invalid functional-group cache: {self.cache_path}")
        if not np.array_equal(presence, features > 0.0):
            raise ValueError("Functional-group count and presence cache entries disagree")
        return {smile: features[index] for index, smile in enumerate(smiles)}

    def _describe(self, smiles: str) -> np.ndarray:
        from rdkit import Chem

        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise ValueError(f"RDKit could not parse SMILES: {smiles}")
        values = [
            float(len(molecule.GetSubstructMatches(pattern, uniquify=True)))
            for pattern in self.patterns
        ]
        return np.asarray(values, dtype=np.float32)

    def _save_cache(self, features: dict[str, np.ndarray]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(features)
        counts = np.stack([features[smile] for smile in ordered]).astype(np.float32)
        np.savez_compressed(
            self.cache_path,
            smiles=np.asarray(ordered),
            features=counts,
            counts=counts,
            presence=(counts > 0.0).astype(np.uint8),
            feature_names=np.asarray(self.feature_names),
            smarts=np.asarray(self.smarts),
            vocabulary_sha256=np.asarray(self.vocabulary_sha256),
            model=np.asarray("functional_groups"),
            model_size=np.asarray(self._MODEL_SIZE),
        )

    def encode(self, smiles: Sequence[str]) -> dict[str, np.ndarray]:
        requested = sorted({value.strip() for value in smiles if value.strip()})
        if not requested:
            raise ValueError("At least one non-empty SMILES is required")
        cached = self._load_cache()
        missing = [value for value in requested if value not in cached]
        for value in missing:
            cached[value] = self._describe(value)
        if missing:
            self._save_cache(cached)
        return {smile: cached[smile] for smile in requested}


@dataclass(frozen=True)
class RDKitDescriptorScaler:
    """Train-partition-only standardization for the frozen descriptor vector."""

    mean: np.ndarray
    std: np.ndarray
    descriptor_names: tuple[str, ...]
    fit_smiles: tuple[str, ...]

    @classmethod
    def fit(
        cls,
        raw_features: dict[str, np.ndarray],
        train_smiles: Sequence[str],
        descriptor_names: Sequence[str],
    ) -> "RDKitDescriptorScaler":
        fitted = tuple(sorted({value for value in train_smiles if value in raw_features}))
        if not fitted:
            raise ValueError("RDKit scaler requires at least one training molecule")
        matrix = np.stack([raw_features[value] for value in fitted]).astype(np.float64)
        if matrix.shape[1] != len(descriptor_names) or not np.isfinite(matrix).all():
            raise ValueError("RDKit scaler received invalid descriptor values")
        mean = matrix.mean(axis=0)
        std = matrix.std(axis=0)
        std = np.where(std > 1e-12, std, 1.0)
        return cls(
            mean=mean.astype(np.float32),
            std=std.astype(np.float32),
            descriptor_names=tuple(descriptor_names),
            fit_smiles=fitted,
        )

    def transform(self, values: np.ndarray) -> np.ndarray:
        array = np.asarray(values, dtype=np.float32)
        if array.shape[-1] != len(self.descriptor_names):
            raise ValueError("RDKit descriptor dimension does not match the fitted scaler")
        transformed = (array - self.mean) / self.std
        if not np.isfinite(transformed).all():
            raise ValueError("RDKit standardization produced a non-finite value")
        return transformed.astype(np.float32)

    def to_dict(self) -> dict[str, object]:
        payload = {
            "mean": self.mean.tolist(),
            "std": self.std.tolist(),
            "descriptor_names": list(self.descriptor_names),
            "fit_smiles": list(self.fit_smiles),
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        return {**payload, "sha256": hashlib.sha256(encoded).hexdigest()}


class UniMolV2Encoder:
    """Encode unique SMILES with Uni-Mol v2 ``cls_repr`` vectors."""

    def __init__(
        self,
        cache_path: Path,
        batch_size: int = 16,
        model_size: str = "84m",
        use_cuda: bool | None = None,
        backend_factory: Callable[..., object] | None = None,
    ) -> None:
        self.cache_path = cache_path
        self.batch_size = batch_size
        self.model_size = model_size
        self.use_cuda = use_cuda
        self._backend_factory = backend_factory

    def _load_cache(self) -> dict[str, np.ndarray]:
        if not self.cache_path.exists():
            return {}
        with np.load(self.cache_path, allow_pickle=False) as cache:
            model = str(cache["model"].item())
            model_size = str(cache["model_size"].item())
            if model != "unimolv2" or model_size != self.model_size:
                return {}
            smiles = cache["smiles"].astype(str).tolist()
            features = np.asarray(cache["features"], dtype=np.float32)
        if features.ndim != 2 or len(smiles) != len(features):
            raise ValueError(f"Invalid Uni-Mol cache: {self.cache_path}")
        return {smile: features[index] for index, smile in enumerate(smiles)}

    def _make_backend(self) -> object:
        if self._backend_factory is None:
            from unimol_tools import UniMolRepr

            factory: Callable[..., object] = UniMolRepr
        else:
            factory = self._backend_factory
        options = {
            "data_type": "molecule",
            "model_name": "unimolv2",
            "model_size": self.model_size,
            "batch_size": self.batch_size,
        }
        if self.use_cuda is not None:
            options["use_cuda"] = self.use_cuda
        return factory(**options)

    def _save_cache(self, features: dict[str, np.ndarray]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(features)
        matrix = np.stack([features[smile] for smile in ordered]).astype(np.float32)
        np.savez_compressed(
            self.cache_path,
            smiles=np.asarray(ordered),
            features=matrix,
            model=np.asarray("unimolv2"),
            model_size=np.asarray(self.model_size),
        )

    def encode(self, smiles: Sequence[str]) -> dict[str, np.ndarray]:
        requested = sorted({value.strip() for value in smiles if value.strip()})
        if not requested:
            raise ValueError("At least one non-empty SMILES is required")
        cached = self._load_cache()
        missing = [value for value in requested if value not in cached]
        if missing:
            backend = self._make_backend()
            for start in range(0, len(missing), self.batch_size):
                chunk = missing[start : start + self.batch_size]
                result = backend.get_repr(chunk, return_atomic_reprs=False)
                if not isinstance(result, dict) or "cls_repr" not in result:
                    raise TypeError("Uni-Mol v2 get_repr must return a dictionary containing 'cls_repr'")
                embeddings = np.asarray(result["cls_repr"], dtype=np.float32)
                if embeddings.ndim != 2 or embeddings.shape[0] != len(chunk):
                    raise ValueError(
                        f"Uni-Mol returned shape {embeddings.shape} for {len(chunk)} molecules"
                    )
                cached.update({smile: embeddings[index] for index, smile in enumerate(chunk)})
            self._save_cache(cached)
        return {smile: cached[smile] for smile in requested}


class HybridMolecularEncoder:
    """Concatenate physical, pretrained 3D, and functional-group features."""

    _BRANCH_ORDER = ("rdkit_2d", "unimol_v2", "functional_groups")

    def __init__(
        self,
        cache_path: Path,
        batch_size: int = 16,
        model_size: str = "84m",
        use_cuda: bool | None = None,
        backend_factory: Callable[..., object] | None = None,
        use_rdkit_descriptors: bool = True,
        use_unimol: bool = True,
        use_functional_groups: bool = True,
    ) -> None:
        self.cache_path = cache_path
        self.batch_size = batch_size
        self.model_size = model_size
        self.use_cuda = use_cuda
        self._backend_factory = backend_factory
        enabled = {
            "rdkit_2d": use_rdkit_descriptors,
            "unimol_v2": use_unimol,
            "functional_groups": use_functional_groups,
        }
        self.enabled_branches = tuple(name for name in self._BRANCH_ORDER if enabled[name])
        if not self.enabled_branches:
            raise ValueError("Hybrid molecular representation requires at least one branch")
        self.feature_block_sizes: dict[str, int] = {}

    @property
    def _signature(self) -> str:
        return "+".join(
            {
                "rdkit_2d": "rdkit_raw24_v1",
                "unimol_v2": f"unimolv2_{self.model_size}",
                "functional_groups": FunctionalGroupEncoder._MODEL_SIZE,
            }[name]
            for name in self.enabled_branches
        )

    def _load_cache(self) -> dict[str, np.ndarray]:
        if not self.cache_path.exists():
            return {}
        with np.load(self.cache_path, allow_pickle=False) as cache:
            if str(cache["model"].item()) != "hybrid_molecular":
                return {}
            if str(cache["model_size"].item()) != self._signature:
                return {}
            branch_names = tuple(cache["branch_names"].astype(str).tolist())
            branch_dims = cache["branch_dims"].astype(int).tolist()
            if branch_names != self.enabled_branches:
                return {}
            smiles = cache["smiles"].astype(str).tolist()
            features = np.asarray(cache["features"], dtype=np.float32)
        self.feature_block_sizes = dict(zip(branch_names, branch_dims))
        if features.shape != (len(smiles), sum(branch_dims)):
            raise ValueError(f"Invalid hybrid molecular cache: {self.cache_path}")
        return {smile: features[index] for index, smile in enumerate(smiles)}

    def _branch_encoders(self) -> dict[str, object]:
        cache_root = self.cache_path.parent
        return {
            "rdkit_2d": RDKit2DEncoder(cache_root / "rdkit_2d_raw24_v1.npz"),
            "unimol_v2": UniMolV2Encoder(
                cache_root / f"unimolv2_{self.model_size}.npz",
                batch_size=self.batch_size,
                model_size=self.model_size,
                use_cuda=self.use_cuda,
                backend_factory=self._backend_factory,
            ),
            "functional_groups": FunctionalGroupEncoder(
                cache_root / "functional_groups_thermoformer_v1.npz"
            ),
        }

    def _save_cache(self, features: dict[str, np.ndarray]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(features)
        np.savez_compressed(
            self.cache_path,
            smiles=np.asarray(ordered),
            features=np.stack([features[smile] for smile in ordered]).astype(np.float32),
            branch_names=np.asarray(tuple(self.feature_block_sizes)),
            branch_dims=np.asarray(tuple(self.feature_block_sizes.values()), dtype=np.int64),
            model=np.asarray("hybrid_molecular"),
            model_size=np.asarray(self._signature),
        )

    def encode(self, smiles: Sequence[str]) -> dict[str, np.ndarray]:
        requested = sorted({value.strip() for value in smiles if value.strip()})
        if not requested:
            raise ValueError("At least one non-empty SMILES is required")
        cached = self._load_cache()
        missing = [value for value in requested if value not in cached]
        if missing:
            encoders = self._branch_encoders()
            branch_features = {
                name: encoders[name].encode(missing) for name in self.enabled_branches
            }
            self.feature_block_sizes = {
                name: int(branch_features[name][missing[0]].shape[0])
                for name in self.enabled_branches
            }
            for smile in missing:
                cached[smile] = np.concatenate(
                    [branch_features[name][smile] for name in self.enabled_branches]
                ).astype(np.float32)
            self._save_cache(cached)
        return {smile: cached[smile] for smile in requested}


@dataclass(frozen=True)
class PreparedMolecularFeatures:
    values: dict[str, np.ndarray]
    view_dimensions: dict[str, int]
    metadata: dict[str, object]


def prepare_partition_features(
    encoder: object,
    all_smiles: Sequence[str],
    train_smiles: Sequence[str],
) -> PreparedMolecularFeatures:
    """Encode all molecules while fitting RDKit statistics on training molecules only."""

    if not hasattr(encoder, "encode"):
        raise TypeError("Molecular encoder must expose encode(smiles)")
    raw = encoder.encode(all_smiles)
    if not raw:
        raise ValueError("Molecular feature map is empty")
    total_dim = int(next(iter(raw.values())).shape[0])
    view_dimensions = {"rdkit_2d": 0, "unimol_v2": 0, "functional_groups": 0}
    if isinstance(encoder, HybridMolecularEncoder):
        view_dimensions.update(encoder.feature_block_sizes)
        block_order = encoder.enabled_branches
    elif isinstance(encoder, RDKit2DEncoder):
        view_dimensions["rdkit_2d"] = total_dim
        block_order = ("rdkit_2d",)
    elif isinstance(encoder, UniMolV2Encoder):
        view_dimensions["unimol_v2"] = total_dim
        block_order = ("unimol_v2",)
    elif isinstance(encoder, FunctionalGroupEncoder):
        view_dimensions["functional_groups"] = total_dim
        block_order = ("functional_groups",)
    else:
        raise TypeError(f"Unsupported molecular encoder type: {type(encoder).__name__}")

    values = {name: np.asarray(vector, dtype=np.float32).copy() for name, vector in raw.items()}
    metadata: dict[str, object] = {
        "view_dimensions": view_dimensions,
        "block_order": list(block_order),
    }
    source_paths: dict[str, Path] = {}
    if isinstance(encoder, HybridMolecularEncoder):
        source_paths = {
            "rdkit_2d": encoder.cache_path.parent / "rdkit_2d_raw24_v1.npz",
            "unimol_v2": encoder.cache_path.parent / f"unimolv2_{encoder.model_size}.npz",
            "functional_groups": (
                encoder.cache_path.parent / "functional_groups_thermoformer_v1.npz"
            ),
        }
    elif isinstance(encoder, RDKit2DEncoder):
        source_paths = {"rdkit_2d": encoder.cache_path}
    elif isinstance(encoder, UniMolV2Encoder):
        source_paths = {"unimol_v2": encoder.cache_path}
    elif isinstance(encoder, FunctionalGroupEncoder):
        source_paths = {"functional_groups": encoder.cache_path}
    metadata["source_cache_sha256"] = {
        name: _sha256(path)
        for name, path in source_paths.items()
        if name in block_order and path.is_file()
    }
    if view_dimensions["rdkit_2d"]:
        offset = sum(
            view_dimensions[name]
            for name in block_order[: block_order.index("rdkit_2d")]
        )
        dimension = view_dimensions["rdkit_2d"]
        raw_rdkit = {name: vector[offset : offset + dimension] for name, vector in raw.items()}
        descriptor_encoder = (
            encoder
            if isinstance(encoder, RDKit2DEncoder)
            else RDKit2DEncoder(encoder.cache_path.parent / "rdkit_2d_raw24_v1.npz")
        )
        scaler = RDKitDescriptorScaler.fit(
            raw_rdkit,
            train_smiles,
            descriptor_encoder.feature_names,
        )
        for name, vector in values.items():
            vector[offset : offset + dimension] = scaler.transform(
                raw[name][offset : offset + dimension]
            )
        metadata["rdkit_descriptor_definition_sha256"] = descriptor_encoder.definition_sha256
        metadata["rdkit_scaler"] = scaler.to_dict()
    if view_dimensions["functional_groups"]:
        group_encoder = (
            encoder
            if isinstance(encoder, FunctionalGroupEncoder)
            else FunctionalGroupEncoder(
                encoder.cache_path.parent / "functional_groups_thermoformer_v1.npz"
            )
        )
        metadata["functional_group_vocabulary_sha256"] = group_encoder.vocabulary_sha256
        metadata["functional_group_names"] = list(group_encoder.feature_names)
        metadata["functional_group_presence"] = "deterministic counts > 0; BASE/OTHER in model"
    definition_payload = {
        "view_dimensions": view_dimensions,
        "block_order": list(block_order),
        "rdkit_descriptor_definition_sha256": metadata.get(
            "rdkit_descriptor_definition_sha256"
        ),
        "functional_group_vocabulary_sha256": metadata.get(
            "functional_group_vocabulary_sha256"
        ),
    }
    metadata["feature_definition_sha256"] = hashlib.sha256(
        json.dumps(definition_payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    if not all(np.isfinite(vector).all() for vector in values.values()):
        raise ValueError("Prepared molecular features contain NaN or Inf")
    return PreparedMolecularFeatures(values, view_dimensions, metadata)


def encoder_cache_filename(config: Any) -> str:
    """Return a cache identity that changes with every representation branch."""

    if config.representation == "unimol_v2":
        return f"unimolv2_{config.model_size}.npz"
    if config.representation == "rdkit_2d":
        return "rdkit_2d_raw24_v1.npz"
    if config.representation == "functional_groups":
        return "functional_groups_thermoformer_v1.npz"
    if config.representation not in ("hybrid", "multiview"):
        raise ValueError(f"Unsupported molecular representation: {config.representation}")
    branches = []
    if config.use_rdkit_descriptors:
        branches.append("rdkit")
    if config.use_unimol:
        branches.append(f"unimol_{config.model_size}")
    if config.use_functional_groups:
        branches.append("functional")
    return "hybrid_" + "_".join(branches) + "_v1.npz"


def build_molecular_encoder(
    config: Any,
    cache_path: Path,
    use_cuda: bool | None = None,
    backend_factory: Callable[..., object] | None = None,
) -> object:
    """Construct the configured molecular encoder behind one runner-facing seam."""

    if config.representation in ("hybrid", "multiview"):
        return HybridMolecularEncoder(
            cache_path,
            batch_size=config.batch_size,
            model_size=config.model_size,
            use_cuda=use_cuda,
            backend_factory=backend_factory,
            use_rdkit_descriptors=config.use_rdkit_descriptors,
            use_unimol=config.use_unimol,
            use_functional_groups=config.use_functional_groups,
        )
    if config.representation == "unimol_v2":
        return UniMolV2Encoder(
            cache_path,
            batch_size=config.batch_size,
            model_size=config.model_size,
            use_cuda=use_cuda,
            backend_factory=backend_factory,
        )
    if config.representation == "rdkit_2d":
        return RDKit2DEncoder(cache_path)
    if config.representation == "functional_groups":
        return FunctionalGroupEncoder(cache_path)
    raise ValueError(f"Unsupported molecular representation: {config.representation}")
