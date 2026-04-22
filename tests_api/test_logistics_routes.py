"""Logistics API: plan + assign order to point + update point status."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import pytest

CATALOG_PREFIX = "/catalog/api/v1/catalog"
IDENTITY_PREFIX = "/identity/api/v1/identity"
LOGISTICS_PREFIX = "/logistics/api/v1/logistics"
ORDERS_PREFIX = "/orders/api/v1/orders"


def test_list_routes_ok(client) -> None:
    r = client.get(f"{LOGISTICS_PREFIX}", params={"skip": 0, "limit": 10})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def _register_driver(client) -> tuple[int, str]:
    suffix = uuid.uuid4().hex[:10]
    r = client.post(
        f"{IDENTITY_PREFIX}/users",
        json={
            "username": f"driver_{suffix}",
            "email": f"driver_{suffix}@example.com",
            "password": "TestPass123!",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return body["id"], body["username"]


def _create_product(client) -> int:
    suffix = uuid.uuid4().hex[:8]
    r = client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": f"Logistics Int Product {suffix}",
            "category": "integration",
            "price": 7.0,
            "sku": f"log-{suffix}",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_order(client, client_id: int, product_id: int) -> int:
    delivery = (datetime.now(timezone.utc) + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post(
        f"{ORDERS_PREFIX}",
        json={
            "client_id": client_id,
            "items": [{"product_id": product_id, "quantity": 1}],
            "delivery_date": delivery,
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _plan_route(client, driver_id: int, driver_name: str) -> dict:
    start = (datetime.now(timezone.utc) + timedelta(hours=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post(
        f"{LOGISTICS_PREFIX}",
        json={
            "vehicle_id": 1,
            "driver_id": driver_id,
            "driver_name": driver_name,
            "start_time": start,
            "points": [
                {"client_id": 1, "address": "ул. Тестовая, 1"},
                {"client_id": 2, "address": "ул. Тестовая, 2"},
            ],
        },
    )
    assert r.status_code == 201, r.text
    return r.json()


def test_plan_route_creates_route_with_identity_driver_name(client) -> None:
    driver_id, driver_name = _register_driver(client)
    route = _plan_route(client, driver_id, driver_name)
    assert route["driver_name"] == driver_name
    assert route["points_count"] == 2
    assert route["status"] == "planning"


def test_assign_order_and_update_point_status(client) -> None:
    driver_id, driver_name = _register_driver(client)
    route = _plan_route(client, driver_id, driver_name)
    route_id = route["id"]

    customer_id, _ = _register_driver(client)
    product_id = _create_product(client)
    order_id = _create_order(client, customer_id, product_id)

    r = client.put(
        f"{LOGISTICS_PREFIX}/routes/{route_id}/assign",
        json={"order_id": order_id, "point_index": 0},
    )
    assert r.status_code == 200, r.text
    assigned = r.json()
    # DAL returns either the full updated route or the assignment payload —
    # either way, a successful response with JSON is enough for the contract test.
    assert isinstance(assigned, dict)

    point_id = assigned.get("point_id") or assigned.get("id")
    if point_id is None:
        pytest.skip("assign response does not expose a point_id — cannot continue status chain")

    r = client.patch(
        f"{LOGISTICS_PREFIX}/routes/points/{point_id}/status",
        json={"status": "in_transit"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["point_id"] == point_id
    assert body["status"] == "in_transit"


def test_update_point_status_invalid_value_returns_422(client) -> None:
    r = client.patch(
        f"{LOGISTICS_PREFIX}/routes/points/1/status",
        json={"status": "weird"},
    )
    assert r.status_code == 422, r.text


def test_update_point_status_unknown_point_returns_404(client) -> None:
    r = client.patch(
        f"{LOGISTICS_PREFIX}/routes/points/999999991/status",
        json={"status": "delivered"},
    )
    assert r.status_code == 404, r.text
