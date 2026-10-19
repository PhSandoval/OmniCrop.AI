"""
Módulo de Resiliência e Circuit Breakers Corporativos - OmniCrop AI.
Protege o sistema contra lentidão, indisponibilidade ou esgotamento de taxa em APIs externas
(Open-Meteo, Google Gemini, Azure Blob Storage) utilizando o padrão Circuit Breaker (pybreaker).
"""
from __future__ import annotations

import functools
from typing import Any, Callable, Dict, Optional
import pybreaker

from src.core.logger import logger


class OmniCropCircuitBreakerListener(pybreaker.CircuitBreakerListener):
    """Observador de transições de estado dos Circuit Breakers com Structured Logging."""

    def state_change(self, cb: pybreaker.CircuitBreaker, old_state: Any, new_state: Any) -> None:
        logger.warning(
            f"⚡ Transição de Circuit Breaker [{cb.name}]: {old_state.name} -> {new_state.name}",
            extra={"extra_data": {"circuit_breaker": cb.name, "old_state": old_state.name, "new_state": new_state.name}},
        )

    def failure(self, cb: pybreaker.CircuitBreaker, exc: Exception) -> None:
        logger.error(
            f"❌ Falha registrada no Circuit Breaker [{cb.name}]: {exc}",
            extra={"extra_data": {"circuit_breaker": cb.name, "error": str(exc), "fail_counter": cb.fail_counter}},
        )

    def success(self, cb: pybreaker.CircuitBreaker) -> None:
        pass


# Criação dos Circuit Breakers especializados
listener = OmniCropCircuitBreakerListener()

open_meteo_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="OpenMeteo",
    listeners=[listener],
)

gemini_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=45,
    name="Gemini",
    listeners=[listener],
)

azure_storage_breaker = pybreaker.CircuitBreaker(
    fail_max=3,
    reset_timeout=30,
    name="AzureStorage",
    listeners=[listener],
)

ALL_BREAKERS: Dict[str, pybreaker.CircuitBreaker] = {
    "open_meteo": open_meteo_breaker,
    "gemini": gemini_breaker,
    "azure_storage": azure_storage_breaker,
}


def with_circuit_breaker(
    breaker: pybreaker.CircuitBreaker,
    fallback_fn: Optional[Callable[..., Any]] = None,
) -> Callable:
    """
    Decorador para envolver chamadas de I/O de rede com Circuit Breaker e fallback seguro.
    Se o circuito estiver ABERTO (Open), evita chamadas externas que possam gerar travamentos
    e delega para a rotina de contingência (fallback_fn).
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return breaker(func)(*args, **kwargs)
            except pybreaker.CircuitBreakerError as cb_err:
                logger.warning(
                    f"⚠️ Circuito [{breaker.name}] ABERTO. Executando fallback de contingência ({cb_err}).",
                    extra={"extra_data": {"circuit": breaker.name, "fallback": fallback_fn.__name__ if fallback_fn else "none"}},
                )
                if fallback_fn is not None:
                    return fallback_fn(*args, **kwargs)
                raise
        return wrapper
    return decorator


def get_circuit_breakers_status() -> Dict[str, Dict[str, Any]]:
    """Retorna o estado operacional e métricas de todos os Circuit Breakers para observabilidade."""
    status_dict: Dict[str, Dict[str, Any]] = {}
    for key, cb in ALL_BREAKERS.items():
        status_dict[key] = {
            "name": cb.name,
            "state": cb.current_state,
            "fail_counter": cb.fail_counter,
            "fail_max": cb.fail_max,
            "reset_timeout_seconds": cb.reset_timeout,
        }
    return status_dict
