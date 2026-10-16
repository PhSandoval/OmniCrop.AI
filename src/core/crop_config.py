"""
Dicionário Biológico e Parâmetros Fisiológicos Multi-Cultura do OmniCrop AI.
Suporta parametrização dinâmica de Graus-Dia Acumulados (GDA) e Coeficientes de Cultura (Kc).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class CropParameters:
    """
    Parâmetros biológicos e fisiológicos fundamentais de uma cultura agrícola.

    Atributos:
    - crop_id: Identificador canônico da cultura (ex: 'sugarcane', 'soybean', 'corn').
    - name: Nome legível da cultura em português (ex: 'Cana-de-Açúcar').
    - base_temp_celsius: Temperatura base inferior (Tb) em °C para o cálculo de Graus-Dia (GDD).
    - kc_default: Coeficiente de cultura médio padrão (Kc da FAO 56) para estimativa de evapotranspiração real (ETc).
    - description: Descrição fisiológica sucinta.
    """
    crop_id: str
    name: str
    base_temp_celsius: float
    kc_default: float
    description: str = ""


# ── Registro de Culturas Suportadas ─────────────────────────────────────────
CROP_REGISTRY: Dict[str, CropParameters] = {
    "sugarcane": CropParameters(
        crop_id="sugarcane",
        name="Cana-de-Açúcar",
        base_temp_celsius=18.0,
        kc_default=1.05,
        description="Gramínea C4 de ciclo semi-perene, alta exigência térmica (Tb=18°C) e acúmulo de sacarose (ATR).",
    ),
    "soybean": CropParameters(
        crop_id="soybean",
        name="Soja",
        base_temp_celsius=10.0,
        kc_default=1.15,
        description="Leguminosa C3 de ciclo anual, sensível ao fotoperíodo e com temperatura base de 10°C.",
    ),
    "corn": CropParameters(
        crop_id="corn",
        name="Milho",
        base_temp_celsius=10.0,
        kc_default=1.20,
        description="Cereal C4 de ciclo anual, alta taxa fotossintética e elevada demanda hídrica no pendoamento.",
    ),
}

# Mapeamento para normalização de strings vindas de dropdowns ou cadastros legados
CROP_ALIAS_MAP: Dict[str, str] = {
    "sugarcane": "sugarcane",
    "cana": "sugarcane",
    "cana-de-açúcar": "sugarcane",
    "cana-de-acucar": "sugarcane",
    "cana de acucar": "sugarcane",
    "cana de açúcar": "sugarcane",

    "soybean": "soybean",
    "soja": "soybean",
    "soy": "soybean",

    "corn": "corn",
    "milho": "corn",
    "maize": "corn",
}


def normalize_crop_id(crop_identifier: str | None) -> str:
    """Normaliza nomes e aliases para o identificador canônico da cultura."""
    if not crop_identifier:
        return "sugarcane"
    cleaned = str(crop_identifier).strip().lower()
    return CROP_ALIAS_MAP.get(cleaned, cleaned)


def get_crop_parameters(crop_identifier: str | None = "sugarcane") -> CropParameters:
    """
    Retorna os parâmetros biológicos da cultura solicitada.
    Fallback seguro para 'sugarcane' se o identificador não for reconhecido.
    """
    canon_id = normalize_crop_id(crop_identifier)
    return CROP_REGISTRY.get(canon_id, CROP_REGISTRY["sugarcane"])


def list_supported_crops() -> List[CropParameters]:
    """Retorna a lista de todas as culturas catalogadas no dicionário biológico."""
    return list(CROP_REGISTRY.values())
