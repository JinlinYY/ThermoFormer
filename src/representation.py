"""Versioned molecular representations with deterministic, non-pickle caches."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Sequence

import numpy as np


class RDKit2DEncoder:
    """Deterministic, non-pretrained 2D descriptors for the encoder ablation."""

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

    def __init__(self, cache_path: Path) -> None:
        self.cache_path = cache_path

    def _load_cache(self) -> dict[str, np.ndarray]:
        if not self.cache_path.exists():
            return {}
        with np.load(self.cache_path, allow_pickle=False) as cache:
            if str(cache["model"].item()) != "rdkit_2d":
                return {}
            if str(cache["model_size"].item()) != "scaled24_v1":
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
        for name, scale in cls._DESCRIPTORS:
            descriptor = getattr(Descriptors, name)
            value = float(descriptor(molecule)) / scale
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
            model_size=np.asarray("scaled24_v1"),
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
    """RDKit fragment-count features generated from documented SMARTS definitions."""

    _MODEL_SIZE = "rdkit_fragments_v1"

    def __init__(self, cache_path: Path) -> None:
        from rdkit.Chem import Fragments

        self.cache_path = cache_path
        self.feature_names = tuple(
            sorted(name for name in dir(Fragments) if name.startswith("fr_"))
        )
        if not self.feature_names:
            raise RuntimeError("RDKit exposes no functional-group fragment descriptors")

    def _load_cache(self) -> dict[str, np.ndarray]:
        if not self.cache_path.exists():
            return {}
        with np.load(self.cache_path, allow_pickle=False) as cache:
            if str(cache["model"].item()) != "functional_groups":
                return {}
            if str(cache["model_size"].item()) != self._MODEL_SIZE:
                return {}
            names = tuple(cache["feature_names"].astype(str).tolist())
            if names != self.feature_names:
                return {}
            smiles = cache["smiles"].astype(str).tolist()
            features = np.asarray(cache["features"], dtype=np.float32)
        if features.shape != (len(smiles), len(self.feature_names)):
            raise ValueError(f"Invalid functional-group cache: {self.cache_path}")
        return {smile: features[index] for index, smile in enumerate(smiles)}

    def _describe(self, smiles: str) -> np.ndarray:
        from rdkit import Chem
        from rdkit.Chem import Fragments

        molecule = Chem.MolFromSmiles(smiles)
        if molecule is None:
            raise ValueError(f"RDKit could not parse SMILES: {smiles}")
        values = [float(getattr(Fragments, name)(molecule)) for name in self.feature_names]
        return np.asarray(values, dtype=np.float32)

    def _save_cache(self, features: dict[str, np.ndarray]) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        ordered = sorted(features)
        np.savez_compressed(
            self.cache_path,
            smiles=np.asarray(ordered),
            features=np.stack([features[smile] for smile in ordered]).astype(np.float32),
            feature_names=np.asarray(self.feature_names),
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
                "rdkit_2d": "rdkit_scaled24_v1",
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
            "rdkit_2d": RDKit2DEncoder(cache_root / "rdkit_2d_scaled24_v1.npz"),
            "unimol_v2": UniMolV2Encoder(
                cache_root / f"unimolv2_{self.model_size}.npz",
                batch_size=self.batch_size,
                model_size=self.model_size,
                use_cuda=self.use_cuda,
                backend_factory=self._backend_factory,
            ),
            "functional_groups": FunctionalGroupEncoder(
                cache_root / "functional_groups_rdkit_fragments_v1.npz"
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


def encoder_cache_filename(config: Any) -> str:
    """Return a cache identity that changes with every representation branch."""

    if config.representation == "unimol_v2":
        return f"unimolv2_{config.model_size}.npz"
    if config.representation == "rdkit_2d":
        return "rdkit_2d_scaled24_v1.npz"
    if config.representation == "functional_groups":
        return "functional_groups_rdkit_fragments_v1.npz"
    if config.representation != "hybrid":
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

    if config.representation == "hybrid":
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
