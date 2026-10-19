"""
Módulo de Structured Logging (JSON) Corporativo - OmniCrop AI.
Gera logs estruturados em formato JSON padronizado com correlação por trace_id, farm_id e medição de latência.
"""
from __future__ import annotations

import contextvars
import json
import logging
import sys
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, Optional

# Variáveis de contexto para propagação assíncrona/concorrente de rastreabilidade
trace_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("trace_id", default=None)
farm_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("farm_id", default=None)
user_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("user_id", default=None)


class JSONFormatter(logging.Formatter):
    """Formatador de logs em JSON com enriquecimento automático de metadados e observabilidade."""

    def format(self, record: logging.LogRecord) -> str:
        log_payload: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Injeta identificadores de rastreabilidade do contexto ou do registro extra
        current_trace = getattr(record, "trace_id", None) or trace_id_ctx.get()
        if current_trace:
            log_payload["trace_id"] = current_trace

        current_farm = getattr(record, "farm_id", None) or farm_id_ctx.get()
        if current_farm:
            log_payload["farm_id"] = current_farm

        current_user = getattr(record, "user_id", None) or user_id_ctx.get()
        if current_user:
            log_payload["user_id"] = current_user

        # Injeta latência caso calculada
        latency = getattr(record, "latency_ms", None) or getattr(record, "duration_ms", None)
        if latency is not None:
            log_payload["latency_ms"] = round(float(latency), 2)

        # Injeta campos extras customizados
        if hasattr(record, "extra_data") and isinstance(record.extra_data, dict):
            log_payload.update(record.extra_data)

        if record.exc_info:
            log_payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_payload, ensure_ascii=False)


def setup_logger(name: str = "omnicrop", level: int = logging.INFO) -> logging.Logger:
    """Configura e retorna uma instância de logger com saída JSON para stdout."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Evita duplicação de handlers caso já configurado
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.propagate = False

    return logger


# Instância global compartilhada de logger corporativo
logger = setup_logger("omnicrop")


def set_trace_context(
    trace_id: Optional[str] = None,
    farm_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> None:
    """Configura o contexto de rastreabilidade para a requisição ou thread ativa."""
    if trace_id is not None:
        trace_id_ctx.set(trace_id)
    if farm_id is not None:
        farm_id_ctx.set(farm_id)
    if user_id is not None:
        user_id_ctx.set(user_id)


def clear_trace_context() -> None:
    """Limpa o contexto de rastreabilidade."""
    trace_id_ctx.set(None)
    farm_id_ctx.set(None)
    user_id_ctx.set(None)


@contextmanager
def timed_stage(
    stage_name: str,
    custom_logger: Optional[logging.Logger] = None,
    extra: Optional[Dict[str, Any]] = None,
) -> Iterator[Dict[str, Any]]:
    """
    Context manager que cronometra a execução de um bloco de código
    e emite log estruturado em JSON com a latência precisa em milissegundos.
    """
    active_logger = custom_logger or logger
    start_time = time.perf_counter()
    metrics: Dict[str, Any] = {"stage": stage_name, "status": "running"}

    try:
        yield metrics
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        metrics["status"] = "success"
        metrics["latency_ms"] = round(elapsed_ms, 2)
        payload = dict(extra or {})
        payload.update(metrics)
        active_logger.info(
            f"Etapa concluída: {stage_name} em {elapsed_ms:.2f}ms",
            extra={"extra_data": payload, "latency_ms": elapsed_ms},
        )
    except Exception as exc:
        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        metrics["status"] = "failed"
        metrics["latency_ms"] = round(elapsed_ms, 2)
        payload = dict(extra or {})
        payload.update(metrics)
        payload["error"] = str(exc)
        active_logger.error(
            f"Etapa falhou: {stage_name} após {elapsed_ms:.2f}ms ({exc})",
            extra={"extra_data": payload, "latency_ms": elapsed_ms},
            exc_info=True,
        )
        raise
