import pytest
import streamlit as st
from unittest.mock import patch, MagicMock
from types import SimpleNamespace

from src.utils.farm_config import (
    get_user_farms_db,
    load_config,
    save_config,
    is_configured,
)


@pytest.fixture(autouse=True)
def clean_session_state():
    """Limpa st.session_state antes de cada teste."""
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    yield
    for key in list(st.session_state.keys()):
        del st.session_state[key]


def test_get_user_farms_db_no_user():
    """Garante retorno de lista vazia quando não há usuário logado."""
    assert get_user_farms_db() == []


def test_get_user_farms_db_with_user():
    """Valida busca de fazendas quando usuário está logado."""
    st.session_state["user"] = SimpleNamespace(id="user-123")
    mock_farms = [{"id": "farm-1", "farm_name": "Fazenda Boa Vista"}]

    with patch("src.data.db.get_user_farms", return_value=mock_farms):
        res = get_user_farms_db()
        assert res == mock_farms


def test_get_user_farms_db_exception():
    """Valida tratamento seguro de erro quando get_user_farms falha."""
    st.session_state["user"] = SimpleNamespace(id="user-123")

    with patch("src.data.db.get_user_farms", side_effect=Exception("DB Error")):
        res = get_user_farms_db()
        assert res == []


def test_load_config_with_active_farm():
    """Valida carregamento de fazenda ativa com normalização de cultura."""
    st.session_state["active_farm"] = {
        "id": "farm-1",
        "farm_name": "Fazenda Modelo",
        "tipo_cultura": "Cana-de-Açúcar",
    }
    config = load_config()
    assert config is not None
    assert config["crop_id"] == "sugarcane"


def test_load_config_cleanup_nova_fazenda():
    """Valida rotina de limpeza de fazendas placeholder criadas por erro."""
    st.session_state["user"] = SimpleNamespace(id="user-123")
    initial_farms = [
        {"id": "f-clean", "farm_name": "Nova Fazenda"},
        {"id": "f-real", "farm_name": "Fazenda Real"},
    ]
    cleaned_farms = [{"id": "f-real", "farm_name": "Fazenda Real"}]

    with patch("src.utils.farm_config.get_user_farms_db", side_effect=[initial_farms, cleaned_farms]):
        with patch("src.data.db.delete_farm") as mock_delete:
            res = load_config()
            assert res is None
            mock_delete.assert_called_once_with("f-clean", "user-123")
            assert st.session_state.get("cleaned_up_nova_fazenda") is True
            assert st.session_state.get("user_farms") == cleaned_farms


def test_load_config_cleanup_delete_exception_handled():
    """Valida que falha no delete_farm durante cleanup é capturada com segurança."""
    st.session_state["user"] = SimpleNamespace(id="user-123")
    initial_farms = [{"id": "f-fail", "farm_name": "Nova Fazenda"}]

    with patch("src.utils.farm_config.get_user_farms_db", return_value=initial_farms):
        with patch("src.data.db.delete_farm", side_effect=Exception("Cannot delete")):
            res = load_config()
            assert res is None
            assert st.session_state.get("cleaned_up_nova_fazenda") is True


def test_load_config_no_farms():
    """Valida retorno None quando usuário não tem fazendas cadastradas."""
    with patch("src.utils.farm_config.get_user_farms_db", return_value=[]):
        res = load_config()
        assert res is None


def test_save_config_active_farm_update():
    """Valida salvamento e sincronização com banco para fazenda ativa."""
    st.session_state["user"] = SimpleNamespace(id="user-123")
    st.session_state["active_farm"] = {
        "id": "farm-99",
        "farm_name": "Fazenda Central",
        "tipo_cultura": "Soja",
    }

    config_update = {
        "area_ha": 350.0,
        "variedade": "TMG 7062",
        "ndvi_medio_lim": 0.65,
        "ndvi_critico_lim": 0.45,
        "deficit_lim": -30.0,
        "dias_calor_lim": 5,
        "tipo_cultura": "Milho",
        "crop_id": "corn",
    }

    with patch("src.data.db.update_farm") as mock_update:
        with patch("src.utils.farm_config.get_user_farms_db", return_value=[{"id": "farm-99"}]):
            save_config(config_update)
            mock_update.assert_called_once()
            args = mock_update.call_args[0]
            assert args[0] == "farm-99"
            assert args[1] == "user-123"
            assert args[2]["area_ha"] == 350.0
            assert args[2]["chuva_critica"] == 30.0
            assert args[2]["crop_id"] == "corn"
            assert st.session_state["active_farm"]["area_ha"] == 350.0


def test_save_config_active_farm_without_crop_id():
    """Valida normalização de crop_id quando ausente na fazenda ativa e na atualização."""
    st.session_state["user"] = SimpleNamespace(id="user-123")
    st.session_state["active_farm"] = {
        "id": "farm-101",
        "farm_name": "Fazenda Sem Crop ID",
    }
    with patch("src.data.db.update_farm"):
        with patch("src.utils.farm_config.get_user_farms_db", return_value=[]):
            save_config({"area_ha": 200, "tipo_cultura": "Cana-de-Açúcar"})
            assert st.session_state["active_farm"]["crop_id"] == "sugarcane"


def test_save_config_no_active_farm_with_user():

    """Valida definição de active_farm no onboarding quando id ainda não existe."""
    st.session_state["user"] = SimpleNamespace(id="user-123")
    new_farm = {"farm_name": "Nova Propriedade", "crop_id": "soybean"}

    with patch("src.utils.farm_config.get_user_farms_db", return_value=[new_farm]):
        save_config(new_farm)
        assert st.session_state["active_farm"] == new_farm


def test_save_config_exception_handled():
    """Valida captura de exceção ao tentar salvar no banco de dados."""
    st.session_state["user"] = SimpleNamespace(id="user-123")
    st.session_state["active_farm"] = {"id": "farm-error"}

    with patch("src.data.db.update_farm", side_effect=Exception("Database Timeout")):
        with patch.object(st, "error") as mock_err:
            save_config({"area_ha": 100})
            mock_err.assert_called_once()


def test_save_config_offline_no_user():
    """Valida persistência local no session_state quando não há usuário logado."""
    save_config({"farm_name": "Modo Local"})
    assert st.session_state["active_farm"]["farm_name"] == "Modo Local"

    save_config({"area_ha": 500})
    assert st.session_state["active_farm"]["area_ha"] == 500


def test_is_configured():
    """Valida helper is_configured."""
    with patch("src.utils.farm_config.load_config", return_value=None):
        assert is_configured() is False

    with patch("src.utils.farm_config.load_config", return_value={"id": "f-1"}):
        assert is_configured() is True
