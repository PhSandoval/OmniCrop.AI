import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from src.core.crop_config import (
    CropParameters,
    CROP_REGISTRY,
    get_crop_parameters,
    normalize_crop_id,
    list_supported_crops,
)


def test_crop_parameters_registry():
    """Valida se o dicionário biológico contém as 5 culturas com os parâmetros especificados."""
    assert "sugarcane" in CROP_REGISTRY
    assert "soybean" in CROP_REGISTRY
    assert "corn" in CROP_REGISTRY
    assert "coffee" in CROP_REGISTRY
    assert "pasture" in CROP_REGISTRY

    # Sugarcane: base 18.0, kc 1.05
    sugarcane = CROP_REGISTRY["sugarcane"]
    assert sugarcane.base_temp_celsius == 18.0
    assert sugarcane.kc_default == 1.05
    assert sugarcane.name == "Cana-de-Açúcar"

    # Soybean: base 10.0, kc 1.15
    soybean = CROP_REGISTRY["soybean"]
    assert soybean.base_temp_celsius == 10.0
    assert soybean.kc_default == 1.15
    assert soybean.name == "Soja"

    # Corn: base 10.0, kc 1.20
    corn = CROP_REGISTRY["corn"]
    assert corn.base_temp_celsius == 10.0
    assert corn.kc_default == 1.20
    assert corn.name == "Milho"

    # Coffee: base 10.0, kc 1.05
    coffee = CROP_REGISTRY["coffee"]
    assert coffee.base_temp_celsius == 10.0
    assert coffee.kc_default == 1.05
    assert coffee.name == "Café"

    # Pasture: base 15.0, kc 0.90
    pasture = CROP_REGISTRY["pasture"]
    assert pasture.base_temp_celsius == 15.0
    assert pasture.kc_default == 0.90
    assert pasture.name == "Pecuária (Pastagem)"


def test_normalize_crop_id_aliases():
    """Valida que aliases em português e variações de maiúsculas/acentos são normalizados corretamente."""
    assert normalize_crop_id("Cana-de-Açúcar") == "sugarcane"
    assert normalize_crop_id("Cana") == "sugarcane"
    assert normalize_crop_id("sugarcane") == "sugarcane"

    assert normalize_crop_id("Soja") == "soybean"
    assert normalize_crop_id("SOJA") == "soybean"
    assert normalize_crop_id("soybean") == "soybean"

    assert normalize_crop_id("Milho") == "corn"
    assert normalize_crop_id("MILHO") == "corn"
    assert normalize_crop_id("corn") == "corn"

    assert normalize_crop_id("Café") == "coffee"
    assert normalize_crop_id("cafe") == "coffee"
    assert normalize_crop_id("coffee") == "coffee"

    assert normalize_crop_id("Pecuária") == "pasture"
    assert normalize_crop_id("pastagem") == "pasture"
    assert normalize_crop_id("pasture") == "pasture"
    assert normalize_crop_id("gado") == "pasture"

    # Fallback para string vazia ou None
    assert normalize_crop_id(None) == "sugarcane"
    assert normalize_crop_id("") == "sugarcane"


def test_get_crop_parameters_fallback():
    """Valida se get_crop_parameters resolve com segurança e faz fallback para Cana caso desconhecido."""
    p_soja = get_crop_parameters("Soja")
    assert p_soja.crop_id == "soybean"
    assert p_soja.base_temp_celsius == 10.0

    p_cafe = get_crop_parameters("Café")
    assert p_cafe.crop_id == "coffee"
    assert p_cafe.base_temp_celsius == 10.0

    p_pasture = get_crop_parameters("Pecuária")
    assert p_pasture.crop_id == "pasture"
    assert p_pasture.base_temp_celsius == 15.0

    p_unknown = get_crop_parameters("cultura_inexistente")
    assert p_unknown.crop_id == "sugarcane"
    assert p_unknown.base_temp_celsius == 18.0


def test_list_supported_crops():
    """Valida que list_supported_crops retorna todas as 5 culturas cadastradas."""
    crops = list_supported_crops()
    assert len(crops) >= 5
    crop_ids = [c.crop_id for c in crops]
    assert "sugarcane" in crop_ids
    assert "soybean" in crop_ids
    assert "corn" in crop_ids
    assert "coffee" in crop_ids
    assert "pasture" in crop_ids
