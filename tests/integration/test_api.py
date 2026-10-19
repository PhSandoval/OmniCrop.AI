"""
Testes de integração para a API RESTful Headless do OmniCrop AI.
Garante 100% de cobertura nos roteadores, schemas, tratamento de exceções e injeção de dependências.
"""
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from src.api.main import app
from src.api.dependencies import AuthContext, get_auth_context
from src.mlops.data_drift import DataDriftReport, FeatureDriftResult

client = TestClient(app)


# ── 1. HEALTH CHECKS ──────────────────────────────────────────────────────────

def test_health_check_endpoints():
    r1 = client.get("/health")
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["status"] == "ok"
    assert data1["app"] == "OmniCrop AI REST API"
    assert data1["version"] == "1.0.0"

    r2 = client.get("/api/v1/health")
    assert r2.status_code == 200
    assert r2.json()["status"] == "ok"


# ── 2. AUTHENTICATION & DEPENDENCIES ──────────────────────────────────────────

def test_auth_context_resolution():
    # 1. Sem headers (fallback para DEFAULT_TEST_USER_ID)
    ctx1 = get_auth_context(authorization=None, x_user_id=None)
    assert ctx1.user_id == "00000000-0000-0000-0000-000000000000"
    assert ctx1.access_token is None
    assert ctx1.is_authenticated is False

    # 2. Com Bearer token
    ctx2 = get_auth_context(authorization="Bearer token_12345678_xyz", x_user_id=None)
    assert ctx2.access_token == "token_12345678_xyz"
    assert ctx2.user_id == "user_token_12"
    assert ctx2.is_authenticated is True

    # 3. Com X-User-ID explícito
    ctx3 = get_auth_context(authorization="Bearer abc", x_user_id="custom-uuid-999")
    assert ctx3.user_id == "custom-uuid-999"
    assert ctx3.access_token == "abc"
    assert ctx3.is_authenticated is True


# ── 3. PREDICT & XAI ENDPOINTS ────────────────────────────────────────────────

def test_predict_ndvi_success_with_xai_and_dss():
    payload = {
        "crop_id": "sugarcane",
        "chuva_acumulada_30d": 45.0,
        "chuva_acumulada_60d": 90.0,
        "chuva_acumulada_90d": 120.0,
        "GDA_mensal": 180.0,
        "include_xai": True,
        "scenario_name": "Irrigação +20mm",
        "mes_atual": 2,
    }
    res = client.post("/api/v1/predict/ndvi", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["crop_id"] == "sugarcane"
    assert data["crop_name"] == "Cana-de-Açúcar"
    assert 0.0 <= data["ndvi_previsto"] <= 1.0
    assert data["xai"] is not None
    assert "contributions" in data["xai"]
    assert data["dss"] is not None
    assert "status_title" in data["dss"]


def test_predict_ndvi_with_custom_baselines_and_no_xai():
    payload = {
        "crop_id": "soybean",
        "chuva_acumulada_30d": 20.0,
        "chuva_acumulada_60d": 60.0,
        "chuva_acumulada_90d": 80.0,
        "GDA_mensal": 150.0,
        "include_xai": False,
        "baseline_chuva_acumulada_30d": 35.0,
        "baseline_chuva_acumulada_60d": 70.0,
        "baseline_chuva_acumulada_90d": 100.0,
        "baseline_GDA_mensal": 160.0,
    }
    res = client.post("/api/v1/predict/ndvi", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["crop_id"] == "soybean"
    assert data["xai"] is None
    assert data["dss"] is None


def test_predict_ndvi_failure_and_exception_handling():
    # 1. Falha interna do modelo (retorna None)
    with patch("src.api.routers.predict.get_prediction", return_value=None):
        payload = {
            "crop_id": "sugarcane",
            "chuva_acumulada_30d": 30.0,
            "chuva_acumulada_60d": 60.0,
            "chuva_acumulada_90d": 90.0,
            "GDA_mensal": 100.0,
        }
        res = client.post("/api/v1/predict/ndvi", json=payload)
        assert res.status_code == 500
        assert "Falha ao executar o modelo" in res.json()["detail"]

    # 2. Cultura que levanta NotImplementedError (tratada pelo exception_handler)
    with patch("src.api.routers.predict.get_prediction", side_effect=NotImplementedError("Cultura em calibração")):
        res_nie = client.post("/api/v1/predict/ndvi", json=payload)
        assert res_nie.status_code == 400
        assert res_nie.json()["error_code"] == "CROP_IN_CALIBRATION"


# ── 4. FARMS & GEO CRUD ENDPOINTS ─────────────────────────────────────────────

def test_farms_crud_endpoints():
    mock_farms = [
        {
            "id": "farm-uuid-1",
            "user_id": "test-user-id",
            "farm_name": "Fazenda Modelo",
            "city": "Ribeirão Preto - SP",
            "lat": -21.17,
            "lon": -47.81,
            "area_ha": 250.0,
            "tipo_cultura": "Cana-de-Açúcar",
            "crop_id": "sugarcane",
            "boundary_geojson": {"type": "Polygon", "coordinates": []},
            "created_at": "2026-10-19T10:00:00Z",
        }
    ]

    # 1. Listar fazendas (GET)
    with patch("src.api.routers.farms.get_user_farms", return_value=mock_farms):
        res = client.get("/api/v1/farms", headers={"X-User-ID": "test-user-id"})
        assert res.status_code == 200
        farms = res.json()
        assert len(farms) == 1
        assert farms[0]["farm_name"] == "Fazenda Modelo"

    # 2. Criar fazenda (POST) com retorno de dados
    mock_res_db = MagicMock()
    mock_res_db.data = [mock_farms[0]]
    with patch("src.api.routers.farms.insert_farm", return_value=mock_res_db):
        create_payload = {
            "farm_name": "Fazenda Modelo",
            "city": "Ribeirão Preto - SP",
            "lat": -21.17,
            "lon": -47.81,
            "tipo_cultura": "Cana-de-Açúcar",
            "area_ha": 250.0,
        }
        res_create = client.post("/api/v1/farms", json=create_payload)
        assert res_create.status_code == 201
        assert res_create.json()["id"] == "farm-uuid-1"

    # 3. Criar fazenda (POST) com fallback quando res.data é vazio
    mock_res_empty = MagicMock()
    mock_res_empty.data = []
    with patch("src.api.routers.farms.insert_farm", return_value=mock_res_empty):
        res_fb = client.post("/api/v1/farms", json=create_payload)
        assert res_fb.status_code == 201
        assert res_fb.json()["id"] == "mock-created-id"

    # 4. Criar fazenda com erro no DB (400)
    with patch("src.api.routers.farms.insert_farm", side_effect=Exception("DB Conexão Recusada")):
        res_err = client.post("/api/v1/farms", json=create_payload)
        assert res_err.status_code == 400
        assert "Erro ao inserir fazenda" in res_err.json()["detail"]

    # 5. Atualizar fazenda (PUT)
    with patch("src.api.routers.farms.update_farm", return_value=MagicMock()):
        update_payload = {"farm_name": "Fazenda Boa Vista Renomeada", "area_ha": 300.0}
        res_up = client.put("/api/v1/farms/farm-uuid-1", json=update_payload)
        assert res_up.status_code == 200
        assert res_up.json()["status"] == "updated"
        assert "farm_name" in res_up.json()["updated_fields"]

    # 6. Atualizar sem campos fornecidos (400)
    res_up_empty = client.put("/api/v1/farms/farm-uuid-1", json={})
    assert res_up_empty.status_code == 400
    assert "Nenhum campo fornecido" in res_up_empty.json()["detail"]

    # 7. Atualizar com exceção no DB (400)
    with patch("src.api.routers.farms.update_farm", side_effect=Exception("Erro de constraint")):
        res_up_err = client.put("/api/v1/farms/farm-uuid-1", json={"farm_name": "Teste"})
        assert res_up_err.status_code == 400

    # 8. Excluir fazenda (DELETE)
    with patch("src.api.routers.farms.delete_farm", return_value=MagicMock()):
        res_del = client.delete("/api/v1/farms/farm-uuid-1")
        assert res_del.status_code == 200
        assert res_del.json()["status"] == "deleted"

    # 9. Excluir com exceção no DB (400)
    with patch("src.api.routers.farms.delete_farm", side_effect=Exception("Chave estrangeira ativa")):
        res_del_err = client.delete("/api/v1/farms/farm-uuid-1")
        assert res_del_err.status_code == 400


# ── 5. IOT TELEMETRY INGESTION ────────────────────────────────────────────────

def test_iot_telemetry_ingestion():
    telemetry_payload = {
        "device_id": "IOT-NODE-TALHAO-01",
        "talhao_id": "talhao_01",
        "crop_id": "sugarcane",
        "latitude": -21.1767,
        "longitude": -47.8208,
        "firmware_version": "v2.4.1-lmic",
        "readings": [
            {
                "timestamp": "2026-10-19T10:00:00Z",
                "hour": 10,
                "soil_moisture_surface_pct": 32.5,
                "soil_moisture_deep_pct": 38.0,
                "soil_temperature_celsius": 24.5,
                "leaf_wetness_index": 0.05,
                "leaf_is_wet": False,
                "battery_voltage": 3.95,
                "rssi_dbm": -72,
            }
        ],
    }

    # 1. Ingestão com sucesso (mock de Azure/disco)
    mock_upload_res = {
        "uploaded_to_cloud": True,
        "cloud_path": "https://azure.blob.core/bronze/telemetry.json",
        "local_path": "/tmp/telemetry.json",
    }
    with patch("src.api.routers.telemetry.upload_iot_telemetry_to_azure", return_value=mock_upload_res):
        res = client.post("/api/v1/telemetry/iot", json=telemetry_payload)
        assert res.status_code == 201
        data = res.json()
        assert data["status"] == "success"
        assert data["device_id"] == "IOT-NODE-TALHAO-01"
        assert data["readings_count"] == 1
        assert data["uploaded_to_cloud"] is True

    # 2. Ingestão com falha interna no upload (500)
    with patch("src.api.routers.telemetry.upload_iot_telemetry_to_azure", side_effect=Exception("Storage inacessível")):
        res_err = client.post("/api/v1/telemetry/iot", json=telemetry_payload)
        assert res_err.status_code == 500
        assert "Falha ao persistir telemetria" in res_err.json()["detail"]

    # 3. Ingestão com lote vazio de leituras (400)
    empty_payload = dict(telemetry_payload)
    empty_payload["readings"] = []
    res_empty = client.post("/api/v1/telemetry/iot", json=empty_payload)
    assert res_empty.status_code == 400
    assert "pelo menos uma leitura" in res_empty.json()["detail"]


# ── 6. PDF REPORT GENERATION ──────────────────────────────────────────────────

def test_pdf_report_generation():
    report_payload = {
        "farm_name": "Fazenda Boa Vista",
        "city": "Ribeirão Preto - SP",
        "payload": {"chuva_acumulada_30d": 50.0, "GDA_mensal": 170.0},
        "resultado": {"ndvi_previsto": 0.72, "status_vigor": "Vigor Médio/Alto"},
        "as_base64": False,
    }

    # 1. Download de stream binário de PDF (200 application/pdf)
    with patch("src.api.routers.reports.generate_pdf_report", return_value=b"%PDF-1.4 mock content"):
        res = client.post("/api/v1/reports/pdf", json=report_payload)
        assert res.status_code == 200
        assert res.headers["content-type"] == "application/pdf"
        assert b"%PDF-1.4 mock content" in res.content

    # 2. Download em formato JSON com Base64
    report_payload["as_base64"] = True
    with patch("src.api.routers.reports.generate_pdf_report", return_value=b"%PDF-1.4 base64 content"):
        res_b64 = client.post("/api/v1/reports/pdf", json=report_payload)
        assert res_b64.status_code == 200
        data = res_b64.json()
        assert data["content_type"] == "application/pdf"
        assert data["pdf_base64"] is not None
        assert data["size_bytes"] > 0

    # 3. Falha na geração do PDF (500)
    with patch("src.api.routers.reports.generate_pdf_report", side_effect=Exception("Erro de fonte")):
        res_fail = client.post("/api/v1/reports/pdf", json=report_payload)
        assert res_fail.status_code == 500
        assert "Falha ao gerar relatório" in res_fail.json()["detail"]


# ── 7. MLOPS DATA DRIFT AUDIT ─────────────────────────────────────────────────

def test_mlops_data_drift_status():
    mock_metric = FeatureDriftResult(
        feature_name="Precipitação (precipitation_sum)",
        ks_statistic=0.12,
        p_value=0.42,
        psi=0.045,
        drift_detected=False,
        severity="ESTÁVEL",
        baseline_mean=12.5,
        current_mean=13.0,
        baseline_std=4.2,
        current_std=4.0,
    )

    # 1. Status Saudável (HEALTHY)
    mock_report_healthy = DataDriftReport(
        timestamp="2026-10-19T10:00:00Z",
        total_features_evaluated=1,
        drifted_features_count=0,
        dataset_drift_detected=False,
        metrics={"precipitation_sum": mock_metric},
        alert_dispatched=False,
        summary="Sem deriva",
    )
    with patch("src.api.routers.mlops.detect_data_drift", return_value=mock_report_healthy):
        res1 = client.get("/api/v1/mlops/drift-status")
        assert res1.status_code == 200
        assert res1.json()["status"] == "HEALTHY"

    # 2. Status de Alerta (WARNING)
    mock_report_warning = DataDriftReport(
        timestamp="2026-10-19T10:00:00Z",
        total_features_evaluated=1,
        drifted_features_count=1,
        dataset_drift_detected=False,
        metrics={"precipitation_sum": mock_metric},
        alert_dispatched=False,
        summary="1 feature em alerta",
    )
    with patch("src.api.routers.mlops.detect_data_drift", return_value=mock_report_warning):
        res2 = client.get("/api/v1/mlops/drift-status")
        assert res2.status_code == 200
        assert res2.json()["status"] == "WARNING"

    # 3. Status de Deriva Crítica (DRIFT_DETECTED)
    mock_report_drift = DataDriftReport(
        timestamp="2026-10-19T10:00:00Z",
        total_features_evaluated=1,
        drifted_features_count=1,
        dataset_drift_detected=True,
        metrics={"precipitation_sum": mock_metric},
        alert_dispatched=True,
        summary="Deriva crítica detectada",
    )
    with patch("src.api.routers.mlops.detect_data_drift", return_value=mock_report_drift):
        res3 = client.get("/api/v1/mlops/drift-status")
        assert res3.status_code == 200
        assert res3.json()["status"] == "DRIFT_DETECTED"

    # 4. Falha na execução da auditoria (500)
    with patch("src.api.routers.mlops.detect_data_drift", side_effect=Exception("Dataset inacessível")):
        res_fail = client.get("/api/v1/mlops/drift-status")
        assert res_fail.status_code == 500
        assert "Falha ao executar auditoria" in res_fail.json()["detail"]


# ── 8. AUDIT LOGS ENDPOINT & MIDDLEWARE ───────────────────────────────────────

def test_audit_logs_endpoint():
    mock_logs = [
        {
            "id": "audit-uuid-1",
            "user_id": "test-user",
            "farm_id": "farm-uuid",
            "action": "UPDATE_FARM_ALERT_THRESHOLDS",
            "entity_type": "farm",
            "entity_id": "farm-uuid",
            "details": {"alert_amarelo": 0.55},
            "ip_address": "127.0.0.1",
            "trace_id": "trace-123",
            "created_at": "2026-10-19T10:00:00Z",
        }
    ]
    with patch("src.api.routers.audit.get_audit_logs", return_value=mock_logs):
        res = client.get("/api/v1/audit/logs?limit=20")
        assert res.status_code == 200
        data = res.json()
        assert len(data) == 1
        assert data[0]["action"] == "UPDATE_FARM_ALERT_THRESHOLDS"
        assert data[0]["trace_id"] == "trace-123"


def test_structured_logging_middleware_and_trace_id():
    # 1. Sem X-Trace-ID enviado -> API gera automaticamente e retorna no header
    res1 = client.get("/health")
    assert res1.status_code == 200
    assert "X-Trace-ID" in res1.headers
    assert len(res1.headers["X-Trace-ID"]) > 10

    # 2. Com X-Trace-ID fornecido pelo cliente -> preserva e propaga
    custom_trace = "custom-external-trace-999"
    res2 = client.get("/health", headers={"X-Trace-ID": custom_trace})
    assert res2.status_code == 200
    assert res2.headers["X-Trace-ID"] == custom_trace

    # 3. Health response contém circuit breakers
    assert "circuit_breakers" in res2.json()
    assert "open_meteo" in res2.json()["circuit_breakers"]


def test_structured_logging_middleware_exception_handling():
    # Valida bloco except Exception do middleware (linhas 97-104)
    with patch("src.api.routers.health.get_circuit_breakers_status", side_effect=RuntimeError("Falha middleware simulada")):
        with pytest.raises(RuntimeError):
            client.get("/health")


# ── 9. BACKGROUND JOBS & CACHE ENDPOINTS ──────────────────────────────────────

def test_jobs_batch_kpis_endpoint():
    payload = {
        "farm_ids": ["TALHAO_01", "TALHAO_02"],
        "crop_id": "sugarcane",
        "lat": -21.17,
        "lon": -47.81,
    }
    # 1. Sucesso com auditoria
    with patch("src.api.routers.jobs.log_audit_event") as mock_audit:
        res = client.post("/api/v1/jobs/batch-kpis", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert "job_id" in data
        assert data["job_type"] == "batch_kpis"
        assert "enfileirada com sucesso" in data["message"]
        mock_audit.assert_called_once()

    # 2. Sucesso mesmo com falha na auditoria
    with patch("src.api.routers.jobs.log_audit_event", side_effect=Exception("Audit DB offline")):
        res2 = client.post("/api/v1/jobs/batch-kpis", json=payload)
        assert res2.status_code == 202


def test_jobs_batch_reports_endpoint():
    payload = {
        "farm_ids": ["FAZENDA_01"],
        "crop_id": "soybean",
    }
    # 1. Sucesso com auditoria
    with patch("src.api.routers.jobs.log_audit_event") as mock_audit:
        res = client.post("/api/v1/jobs/batch-reports", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert data["job_type"] == "batch_reports"
        mock_audit.assert_called_once()

    # 2. Exceção na auditoria tratada
    with patch("src.api.routers.jobs.log_audit_event", side_effect=Exception("Audit offline")):
        res2 = client.post("/api/v1/jobs/batch-reports", json=payload)
        assert res2.status_code == 202


def test_jobs_batch_retrain_endpoint():
    payload = {
        "crops": ["sugarcane", "corn"],
    }
    # 1. Sucesso com auditoria
    with patch("src.api.routers.jobs.log_audit_event") as mock_audit:
        res = client.post("/api/v1/jobs/batch-retrain", json=payload)
        assert res.status_code == 202
        data = res.json()
        assert data["job_type"] == "model_retrain"
        mock_audit.assert_called_once()

    # 2. Exceção na auditoria tratada
    with patch("src.api.routers.jobs.log_audit_event", side_effect=Exception("Audit error")):
        res2 = client.post("/api/v1/jobs/batch-retrain", json=payload)
        assert res2.status_code == 202


def test_get_job_status_endpoint():
    # 1. Job não encontrado (404)
    res_404 = client.get("/api/v1/jobs/unknown-uuid-000")
    assert res_404.status_code == 404
    assert "não foi encontrado" in res_404.json()["detail"]

    # 2. Job existente
    post_res = client.post(
        "/api/v1/jobs/batch-kpis",
        json={"farm_ids": ["T1"], "crop_id": "sugarcane", "lat": -21.17, "lon": -47.81},
    )
    job_id = post_res.json()["job_id"]

    res_get = client.get(f"/api/v1/jobs/{job_id}")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["job_id"] == job_id
    assert "status" in data
    assert "progress" in data


def test_cancel_job_endpoint():
    # 1. Cancelar job inexistente (404)
    res_404 = client.post("/api/v1/jobs/unknown-uuid-999/cancel")
    assert res_404.status_code == 404

    # 2. Submeter tarefa lenta e cancelar com sucesso (200)
    from src.core.jobs import job_manager
    import time

    def slow_task(job_id):
        time.sleep(0.2)
        return {"done": True}

    job = job_manager.submit_job(job_type="cancellable_job", task_fn=slow_task)

    with patch("src.api.routers.jobs.log_audit_event") as mock_audit:
        res_cancel = client.post(f"/api/v1/jobs/{job.job_id}/cancel")
        assert res_cancel.status_code == 200
        assert res_cancel.json()["status"] == "cancelled"
        mock_audit.assert_called_once()

    # 3. Cancelar job com exceção na auditoria
    job2 = job_manager.submit_job(job_type="cancellable_job2", task_fn=slow_task)
    with patch("src.api.routers.jobs.log_audit_event", side_effect=Exception("Audit fail")):
        res_cancel2 = client.post(f"/api/v1/jobs/{job2.job_id}/cancel")
        assert res_cancel2.status_code == 200

    # 4. Cancelar job que já não pode mais ser cancelado (400)
    res_cancel_again = client.post(f"/api/v1/jobs/{job.job_id}/cancel")
    assert res_cancel_again.status_code == 400
    assert "Não é possível cancelar" in res_cancel_again.json()["detail"]


def test_list_jobs_endpoint():
    res = client.get("/api/v1/jobs?limit=5")
    assert res.status_code == 200
    data = res.json()
    assert "jobs" in data
    assert "total" in data
    assert isinstance(data["jobs"], list)

    res_filtered = client.get("/api/v1/jobs?status=cancelled&limit=5")
    assert res_filtered.status_code == 200


def test_cache_stats_and_clear_endpoints():
    # 1. Stats do cache
    res_stats = client.get("/api/v1/cache/stats")
    assert res_stats.status_code == 200
    data_stats = res_stats.json()
    assert "backend" in data_stats
    assert "hits" in data_stats
    assert "misses" in data_stats
    assert "hit_ratio_pct" in data_stats

    # 2. Limpar cache com auditoria
    with patch("src.api.routers.jobs.log_audit_event") as mock_audit:
        res_clear = client.post("/api/v1/cache/clear")
        assert res_clear.status_code == 200
        assert res_clear.json()["status"] == "ok"
        mock_audit.assert_called_once()

    # 3. Limpar cache com falha na auditoria tratada
    with patch("src.api.routers.jobs.log_audit_event", side_effect=Exception("Audit offline")):
        res_clear2 = client.post("/api/v1/cache/clear")
        assert res_clear2.status_code == 200
