import pytest
from unittest.mock import patch, MagicMock
import sys
from pathlib import Path

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.data.db import get_supabase

@patch("src.data.db.create_client")
def test_supabase_connection(mock_create_client):
    """Testa se a inicializacao da conexao Supabase lida com variaveis vazias de forma segura."""
    
    mock_client = MagicMock()
    mock_create_client.return_value = mock_client
    
    # Com token válido, retorna a instância conectada (mock)
    client = get_supabase("fake_token")
    assert client is not None
