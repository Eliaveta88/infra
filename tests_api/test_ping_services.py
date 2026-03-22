"""Ping endpoints for warehouse, logistics, orders."""

from __future__ import annotations


def test_warehouse_ping(client) -> None:
    r = client.get("/warehouse/api/v1/warehouse/ping")
    assert r.status_code == 200, r.text
    assert r.json().get("module") == "warehouse"


def test_logistics_ping(client) -> None:
    r = client.get("/logistics/api/v1/logistics/ping")
    assert r.status_code == 200, r.text
    assert r.json().get("module") == "logistics"


def test_orders_ping(client) -> None:
    r = client.get("/orders/api/v1/orders/ping")
    assert r.status_code == 200, r.text
    assert r.json().get("module") == "orders"
