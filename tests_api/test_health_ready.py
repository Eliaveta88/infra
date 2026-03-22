"""Health and readiness for all services behind Traefik."""

from __future__ import annotations

import pytest

SERVICES = (
    "catalog",
    "finance",
    "identity",
    "warehouse",
    "logistics",
    "orders",
)


@pytest.mark.parametrize("service", SERVICES)
def test_health_ok(client, service: str) -> None:
    r = client.get(f"/{service}/api/v1/health")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "ok"
    assert data.get("service") == service


@pytest.mark.parametrize("service", SERVICES)
def test_ready_ok(client, service: str) -> None:
    r = client.get(f"/{service}/api/v1/ready")
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("status") == "ready"
    assert data.get("service") == service
