"""
Testes unitários para o Módulo de Cache Centralizado e Background Jobs.
Garante 100% de cobertura de código em src/core/cache.py e src/core/jobs.py.
"""
import time
from unittest.mock import MagicMock, patch
import pytest

from src.core.cache import (
    BaseCacheBackend,
    CacheManager,
    MemoryCacheBackend,
    RedisCacheBackend,
    cached,
    make_weather_cache_key,
)
from src.core.jobs import (
    JobManager,
    JobRecord,
    JobStatus,
    task_batch_kpis,
    task_batch_reports,
    task_batch_retrain,
)


# ── 1. TESTES DE CACHE EM MEMÓRIA (TTL) ──────────────────────────────────────────

def test_memory_cache_backend_crud_and_expiration():
    mem = MemoryCacheBackend()

    # 1. Set e Get com TTL
    assert mem.set("key1", "val1", ttl_seconds=60) is True
    assert mem.get("key1") == "val1"
    assert mem.exists("key1") is True

    # 2. Chave inexistente
    assert mem.get("non_existent") is None
    assert mem.exists("non_existent") is False

    # 3. Chave com TTL=0 (não expira)
    assert mem.set("key_permanent", 42, ttl_seconds=0) is True
    assert mem.get("key_permanent") == 42

    # 4. Expiração simulada
    mem._store["key_expired"] = ("expired_val", time.time() - 10.0)
    assert mem.get("key_expired") is None
    assert mem.exists("key_expired") is False

    # 5. Delete
    assert mem.delete("key1") is True
    assert mem.delete("key1") is False

    # 6. Keys e Padrões
    mem.set("agro:farm1", 100)
    mem.set("agro:farm2", 200)
    mem.set("weather:sp", 300)
    assert sorted(mem.keys("*")) == sorted(["key_permanent", "agro:farm1", "agro:farm2", "weather:sp"])
    assert sorted(mem.keys("agro:*")) == sorted(["agro:farm1", "agro:farm2"])

    # 7. Clear
    assert mem.clear() is True
    assert mem.keys() == []


# ── 2. TESTES DE CACHE REDIS (MOCK) ──────────────────────────────────────────────

def test_redis_cache_backend_crud_and_fallbacks():
    mock_redis = MagicMock()
    backend = RedisCacheBackend(mock_redis)

    # 1. Serialization e Deserialization
    assert backend._serialize({"a": 1}) == '{"a": 1}'
    assert backend._deserialize('{"a": 1}') == {"a": 1}
    assert backend._deserialize("invalid-json{") == "invalid-json{"

    # 2. Get com bytes, str e None
    mock_redis.get.return_value = b'{"status": "ok"}'
    assert backend.get("test_key") == {"status": "ok"}

    mock_redis.get.return_value = '{"status": "str_ok"}'
    assert backend.get("test_key_str") == {"status": "str_ok"}

    mock_redis.get.return_value = None
    assert backend.get("missing_key") is None

    # 3. Set com TTL > 0 e TTL == 0
    assert backend.set("key_ttl", {"x": 10}, ttl_seconds=300) is True
    mock_redis.setex.assert_called_with("key_ttl", 300, '{"x": 10}')

    assert backend.set("key_no_ttl", [1, 2], ttl_seconds=0) is True
    mock_redis.set.assert_called_with("key_no_ttl", '[1, 2]')

    # 4. Delete e Exists
    mock_redis.delete.return_value = 1
    assert backend.delete("k1") is True

    mock_redis.delete.return_value = 0
    assert backend.delete("k_none") is False

    mock_redis.exists.return_value = 1
    assert backend.exists("k_exists") is True

    # 5. Clear (flushdb)
    assert backend.clear() is True
    mock_redis.flushdb.assert_called_once()

    # 6. Keys decodificadas (bytes e str)
    mock_redis.keys.return_value = [b"k:1", "k:2"]
    assert backend.keys("k:*") == ["k:1", "k:2"]

    # 7. Resiliência a Exceções no Cliente Redis
    mock_redis.get.side_effect = Exception("Redis connection lost")
    assert backend.get("err_key") is None

    mock_redis.setex.side_effect = Exception("Redis write timeout")
    assert backend.set("err_key", "val", ttl_seconds=60) is False

    mock_redis.delete.side_effect = Exception("Redis error")
    assert backend.delete("err_key") is False

    mock_redis.flushdb.side_effect = Exception("Redis flush error")
    assert backend.clear() is False

    mock_redis.exists.side_effect = Exception("Redis exists error")
    assert backend.exists("err_key") is False

    mock_redis.keys.side_effect = Exception("Redis keys error")
    assert backend.keys() == []


# ── 3. TESTES DO CACHEMANAGER E DECORADORES ──────────────────────────────────────

def test_cache_manager_initialization_and_operations():
    # 1. Inicialização padrão (fallback memória)
    cm = CacheManager()
    assert cm.is_redis() is False

    # 2. Inicialização com REDIS_URL mockado (sucesso)
    mock_client = MagicMock()
    mock_client.ping.return_value = True
    with patch("redis.Redis.from_url", return_value=mock_client):
        cm_redis = CacheManager(redis_url="redis://localhost:6379/0")
        assert cm_redis.is_redis() is True

    # 3. Inicialização com REDIS_HOST mockado (sucesso)
    with patch.dict("os.environ", {"REDIS_HOST": "10.0.0.1", "REDIS_PORT": "6380", "REDIS_PASSWORD": "pass"}):
        with patch("redis.Redis", return_value=mock_client):
            cm_host = CacheManager()
            assert cm_host.is_redis() is True

    # 4. Falha na conexão com Redis (deve ativar fallback memória sem quebrar)
    mock_failing_client = MagicMock()
    mock_failing_client.ping.side_effect = Exception("Connection refused")
    with patch("redis.Redis.from_url", return_value=mock_failing_client):
        cm_fallback = CacheManager(redis_url="redis://localhost:9999/0")
        assert cm_fallback.is_redis() is False

    # 5. Operações e Telemetria (hits, misses, ratio)
    cm.clear()
    assert cm.get("miss") is None
    cm.set("hit_key", "stored_val")
    assert cm.get("hit_key") == "stored_val"
    assert cm.exists("hit_key") is True
    assert cm.delete("hit_key") is True

    stats = cm.get_stats()
    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["total_requests"] == 2
    assert stats["hit_ratio_pct"] == 50.0

    # 6. Clear zera contadores
    cm.clear()
    assert cm.get_stats()["total_requests"] == 0
    assert cm.get_stats()["hit_ratio_pct"] == 0.0


def test_make_weather_cache_key():
    key1 = make_weather_cache_key(-21.1734, -47.8122)
    assert key1 == "weather:-21.17:-47.81"

    key2 = make_weather_cache_key(-21.17, -47.81, date_str="2026-10-19")
    assert key2 == "weather:-21.17:-47.81:2026-10-19"


def test_cached_decorator():
    call_count = 0

    @cached(prefix="test_calc", ttl_seconds=60)
    def calculate_kpi(a: int, b: int) -> int:
        nonlocal call_count
        call_count += 1
        return a * 10 + b

    # 1ª chamada: Cache miss
    res1 = calculate_kpi(3, 5)
    assert res1 == 35
    assert call_count == 1

    # 2ª chamada: Cache hit (não incrementa call_count)
    res2 = calculate_kpi(3, 5)
    assert res2 == 35
    assert call_count == 1

    # Chamada com key_builder customizado
    custom_calls = 0

    @cached(prefix="custom", ttl_seconds=60, key_builder=lambda x: f"custom:{x.upper()}")
    def custom_func(x: str) -> str:
        nonlocal custom_calls
        custom_calls += 1
        return f"processed_{x}"

    assert custom_func("agro") == "processed_agro"
    assert custom_calls == 1
    assert custom_func("agro") == "processed_agro"
    assert custom_calls == 1


# ── 4. TESTES DE BACKGROUND JOBS (JOBMANAGER) ───────────────────────────────────

def test_job_record_serialization():
    rec = JobRecord(
        job_type="batch_test",
        status=JobStatus.PENDING,
        payload={"farms": [1, 2]},
    )
    d = rec.to_dict()
    assert d["job_type"] == "batch_test"
    assert d["status"] == "pending"

    rec2 = JobRecord.from_dict(d)
    assert rec2.job_id == rec.job_id
    assert rec2.status == JobStatus.PENDING


def test_job_manager_success_execution():
    jm = JobManager(max_workers=2)

    def simple_task(job_id: str, multiplier: int) -> dict:
        jm.update_progress(job_id, 50.0, "Metade processada")
        return {"result": 10 * multiplier}

    job = jm.submit_job(job_type="test_success", task_fn=simple_task, multiplier=5)
    assert job.status in [JobStatus.PENDING, JobStatus.RUNNING, JobStatus.COMPLETED]

    # Aguarda conclusão da thread assíncrona
    for _ in range(50):
        retrieved = jm.get_job(job.job_id)
        if retrieved and retrieved.status == JobStatus.COMPLETED:
            break
        time.sleep(0.02)

    retrieved = jm.get_job(job.job_id)
    assert retrieved is not None
    assert retrieved.status == JobStatus.COMPLETED
    assert retrieved.progress == 100.0
    assert retrieved.result == {"result": 50}
    assert retrieved.completed_at is not None

    jm.shutdown(wait=True)


def test_job_manager_failure_execution():
    jm = JobManager(max_workers=1)

    def failing_task(job_id: str) -> dict:
        raise ValueError("Simulação de falha catastrófica de processamento")

    job = jm.submit_job(job_type="test_fail", task_fn=failing_task)

    for _ in range(50):
        retrieved = jm.get_job(job.job_id)
        if retrieved and retrieved.status == JobStatus.FAILED:
            break
        time.sleep(0.02)

    retrieved = jm.get_job(job.job_id)
    assert retrieved is not None
    assert retrieved.status == JobStatus.FAILED
    assert "Simulação de falha" in str(retrieved.error)
    assert retrieved.completed_at is not None

    jm.shutdown(wait=True)


def test_job_manager_cancellation_and_listing():
    jm = JobManager(max_workers=2)

    # Cria um job com atraso proposital e cancela enquanto executa/aguarda
    def slow_task(job_id: str) -> dict:
        time.sleep(0.1)
        return {"ok": True}

    job1 = jm.submit_job(job_type="batch_cancel", task_fn=slow_task)
    assert jm.cancel_job(job1.job_id) is True

    # Tentativa de cancelar job inexistente
    assert jm.cancel_job("invalid-job-id") is False

    # Listagem de jobs e filtro por status
    jobs_all = jm.list_jobs(limit=10)
    assert len(jobs_all) >= 1

    jobs_cancelled = jm.list_jobs(limit=10, status="cancelled")
    assert all(j.status == JobStatus.CANCELLED for j in jobs_cancelled)

    # Cancelamento de job já concluído deve retornar False
    job_completed = JobRecord(job_type="completed", status=JobStatus.COMPLETED)
    jm._jobs[job_completed.job_id] = job_completed
    assert jm.cancel_job(job_completed.job_id) is False

    # Status stats
    stats = jm.get_stats()
    assert "total_jobs" in stats
    assert "pending" in stats
    assert "completed" in stats
    assert "failed" in stats
    assert "cancelled" in stats
    assert stats["max_workers"] == 2

    # Recuperação via cache fallback
    mock_job = JobRecord(job_type="cached_job", status=JobStatus.COMPLETED)
    with patch("src.core.jobs.cache_manager.get", return_value=mock_job.to_dict()):
        recovered = jm.get_job("external-cached-job-id")
        assert recovered is not None
        assert recovered.job_type == "cached_job"

    # get_job com id inexistente no cache e memória
    with patch("src.core.jobs.cache_manager.get", return_value=None):
        assert jm.get_job("completely-unknown-job-id") is None

    # update_progress fallback no cache com status PENDING
    mock_pending_job = JobRecord(job_type="cached_pending_job", status=JobStatus.PENDING)
    with patch("src.core.jobs.cache_manager.get", return_value=mock_pending_job.to_dict()):
        jm.update_progress("external-pending-job-id", progress=75.0, message="Avanço")
        assert jm.get_job("external-pending-job-id").status == JobStatus.RUNNING
        assert jm.get_job("external-pending-job-id").progress == 75.0

    # update_progress com id que não existe em lugar nenhum
    with patch("src.core.jobs.cache_manager.get", return_value=None):
        jm.update_progress("completely-unknown-job", progress=50.0)

    # worker_wrapper quando o job é cancelado antes de iniciar
    cancelled_job = JobRecord(job_type="pre_cancelled", status=JobStatus.CANCELLED)
    jm._jobs[cancelled_job.job_id] = cancelled_job
    jm._worker_wrapper(cancelled_job.job_id, task_fn=lambda **kwargs: {})
    assert jm.get_job(cancelled_job.job_id).status == JobStatus.CANCELLED

    jm.shutdown(wait=True)


# ── 5. TESTES DAS TAREFAS AGRONÔMICAS EM BACKGROUND ─────────────────────────────

def test_task_batch_kpis_all_branches():
    # 1. Lista vazia
    empty_res = task_batch_kpis("job_empty", farm_ids=[])
    assert empty_res["processed_farms"] == 0
    assert empty_res["results"] == []

    # 2. Múltiplos talhões exercitando diferentes ramos de estresse hídrico
    farms = [f"TALHAO_{i:03d}" for i in range(12)]
    res = task_batch_kpis("job_batch", farm_ids=farms, crop_id="sugarcane")
    assert res["processed_farms"] == 12
    assert "critical_alerts_count" in res
    assert len(res["results"]) == 12
    assert res["crop_evaluated"] == "Cana-de-Açúcar"

    # Valida campos de recomendação
    for item in res["results"]:
        assert "farm_id" in item
        assert "deficit_hidrico_mm" in item
        assert item["status_hidrico"] in ["ADEQUADO", "DEFICIT_MODERADO", "ESTRESSE_CRITICO"]
        assert "recomendacao_irrigacao_mm" in item


def test_task_batch_reports():
    farms = ["FAZENDA_ALVORADA", "FAZENDA_SANTA_FE"]
    res = task_batch_reports("job_reports", farm_ids=farms, crop_id="soybean")
    assert res["total_reports"] == 2
    assert len(res["reports"]) == 2
    assert res["reports"][0]["farm_id"] == "FAZENDA_ALVORADA"
    assert res["reports"][0]["status"] == "ready"
    assert "/api/v1/reports/download/" in res["reports"][0]["download_url"]


def test_task_batch_retrain():
    crops = ["sugarcane", "soybean", "corn"]
    res = task_batch_retrain("job_retrain", crops=crops)
    assert res["crops_evaluated"] == 3
    assert len(res["evaluations"]) == 3
    assert res["evaluations"][0]["crop"] == "sugarcane"
    assert res["evaluations"][0]["status"] == "calibrated"
    assert res["evaluations"][0]["r2_score"] == 0.89
