import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path
import streamlit as st

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.db import (
    get_supabase,
    get_user_farms,
    insert_farm,
    update_farm,
    delete_farm,
    insert_farm_gold_kpis,
    get_farm_gold_kpis,
    get_latest_farm_gold_kpi,
)


@patch("src.data.db.create_client")
def test_supabase_connection(mock_create_client):
    """Testa se a inicializacao da conexao Supabase lida com variaveis vazias de forma segura."""
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    client = get_supabase("fake_token")
    assert client is not None
    mock_client.postgrest.auth.assert_called_once_with("fake_token")


@patch("src.data.db.create_client")
def test_get_supabase_session_state_fallback(mock_create_client):
    """Testa se o get_supabase captura automaticamente o JWT da sessão do Streamlit se não passado."""
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    st.session_state['access_token'] = "jwt_session_token_xyz"
    client = get_supabase()
    assert client is not None
    mock_client.postgrest.auth.assert_called_with("jwt_session_token_xyz")


@patch("src.data.db.create_client")
def test_get_user_farms_uses_authenticated_client(mock_create_client):
    """Garante que a listagem de fazendas do usuário utiliza o token de sessão para aplicar RLS."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq
    mock_order = MagicMock()
    mock_eq.order.return_value = mock_order
    mock_order.execute.return_value = MagicMock(data=[{"id": "f1", "farm_name": "Fazenda Modelo"}])
    
    mock_create_client.return_value = mock_client
    
    farms = get_user_farms("user_123", access_token="token_user_123")
    assert len(farms) == 1
    assert farms[0]["farm_name"] == "Fazenda Modelo"
    mock_client.postgrest.auth.assert_called_with("token_user_123")
    mock_client.table.assert_called_with("fazendas")
    mock_select.eq.assert_called_with("user_id", "user_123")


@patch("src.data.db.create_client")
def test_insert_farm_gold_kpis_binds_farm_id_and_token(mock_create_client):
    """Garante que o insert na Camada Ouro atrela o farm_id e injeta o JWT para validação de RLS."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_insert = MagicMock()
    mock_table.insert.return_value = mock_insert
    mock_insert.execute.return_value = MagicMock(data=[{"id": "gold_123", "farm_id": "farm_456"}])
    
    mock_create_client.return_value = mock_client
    
    kpi_payload = {
        "balanco_hidrico_mm": -15.2,
        "dias_sem_chuva": 5,
        "gda_total_acumulado": 110.5,
        "risco_estresse_hidrico": "MODERADO",
        "recomendacao_manejo": "Monitorar umidade.",
        "id": "should_be_removed_before_insert",
    }
    
    res = insert_farm_gold_kpis("farm_456", kpi_payload, access_token="token_farm_owner")
    
    mock_client.postgrest.auth.assert_called_with("token_farm_owner")
    mock_client.table.assert_called_with("kpis_gold")
    
    # Verifica que farm_id foi atrelado e o id foi removido
    called_payload = mock_table.insert.call_args[0][0]
    assert called_payload["farm_id"] == "farm_456"
    assert "id" not in called_payload
    assert called_payload["balanco_hidrico_mm"] == -15.2


@patch("src.data.db.create_client")
def test_get_farm_gold_kpis_filters_and_orders(mock_create_client):
    """Garante que a busca de KPIs Gold filtra estritamente por farm_id com ordenação decrescente."""
    mock_client = MagicMock()
    mock_table = MagicMock()
    mock_client.table.return_value = mock_table
    mock_select = MagicMock()
    mock_table.select.return_value = mock_select
    mock_eq = MagicMock()
    mock_select.eq.return_value = mock_eq
    mock_order = MagicMock()
    mock_eq.order.return_value = mock_order
    mock_limit = MagicMock()
    mock_order.limit.return_value = mock_limit
    mock_limit.execute.return_value = MagicMock(data=[
        {"farm_id": "farm_456", "balanco_hidrico_mm": -12.0, "processed_at": "2026-10-15T12:00:00Z"}
    ])
    
    mock_create_client.return_value = mock_client
    
    results = get_farm_gold_kpis("farm_456", limit=5, access_token="token_456")
    assert len(results) == 1
    assert results[0]["balanco_hidrico_mm"] == -12.0
    mock_select.eq.assert_called_with("farm_id", "farm_456")
    mock_eq.order.assert_called_with("processed_at", desc=True)
    mock_order.limit.assert_called_with(5)


@patch("src.data.db.get_farm_gold_kpis")
def test_get_latest_farm_gold_kpi_single(mock_get_farm_gold_kpis):
    """Testa se o helper get_latest_farm_gold_kpi retorna apenas o primeiro registro ou None."""
    mock_get_farm_gold_kpis.return_value = [{"id": "k1", "balanco_hidrico_mm": -5.0}]
    latest = get_latest_farm_gold_kpi("farm_789")
    assert latest is not None
    assert latest["id"] == "k1"

    mock_get_farm_gold_kpis.return_value = []
    latest_none = get_latest_farm_gold_kpi("farm_empty")
    assert latest_none is None


def test_supabase_schema_rls_multi_tenant_security():
    """Valida o contrato de segurança do arquivo SQL para garantir que a Fazenda A nunca veja a Fazenda B."""
    schema_path = Path(__file__).resolve().parents[2] / "supabase_schema.sql"
    assert schema_path.exists(), "supabase_schema.sql deve existir na raiz do projeto"
    
    sql_content = schema_path.read_text(encoding="utf-8")
    
    # 1. Row Level Security habilitado em ambas as tabelas
    assert "ALTER TABLE public.fazendas ENABLE ROW LEVEL SECURITY;" in sql_content
    assert "ALTER TABLE public.kpis_gold ENABLE ROW LEVEL SECURITY;" in sql_content
    
    # 2. Fazendas vinculadas a auth.uid()
    assert "(auth.uid() = user_id)" in sql_content
    
    # 3. kpis_gold amarrado ao dono da fazenda via subselect em fazendas
    assert "farm_id IN (" in sql_content
    assert "SELECT f.id FROM public.fazendas f WHERE f.user_id = auth.uid()" in sql_content
    
    # 4. Proibição de políticas permissivas para authenticated em kpis_gold
    # Garante que não sobrou USING (true) para authenticated
    lines = sql_content.splitlines()
    for i, line in enumerate(lines):
        if "TO authenticated" in line:
            # As próximas linhas até o próximo ponto e vírgula não podem ter "USING (true)"
            block = "\n".join(lines[i:i+8])
            assert "USING (true)" not in block, f"Encontrado USING (true) inaceitável para authenticated: {block}"
            
    # 5. Índices de performance multi-tenant
    assert "CREATE INDEX IF NOT EXISTS idx_fazendas_user_id" in sql_content
    assert "CREATE INDEX IF NOT EXISTS idx_kpis_gold_farm_id" in sql_content
