from __future__ import annotations
import json
import pickle
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
import joblib
from app.core.config import get_settings
from app.core.exceptions import ArtifactError

settings = get_settings()


class ArtifactBundle:
    def __init__(self) -> None:
        self.artifact_dir: Path = settings.artifact_dir
        self.model: Any = None
        self.preprocessor: Any = None
        self.feature_schema: Dict[str, Any] = {}
        self.label_encoder: Dict[str, Any] = {}
        self.threshold: Dict[str, Any] = {}
        self.frozen_graph: Dict[str, Any] = {}
        self.explanation_templates: Dict[str, Any] = {}
        self.model_card: Dict[str, Any] = {}
        self.feature_importance: Optional[Dict[str, Any]] = None

    def _json(self, name: str) -> Dict[str, Any]:
        path = self.artifact_dir / name
        if not path.exists():
            raise ArtifactError(f"Required artifact missing: {path}")
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)

    def _install_pickle_compatibility_aliases(self) -> None:
        """Expose legacy import names used by older sklearn HistGB pickles."""
        try:
            import sklearn._loss._loss as sklearn_loss_extension
        except Exception:
            return

        sys.modules.setdefault("_loss", sklearn_loss_extension)

    def load(self) -> "ArtifactBundle":
        required = [
            "model.joblib",
            "preprocessing_pipeline.joblib",
            "feature_schema.json",
            "label_encoder.json",
            "threshold.json",
            "frozen_token_graph.pkl",
            "explanation_templates.json",
            "model_card.json",
        ]
        missing = [str(self.artifact_dir / x) for x in required if not (self.artifact_dir / x).exists()]
        if missing:
            raise ArtifactError("Missing required artifacts: " + ", ".join(missing))

        self._install_pickle_compatibility_aliases()
        self.model = joblib.load(self.artifact_dir / "model.joblib")
        self.preprocessor = joblib.load(self.artifact_dir / "preprocessing_pipeline.joblib")
        self.feature_schema = self._json("feature_schema.json")
        self.label_encoder = self._json("label_encoder.json")
        self.threshold = self._json("threshold.json")
        self.explanation_templates = self._json("explanation_templates.json")
        self.model_card = self._json("model_card.json")

        with (self.artifact_dir / "frozen_token_graph.pkl").open("rb") as f:
            self.frozen_graph = pickle.load(f)

        fi_path = self.artifact_dir / "feature_importance.json"
        if fi_path.exists():
            with fi_path.open("r", encoding="utf-8") as f:
                self.feature_importance = json.load(f)

        if not hasattr(self.model, "predict_proba"):
            raise ArtifactError("model.joblib must expose predict_proba(X).")

        return self

    @property
    def features(self) -> List[str]:
        return list(self.feature_schema.get("features", []))

    @property
    def n_features(self) -> int:
        return int(self.feature_schema.get("n_features", len(self.features)))

    @property
    def classes(self) -> List[str]:
        return list(self.label_encoder.get("model_classes_label_order") or self.label_encoder.get("classes") or [])

    @property
    def threshold_value(self) -> float:
        return float(self.threshold.get("threshold", 0.5))

    @property
    def model_version(self) -> str:
        return str(self.model_card.get("model_version", "unknown"))

    @property
    def feature_schema_version(self) -> str:
        return str(self.feature_schema.get("schema_version", "unknown"))


artifacts = ArtifactBundle()
