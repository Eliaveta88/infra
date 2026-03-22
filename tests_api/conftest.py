"""Pytest fixtures for live API integration tests."""

from __future__ import annotations

import os
from typing import Generator

import httpx
import pytest


def _base_url() -> str:
    return os.environ.get("API_BASE_URL", "http://localhost").rstrip("/")


@pytest.fixture(scope="session")
def api_base_url() -> str:
    """Base URL of Traefik (e.g. http://localhost). Paths include service prefix."""
    return _base_url()


@pytest.fixture
def client(api_base_url: str) -> Generator[httpx.Client, None, None]:
    """Sync HTTP client with sane timeout."""
    timeout = float(os.environ.get("API_HTTP_TIMEOUT", "30"))
    with httpx.Client(
        base_url=api_base_url, timeout=timeout, follow_redirects=True
    ) as c:
        yield c


@pytest.fixture(scope="session")
def finance_client_id_with_account(api_base_url: str) -> int | None:
    """If GET .../balance for client_id=1 returns 200, transactions can be created."""
    with httpx.Client(base_url=api_base_url, timeout=15.0) as c:
        r = c.get("/finance/api/v1/finance/accounts/1/balance")
        if r.status_code == 200:
            return 1
    return None
