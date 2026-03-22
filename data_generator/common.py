"""Общие настройки подключения к Postgres (синхронно, без asyncpg)."""

from __future__ import annotations

import os
from urllib.parse import urlparse


def sync_dsn_from_env(env_name: str, default: str) -> str:
    """Берёт DSN из env; async URL превращает в sync для psycopg."""
    raw = os.environ.get(env_name, default).strip()
    return async_to_sync_dsn(raw)


def async_to_sync_dsn(url: str) -> str:
    """postgresql+asyncpg://... -> postgresql://..."""
    u = url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return u


def parse_host_port(dsn: str) -> tuple[str, int]:
    p = urlparse(dsn)
    host = p.hostname or "localhost"
    port = p.port or 5432
    return host, port
