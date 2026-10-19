"""
Schemas Pydantic v2 para Gestão de Fazendas e Geometrias Espaciais.
"""
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FarmCreate(BaseModel):
    """Payload de entrada para cadastro de nova fazenda com geolocalização."""
    farm_name: str = Field(..., min_length=2, max_length=255, description="Nome da propriedade ou talhão")
    city: str = Field(..., min_length=2, max_length=255, description="Município e UF")
    lat: float = Field(..., ge=-90.0, le=90.0, description="Latitude decimal")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Longitude decimal")
    tipo_cultura: str = Field(default="Cana-de-Açúcar", description="Cultura agrícola explorada")
    crop_id: Optional[str] = Field(default=None, description="Identificador canônico da cultura")
    area_ha: float = Field(default=100.0, gt=0.0, description="Área total em hectares")
    boundary_geojson: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Polígono GeoJSON da delimitação perimetral",
    )


class FarmUpdate(BaseModel):
    """Payload para atualização cadastral ou geométrica de fazenda existente."""
    farm_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    city: Optional[str] = Field(default=None, min_length=2, max_length=255)
    lat: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    lon: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    tipo_cultura: Optional[str] = None
    crop_id: Optional[str] = None
    area_ha: Optional[float] = Field(default=None, gt=0.0)
    boundary_geojson: Optional[Dict[str, Any]] = None


class FarmResponse(BaseModel):
    """Representação serializada de uma fazenda cadastrada."""
    id: Optional[str] = Field(default=None, description="UUID da fazenda no PostgreSQL")
    user_id: Optional[str] = Field(default=None, description="UUID do proprietário multi-tenant")
    farm_name: str
    city: str
    lat: float
    lon: float
    area_ha: float
    tipo_cultura: str
    crop_id: str
    boundary_geojson: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None
