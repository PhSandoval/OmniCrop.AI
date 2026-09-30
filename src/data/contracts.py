from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any

class OpenMeteoDaily(BaseModel):
    time: List[str]
    temperature_2m_max: List[float]
    temperature_2m_min: List[float]
    precipitation_sum: List[float]

    @field_validator("precipitation_sum")
    def check_positive_precipitation(cls, v):
        for val in v:
            if val < 0:
                raise ValueError(f"Precipitação não pode ser negativa, recebido: {val}")
        return v

class OpenMeteoResponse(BaseModel):
    latitude: float
    longitude: float
    timezone: str
    daily: OpenMeteoDaily
    _metadata: Dict[str, Any] = None
