"""
Testes unitários para o Módulo de Model Registry (Hugging Face Hub) e integração com inferência.
Garante 100% de cobertura de código em src/mlops/hf_registry.py e nas ramificações de load_model em src/models/predict.py.
"""
import os
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest

from src.mlops.hf_registry import (
    DEFAULT_HF_REPO_ID,
    download_model_from_registry,
    generate_model_card,
    publish_models_to_registry,
)
from src.models.predict import load_model


# ── 1. TESTES DO MODEL CARD ───────────────────────────────────────────────────

def test_generate_model_card():
    card = generate_model_card()
    assert isinstance(card, str)
    assert "tags:" in card
    assert "scikit-learn" in card
    assert "omnicrop" in card
    assert "Cana-de-Açúcar" in card
    assert "Soja" in card
    assert "Milho" in card
    assert "Café" in card
    assert "Pecuária (Pastagem)" in card
    assert "sugarcane" in card
    assert "soybean" in card
    assert "corn" in card
    assert "coffee" in card
    assert "pasture" in card
    assert "MAE" in card
    assert "RMSE" in card
    assert "R^2" in card or "R²" in card


# ── 2. TESTES DE DOWNLOAD DO MODEL REGISTRY ───────────────────────────────────

def test_download_model_from_registry_success():
    mock_dest = "/tmp/mock_models/sugarcane_ndvi.pkl"
    with patch("src.mlops.hf_registry.hf_hub_download", return_value=mock_dest) as mock_dl:
        res = download_model_from_registry("sugarcane", repo_id="custom/repo", local_dir="/tmp/mock_models")
        assert res == mock_dest
        mock_dl.assert_called_once_with(
            repo_id="custom/repo",
            filename="sugarcane_ndvi.pkl",
            local_dir="/tmp/mock_models",
        )


def test_download_model_from_registry_fallback_to_local(tmp_path):
    # Cria arquivo local simulado
    local_file = tmp_path / "soybean_ndvi.pkl"
    local_file.write_text("mock model content")

    # Simula erro de conexão ao Hugging Face Hub
    with patch("src.mlops.hf_registry.hf_hub_download", side_effect=Exception("HF Hub offline")):
        res = download_model_from_registry("soybean", local_dir=str(tmp_path))
        assert res == str(local_file)


def test_download_model_from_registry_fallback_to_legacy_sugarcane(tmp_path):
    # Arquivo legado ndvi_model.pkl existe, mas sugarcane_ndvi.pkl não
    legacy_file = tmp_path / "ndvi_model.pkl"
    legacy_file.write_text("mock legacy model")

    with patch("src.mlops.hf_registry.hf_hub_download", side_effect=Exception("Connection refused")):
        res = download_model_from_registry("sugarcane", local_dir=str(tmp_path))
        assert res == str(legacy_file)


def test_download_model_from_registry_not_found_raises(tmp_path):
    # Nenhum arquivo existe localmente nem no Hub
    with patch("src.mlops.hf_registry.hf_hub_download", side_effect=Exception("404 Not Found")):
        with pytest.raises(FileNotFoundError) as exc_info:
            download_model_from_registry("unknown_crop", local_dir=str(tmp_path))
        assert "não foi encontrado" in str(exc_info.value)


# ── 3. TESTES DE PUBLICAÇÃO NO REGISTRY ───────────────────────────────────────

def test_publish_models_to_registry(tmp_path):
    # Cria modelos simulados no diretório temporário
    (tmp_path / "sugarcane_ndvi.pkl").write_text("pkl_1")
    (tmp_path / "corn_ndvi.pkl").write_text("pkl_2")

    mock_api_instance = MagicMock()

    with patch("src.mlops.hf_registry.HfApi", return_value=mock_api_instance) as mock_api_cls:
        uploaded = publish_models_to_registry(
            repo_id="test_org/test_repo",
            token="hf_mock_token_123",
            models_dir=str(tmp_path),
        )

        mock_api_cls.assert_called_once_with(token="hf_mock_token_123")
        mock_api_instance.create_repo.assert_called_once_with(
            repo_id="test_org/test_repo",
            repo_type="model",
            exist_ok=True,
        )
        assert "sugarcane_ndvi.pkl" in uploaded
        assert "corn_ndvi.pkl" in uploaded
        assert "README.md" in uploaded
        assert (tmp_path / "MODEL_CARD.md").exists()
        assert mock_api_instance.upload_file.call_count == 3  # 2 modelos + 1 README.md


# ── 4. TESTES DE INTEGRAÇÃO COM LOAD_MODEL (PREDICT.PY) ───────────────────────

def test_load_model_with_use_hf_hub_env():
    load_model.clear()
    real_path = str(Path("src/models/sugarcane_ndvi.pkl").resolve())

    with patch.dict(os.environ, {"USE_HF_HUB": "1"}):
        with patch("src.mlops.hf_registry.download_model_from_registry", return_value=real_path) as mock_dl:
            model = load_model("sugarcane")
            assert model is not None
            mock_dl.assert_called_once()
    load_model.clear()


def test_load_model_with_use_hf_hub_exception_fallback():
    load_model.clear()
    # Simula falha ao baixar via HF Hub com USE_HF_HUB=1, mas arquivo local existe
    with patch.dict(os.environ, {"USE_HF_HUB": "1"}):
        with patch("src.mlops.hf_registry.download_model_from_registry", side_effect=Exception("Timeout")):
            model = load_model("sugarcane")
            assert model is not None
    load_model.clear()


def test_load_model_missing_local_file_triggers_hf_download():
    load_model.clear()
    real_path = str(Path("src/models/corn_ndvi.pkl").resolve())

    # Simula que o arquivo específico não existe em disco
    with patch("pathlib.Path.exists", return_value=False):
        with patch("src.mlops.hf_registry.download_model_from_registry", return_value=real_path) as mock_dl:
            with patch("joblib.load", return_value=MagicMock()) as mock_joblib:
                model = load_model("corn")
                assert model is not None
                mock_dl.assert_called_once()
                mock_joblib.assert_called_once()
    load_model.clear()


def test_load_model_missing_local_file_and_hf_failure_raises():
    load_model.clear()
    # Simula ausência de arquivo local e falha no download
    with patch("pathlib.Path.exists", return_value=False):
        with patch("src.mlops.hf_registry.download_model_from_registry", side_effect=FileNotFoundError("Not on Hub")):
            with pytest.raises(NotImplementedError) as exc_info:
                load_model("soybean")
            assert "está em fase de treino" in str(exc_info.value)
    load_model.clear()


def test_load_model_sugarcane_legacy_fallback_when_hf_fails():
    load_model.clear()
    def fake_exists(path_obj):
        return "ndvi_model.pkl" in str(path_obj)

    with patch.object(Path, "exists", fake_exists):
        with patch("src.mlops.hf_registry.download_model_from_registry", side_effect=Exception("Fail")):
            with patch("joblib.load", return_value=MagicMock()) as mock_joblib:
                model = load_model("sugarcane")
                assert model is not None
                mock_joblib.assert_called_once()
    load_model.clear()
