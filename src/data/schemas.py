from pydantic import BaseModel, Field
from typing import List

class DailyWeather(BaseModel):
    time: List[str] = Field(default_factory=list)
    temperature_2m_max: List[float] = Field(default_factory=list)
    temperature_2m_min: List[float] = Field(default_factory=list)
    # Deixando este obrigatório (sem default) para que a omissão da chave gere ValidationError
    # Mas ainda aceita listas vazias [] caso o sensor retorne assim
    precipitation_sum: List[float]
    et0_fao_evapotranspiration: List[float] = Field(default_factory=list)

class OpenMeteoResponse(BaseModel):
    latitude: float
    longitude: float
    daily: DailyWeather
