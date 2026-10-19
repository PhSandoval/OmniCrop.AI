"""
Testes unitários para Structured Logging (JSON) e Circuit Breakers de Resiliência.
Garante 100% de cobertura em src/core/logger.py e src/core/resilience.py.
"""
import json
import logging
from unittest.mock import MagicMock
import pytest
import pybreaker

from src.core.logger import (
    JSONFormatter,
    clear_trace_context,
    logger as global_logger,
    set_trace_context,
    setup_logger,
    timed_stage,
)
from src.core.resilience import (
    ALL_BREAKERS,
    OmniCropCircuitBreakerListener,
    get_circuit_breakers_status,
    open_meteo_breaker,
    with_circuit_breaker,
)


# ── 1. STRUCTURED LOGGING TESTS ───────────────────────────────────────────────

def test_json_formatter_all_fields():
    formatter = JSONFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Teste de log estruturado",
        args=(),
        exc_info=None,
    )
    record.module = "test_module"
    record.funcName = "test_func"
    record.trace_id = "trace-uuid-123"
    record.farm_id = "farm-uuid-456"
    record.user_id = "user-uuid-789"
    record.latency_ms = 45.67
    record.extra_data = {"custom_metric": 99.9}

    formatted_str = formatter.format(record)
    parsed = json.loads(formatted_str)

    assert parsed["level"] == "INFO"
    assert parsed["message"] == "Teste de log estruturado"
    assert parsed["trace_id"] == "trace-uuid-123"
    assert parsed["farm_id"] == "farm-uuid-456"
    assert parsed["user_id"] == "user-uuid-789"
    assert parsed["latency_ms"] == 45.67
    assert parsed["custom_metric"] == 99.9


def test_json_formatter_context_fallback_and_exception():
    formatter = JSONFormatter()
    set_trace_context(trace_id="ctx-trace", farm_id="ctx-farm", user_id="ctx-user")

    try:
        raise ValueError("Falha intencional de teste")
    except ValueError:
        import sys
        exc_info = sys.exc_info()

    record = logging.LogRecord(
        name="test_logger",
        level=logging.ERROR,
        pathname="test_file.py",
        lineno=100,
        msg="Erro com stack trace",
        args=(),
        exc_info=exc_info,
    )
    record.module = "test_mod"
    record.funcName = "test_func"

    formatted_str = formatter.format(record)
    parsed = json.loads(formatted_str)

    assert parsed["trace_id"] == "ctx-trace"
    assert parsed["farm_id"] == "ctx-farm"
    assert parsed["user_id"] == "ctx-user"
    assert "exception" in parsed
    assert "ValueError: Falha intencional de teste" in parsed["exception"]

    clear_trace_context()


def test_setup_logger_and_timed_stage():
    custom_log = setup_logger("test_custom_logger")
    # Segunda chamada não duplica handlers
    same_log = setup_logger("test_custom_logger")
    assert len(same_log.handlers) == 1

    # timed_stage sucesso
    with timed_stage("etapa_sucesso", custom_logger=custom_log, extra={"crop": "sugarcane"}) as metrics:
        assert metrics["stage"] == "etapa_sucesso"
        assert metrics["status"] == "running"

    # timed_stage falha
    with pytest.raises(RuntimeError):
        with timed_stage("etapa_falha", custom_logger=custom_log):
            raise RuntimeError("Erro na etapa")


# ── 2. CIRCUIT BREAKER & RESILIENCE TESTS ─────────────────────────────────────

def test_circuit_breaker_listener_events():
    listener = OmniCropCircuitBreakerListener()
    mock_cb = MagicMock()
    mock_cb.name = "TestBreaker"
    mock_cb.fail_counter = 1

    old_state = MagicMock()
    old_state.name = "closed"
    new_state = MagicMock()
    new_state.name = "open"

    # Testa transição de estado e falha
    listener.state_change(mock_cb, old_state, new_state)
    listener.failure(mock_cb, Exception("Conexão recusada"))
    listener.success(mock_cb)


def test_with_circuit_breaker_decorator_success_and_fallback():
    test_breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=10, name="UnitTestBreaker")

    def fallback_mock(x: int, **kwargs) -> int:
        return x * 100

    @with_circuit_breaker(test_breaker, fallback_fn=fallback_mock)
    def fragile_function(x: int, fail: bool = False) -> int:
        if fail:
            raise ConnectionError("Serviço indisponível")
        return x * 2

    # 1. Sucesso normal
    assert fragile_function(5, fail=False) == 10

    # 2. Primeira falha (circuito ainda fechado)
    with pytest.raises(ConnectionError):
        fragile_function(5, fail=True)

    # 3. Segunda falha -> Trip do circuito (abre o circuito e aciona fallback)
    fallback_res = fragile_function(5, fail=True)
    assert fallback_res == 500
    assert test_breaker.current_state == "open"

    # 4. Chamada subsequente com circuito aberto executa o fallback
    assert fragile_function(5, fail=False) == 500


def test_with_circuit_breaker_no_fallback_raises_circuit_breaker_error():
    test_breaker = pybreaker.CircuitBreaker(fail_max=2, reset_timeout=10, name="NoFallbackBreaker")

    @with_circuit_breaker(test_breaker, fallback_fn=None)
    def failing_fn():
        raise TimeoutError("Timeout na API")

    # Primeira falha: circuito ainda fechado (lança TimeoutError)
    with pytest.raises(TimeoutError):
        failing_fn()

    # Segunda falha: atinge fail_max e abre o circuito (lança CircuitBreakerError)
    with pytest.raises(pybreaker.CircuitBreakerError):
        failing_fn()


def test_get_circuit_breakers_status():
    status = get_circuit_breakers_status()
    assert "open_meteo" in status
    assert "gemini" in status
    assert "azure_storage" in status
    assert status["open_meteo"]["name"] == "OpenMeteo"
    assert "state" in status["open_meteo"]
    assert "fail_counter" in status["open_meteo"]
