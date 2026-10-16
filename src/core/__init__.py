"""
Núcleo de Configurações Biológicas e Agronômicas do OmniCrop AI.
"""
from src.core.crop_config import CropParameters, CROP_REGISTRY, get_crop_parameters, normalize_crop_id

__all__ = ["CropParameters", "CROP_REGISTRY", "get_crop_parameters", "normalize_crop_id"]
