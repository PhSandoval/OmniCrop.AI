"""
Núcleo de Configurações Biológicas e Agronômicas do OmniCrop AI.
"""
from src.core.crop_config import CropParameters, CROP_REGISTRY, get_crop_parameters, normalize_crop_id
from src.core.cache import cache_manager, cached, make_weather_cache_key
from src.core.jobs import job_manager, JobStatus, JobRecord

__all__ = [
    "CropParameters",
    "CROP_REGISTRY",
    "get_crop_parameters",
    "normalize_crop_id",
    "cache_manager",
    "cached",
    "make_weather_cache_key",
    "job_manager",
    "JobStatus",
    "JobRecord",
]
