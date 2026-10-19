"""
Módulo de Caching Centralizado e Distribuído - OmniCrop AI.
Suporta backend Redis para produção distribuída e fallback resiliente em memória (TTL)
para ambientes de desenvolvimento local, testes e CI/CD.
Otimizado para cache de dados climáticos por coordenada geocodificada (ex: weather:lat:lon).
"""
from __future__ import annotations

import functools
import json
import os
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.core.logger import logger

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:  # pragma: no cover
    redis = None  # type: ignore
    REDIS_AVAILABLE = False


class BaseCacheBackend(ABC):
    """Interface abstrata para backends de cache."""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Obtém um valor do cache."""

    @abstractmethod
    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        """Armazena um valor com tempo de expiração em segundos."""

    @abstractmethod
    def delete(self, key: str) -> bool:
        """Remove uma chave do cache."""

    @abstractmethod
    def clear(self) -> bool:
        """Limpa todo o conteúdo do cache."""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """Verifica se uma chave existe e não expirou."""

    @abstractmethod
    def keys(self, pattern: str = "*") -> List[str]:
        """Retorna lista de chaves ativas."""


class MemoryCacheBackend(BaseCacheBackend):
    """
    Backend de cache em memória de alta performance com expiração TTL.
    Thread-safe com locks reentrantes, ideal para ambientes de desenvolvimento e fallback.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[Any, float]] = {}
        self._lock = threading.RLock()

    def _is_expired(self, key: str) -> bool:
        if key not in self._store:
            return True
        _, expire_at = self._store[key]
        if expire_at > 0 and time.time() > expire_at:
            del self._store[key]
            return True
        return False

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if self._is_expired(key):
                return None
            val, _ = self._store[key]
            return val

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        with self._lock:
            expire_at = time.time() + ttl_seconds if ttl_seconds > 0 else 0.0
            self._store[key] = (value, expire_at)
            return True

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._store:
                del self._store[key]
                return True
            return False

    def clear(self) -> bool:
        with self._lock:
            self._store.clear()
            return True

    def exists(self, key: str) -> bool:
        with self._lock:
            return not self._is_expired(key)

    def keys(self, pattern: str = "*") -> List[str]:
        with self._lock:
            # Filtra chaves expiradas
            valid_keys = [k for k in list(self._store.keys()) if not self._is_expired(k)]
            if pattern == "*":
                return valid_keys
            import fnmatch
            return fnmatch.filter(valid_keys, pattern)


class RedisCacheBackend(BaseCacheBackend):
    """
    Backend de cache corporativo conectado a cluster ou instância Redis.
    Serializa dados em formato JSON padronizado com suporte a TTL nativo do Redis.
    """

    def __init__(self, client: Any) -> None:
        self.client = client

    def _serialize(self, value: Any) -> str:
        return json.dumps(value, default=str)

    def _deserialize(self, raw_str: str) -> Any:
        try:
            return json.loads(raw_str)
        except Exception:
            return raw_str

    def get(self, key: str) -> Optional[Any]:
        try:
            raw = self.client.get(key)
            if raw is None:
                return None
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8")
            return self._deserialize(raw)
        except Exception as exc:
            logger.warning(f"Erro ao ler chave [{key}] do Redis: {exc}")
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        try:
            payload = self._serialize(value)
            if ttl_seconds > 0:
                self.client.setex(key, ttl_seconds, payload)
            else:
                self.client.set(key, payload)
            return True
        except Exception as exc:
            logger.warning(f"Erro ao gravar chave [{key}] no Redis: {exc}")
            return False

    def delete(self, key: str) -> bool:
        try:
            res = self.client.delete(key)
            return bool(res > 0)
        except Exception as exc:
            logger.warning(f"Erro ao deletar chave [{key}] no Redis: {exc}")
            return False

    def clear(self) -> bool:
        try:
            self.client.flushdb()
            return True
        except Exception as exc:
            logger.warning(f"Erro ao limpar banco Redis: {exc}")
            return False

    def exists(self, key: str) -> bool:
        try:
            return bool(self.client.exists(key))
        except Exception as exc:
            logger.warning(f"Erro ao checar existência da chave [{key}] no Redis: {exc}")
            return False

    def keys(self, pattern: str = "*") -> List[str]:
        try:
            raw_keys = self.client.keys(pattern)
            decoded = []
            for k in raw_keys:
                if isinstance(k, bytes):
                    decoded.append(k.decode("utf-8"))
                else:
                    decoded.append(str(k))
            return decoded
        except Exception as exc:
            logger.warning(f"Erro ao listar chaves do Redis: {exc}")
            return []


class CacheManager:
    """
    Gerenciador Centralizado de Cache do OmniCrop AI.
    Alterna de forma transparente entre Redis e memória local.
    """

    def __init__(self, redis_url: Optional[str] = None) -> None:
        self._backend: BaseCacheBackend
        self._is_redis = False
        self._hits = 0
        self._misses = 0
        self._lock = threading.RLock()
        self.init_backend(redis_url)

    def init_backend(self, redis_url: Optional[str] = None) -> None:
        """Inicializa ou reconecta o backend apropriado."""
        url = redis_url or os.getenv("REDIS_URL")
        host = os.getenv("REDIS_HOST")
        port = int(os.getenv("REDIS_PORT", "6379"))
        password = os.getenv("REDIS_PASSWORD")
        db = int(os.getenv("REDIS_DB", "0"))

        client = None
        if REDIS_AVAILABLE and (url or host):
            try:
                if url:
                    client = redis.Redis.from_url(url, socket_timeout=2.0)
                else:
                    client = redis.Redis(
                        host=host,
                        port=port,
                        password=password,
                        db=db,
                        socket_timeout=2.0,
                    )
                client.ping()
                self._backend = RedisCacheBackend(client)
                self._is_redis = True
                logger.info("⚡ Conexão com Redis estabelecida com sucesso para caching centralizado.")
                return
            except Exception as exc:
                logger.warning(f"⚠️ Não foi possível conectar ao Redis ({exc}). Ativando fallback para cache em memória.")

        # Fallback padrão seguro
        self._backend = MemoryCacheBackend()
        self._is_redis = False

    def get(self, key: str) -> Optional[Any]:
        val = self._backend.get(key)
        with self._lock:
            if val is not None:
                self._hits += 1
            else:
                self._misses += 1
        return val

    def set(self, key: str, value: Any, ttl_seconds: int = 3600) -> bool:
        return self._backend.set(key, value, ttl_seconds)

    def delete(self, key: str) -> bool:
        return self._backend.delete(key)

    def clear(self) -> bool:
        with self._lock:
            self._hits = 0
            self._misses = 0
        return self._backend.clear()

    def exists(self, key: str) -> bool:
        return self._backend.exists(key)

    def is_redis(self) -> bool:
        return self._is_redis

    def get_stats(self) -> Dict[str, Any]:
        """Retorna telemetria operacional de hits, misses e chaves ativas."""
        with self._lock:
            total_requests = self._hits + self._misses
            hit_ratio = (self._hits / total_requests * 100.0) if total_requests > 0 else 0.0
            keys_list = self._backend.keys()
            return {
                "backend": "redis" if self._is_redis else "in_memory",
                "connected": True,
                "hits": self._hits,
                "misses": self._misses,
                "total_requests": total_requests,
                "hit_ratio_pct": round(hit_ratio, 2),
                "keys_count": len(keys_list),
            }


# Instância global singleton do CacheManager
cache_manager = CacheManager()


def make_weather_cache_key(lat: float, lon: float, date_str: Optional[str] = None) -> str:
    """
    Gera chave canônica de cache para previsões climáticas por coordenada geocodificada.
    Arredonda lat/lon para 2 casas decimais (~1.1 km de resolução espacial),
    garantindo agrupamento inteligente de talhões próximos na mesma fazenda.
    """
    lat_r = round(float(lat), 2)
    lon_r = round(float(lon), 2)
    suffix = f":{date_str}" if date_str else ""
    return f"weather:{lat_r:.2f}:{lon_r:.2f}{suffix}"


def cached(
    prefix: str,
    ttl_seconds: int = 3600,
    key_builder: Optional[Callable[..., str]] = None,
) -> Callable:
    """
    Decorador corporativo para caching de funções determinísticas.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if key_builder is not None:
                cache_key = key_builder(*args, **kwargs)
            else:
                arg_repr = [str(a) for a in args]
                kwarg_repr = [f"{k}={v}" for k, v in sorted(kwargs.items())]
                signature = ":".join(arg_repr + kwarg_repr)
                cache_key = f"{prefix}:{signature}" if signature else prefix

            val = cache_manager.get(cache_key)
            if val is not None:
                return val

            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, ttl_seconds=ttl_seconds)
            return result
        return wrapper
    return decorator
