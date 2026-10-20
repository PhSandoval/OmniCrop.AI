"""
Módulo de MLOps do OmniCrop AI:
Monitoramento de Data Drift, estabilidade de dados e governança de modelos de Machine Learning.
"""
from src.mlops.data_drift import (
    calculate_psi,
    evaluate_feature_drift,
    detect_data_drift,
    FeatureDriftResult,
    DataDriftReport,
)
from src.mlops.hf_registry import (
    DEFAULT_HF_REPO_ID,
    download_model_from_registry,
    publish_models_to_registry,
    generate_model_card,
)

__all__ = [
    "calculate_psi",
    "evaluate_feature_drift",
    "detect_data_drift",
    "FeatureDriftResult",
    "DataDriftReport",
    "DEFAULT_HF_REPO_ID",
    "download_model_from_registry",
    "publish_models_to_registry",
    "generate_model_card",
]
