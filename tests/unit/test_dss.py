import pytest
import sys
from pathlib import Path

# Garante que o projeto está no PATH
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.models.predict import calcular_dss

def test_fase_crescimento_critico():
    """Mês de Janeiro (Crescimento), NDVI muito baixo, Simulador sobe NDVI."""
    res = calcular_dss(mes_atual=1, ndvi_atual=0.3, ndvi_projetado=0.5)
    assert res["status_title"] == "🔴 Critico"
    assert "Irrigacao de salvamento" in res["mensagem_recomendacao"]

def test_fase_maturacao_pronto_corte():
    """Mês de Agosto (Maturação), NDVI muito baixo (Secando), Simulador não importa."""
    res = calcular_dss(mes_atual=8, ndvi_atual=0.3, ndvi_projetado=0.3)
    assert res["status_title"] == "🟡 Pronto p/ Corte"
    assert "desperdício" in res["mensagem_recomendacao"]

def test_simulacao_piora_resultado():
    """Se houver intervenção de Irrigação, e o NDVI abaixar, a regra dispara um alerta de falha de estratégia."""
    res = calcular_dss(mes_atual=5, ndvi_atual=0.6, ndvi_projetado=0.4, cenario="Irrigação")
    assert res["status_title"] == "❌ Alerta Simulacao"
    assert "Estratégia não recomendada" in res["mensagem_recomendacao"]
    
def test_fase_maturacao_cana_verde():
    """Mês de Julho (Maturação), NDVI muito alto (Choveu fora de época, não acumula açúcar)."""
    res = calcular_dss(mes_atual=7, ndvi_atual=0.7, ndvi_projetado=0.7)
    assert res["status_title"] == "🟠 Alerta"
    assert "maturador químico" in res["mensagem_recomendacao"]


def test_dispatch_operational_alerts():
    """Testa o roteamento e despacho de alertas operacionais por email e webhook."""
    from unittest.mock import patch, MagicMock
    from src.utils.daily_alerts import dispatch_alert

    # 1. Teste de canal Email
    with patch("src.utils.daily_alerts.send_alert_email") as mock_email:
        res_email = dispatch_alert("gestor@fazenda.com", "Fazenda Modelo", ["Alerta de seca"])
        assert res_email["success"] is True
        assert res_email["channel"] == "email"
        mock_email.assert_called_once()

    # 2. Teste de canal Webhook com sucesso (mock HTTP 200)
    with patch("requests.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_post.return_value = mock_resp

        res_wh = dispatch_alert("https://discord.com/api/webhooks/mock123", "Fazenda Modelo", ["Déficit crítico"], ndvi=0.35)
        assert res_wh["success"] is True
        assert res_wh["channel"] == "webhook"
        mock_post.assert_called_once()


def test_send_alert_email_smtp_success_and_failure(monkeypatch):
    """Valida send_alert_email com mock de smtplib.SMTP para sucesso e falha."""
    from unittest.mock import patch, MagicMock
    import smtplib
    from src.utils.daily_alerts import send_alert_email

    monkeypatch.setenv("SMTP_USER", "usuario_teste@omnicrop.ai")
    monkeypatch.setenv("SMTP_PASS", "senha_secreta_smtp")

    # 1. Sucesso
    with patch("smtplib.SMTP") as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server

        ok = send_alert_email("produtor@fazenda.com", "Fazenda Alvorada", ["Alerta de Veranico", "Déficit Hídrico"])
        assert ok is True
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once_with("usuario_teste@omnicrop.ai", "senha_secreta_smtp")
        mock_server.send_message.assert_called_once()

    # 2. Exceção no servidor SMTP
    with patch("smtplib.SMTP", side_effect=smtplib.SMTPException("Erro de conexão")):
        fail = send_alert_email("produtor@fazenda.com", "Fazenda Alvorada", ["Alerta de Veranico"])
        assert fail is False


def test_webhook_alerts_and_dispatch_edge_cases():
    """Valida casos de borda do despachante e formatos Discord vs Genérico."""
    from unittest.mock import patch, MagicMock
    from src.utils.daily_alerts import send_webhook_alert, dispatch_alert

    # 1. URL vazia ou inválida
    assert send_webhook_alert("", "Fazenda", ["Alerta"]) is False
    assert send_webhook_alert("ftp://invalid-url", "Fazenda", ["Alerta"]) is False

    # 2. Destino vazio no dispatch_alert
    res_empty = dispatch_alert("", "Fazenda", ["Alerta"])
    assert res_empty["success"] is False
    assert res_empty["channel"] == "none"

    # 3. Webhook Slack/Discord com sucesso
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=204)
        assert send_webhook_alert("https://slack.com/services/mock", "Fazenda", ["Alerta Slack"], ndvi=0.72) is True

    # 4. Webhook genérico com status 400
    with patch("requests.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=400)
        assert send_webhook_alert("https://api.custom.com/webhook", "Fazenda", ["Alerta Custom"]) is False

    # 5. Exceção de rede em requests.post
    with patch("requests.post", side_effect=Exception("Timeout no webhook")):
        assert send_webhook_alert("https://api.custom.com/webhook", "Fazenda", ["Alerta"]) is False


def test_run_daily_cron_execution():
    """Valida execução da rotina diária de cron e iteração de fazendas cadastradas."""
    from unittest.mock import patch, MagicMock
    import pandas as pd
    from src.utils.daily_alerts import run_daily_cron

    mock_sb = MagicMock()
    mock_sb.auth.admin.list_users.side_effect = Exception("Sem admin role")
    mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=[
        {"farm_name": "Fazenda Ativa", "lat": -21.1, "lon": -47.8, "receber_alertas": True},
        {"farm_name": "Fazenda Silenciada", "lat": -21.2, "lon": -47.9, "receber_alertas": False},
        {"farm_name": "Fazenda Sem Risco", "lat": -21.3, "lon": -48.0, "receber_alertas": True},
        {"farm_name": "Fazenda Falha", "lat": -21.4, "lon": -48.1, "receber_alertas": True},
    ])

    today_sample = {"chuva_acumulada_30d": 10.0, "chuva_acumulada_60d": 20.0, "chuva_acumulada_90d": 30.0, "GDA_mensal": 100.0}
    df_sample = pd.DataFrame([today_sample])

    def fake_fetch(lat, lon):
        if lat == -21.4:
            raise RuntimeError("Erro ao puxar dados da fazenda falha")
        return df_sample, today_sample

    with patch("src.utils.daily_alerts.get_supabase", return_value=mock_sb), \
         patch("src.utils.daily_alerts.fetch_farm_data", side_effect=fake_fetch), \
         patch("src.utils.daily_alerts.build_payload", return_value=today_sample), \
         patch("src.utils.daily_alerts.get_prediction", side_effect=[
             {"fatores_de_risco_identificados": ["Déficit"]},
             {"fatores_de_risco_identificados": ["Déficit"]},
             {"fatores_de_risco_identificados": []},
         ]), \
         patch("src.utils.daily_alerts.send_alert_email") as mock_email:
        run_daily_cron()
        mock_email.assert_called_once()


def test_daily_alerts_main_execution():
    """Valida execução do módulo daily_alerts como __main__."""
    import runpy
    from unittest.mock import patch, MagicMock
    from pathlib import Path

    script_path = str(Path(__file__).resolve().parents[2] / "src" / "utils" / "daily_alerts.py")
    mock_sb = MagicMock()
    mock_sb.auth.admin.list_users.return_value = []
    mock_sb.table.return_value.select.return_value.execute.return_value = MagicMock(data=[])
    with patch("src.data.db.get_supabase", return_value=mock_sb):
        runpy.run_path(script_path, run_name="__main__")

