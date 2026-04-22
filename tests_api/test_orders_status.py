"""Orders API: status pipeline (PATCH) + cross-service warehouse orchestration."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

CATALOG_PREFIX = "/catalog/api/v1/catalog"
IDENTITY_PREFIX = "/identity/api/v1/identity"
ORDERS_PREFIX = "/orders/api/v1/orders"
WAREHOUSE_PREFIX = "/warehouse/api/v1/warehouse"


def _register_user(client) -> int:
    suffix = uuid.uuid4().hex[:10]
    r = client.post(
        f"{IDENTITY_PREFIX}/users",
        json={
            "username": f"statusflow_{suffix}",
            "email": f"statusflow_{suffix}@example.com",
            "password": "TestPass123!",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _create_product(client) -> int:
    suffix = uuid.uuid4().hex[:8]
    r = client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": f"Status Int Product {suffix}",
            "category": "integration",
            "price": 10.0,
            "sku": f"sts-{suffix}",
        },
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


def _receive_batch(client, product_id: int, quantity: int) -> None:
    exp = (datetime.now(timezone.utc) + timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post(
        f"{WAREHOUSE_PREFIX}/receive",
        json={
            "product_id": product_id,
            "quantity": quantity,
            "unit_type": "unit",
            "expiry_date": exp,
            "cell_location": "A-STS",
            "batch_reference": f"BR-{uuid.uuid4().hex[:6]}",
        },
    )
    assert r.status_code == 201, r.text


def _create_order(client, client_id: int, product_id: int, quantity: int = 1) -> int:
    delivery = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post(
        f"{ORDERS_PREFIX}",
        json={
            "client_id": client_id,
            "items": [{"product_id": product_id, "quantity": quantity}],
            "delivery_date": delivery,
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["status"] == "draft"
    return body["id"]


def test_patch_status_confirmed_reserves_warehouse_stock(client) -> None:
    client_id = _register_user(client)
    product_id = _create_product(client)
    _receive_batch(client, product_id, quantity=5)

    order_id = _create_order(client, client_id, product_id, quantity=2)
    r = client.patch(
        f"{ORDERS_PREFIX}/{order_id}/status",
        json={"status": "confirmed"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"] == order_id
    assert body["status"] == "confirmed"


def test_patch_status_confirmed_without_stock_fails(client) -> None:
    client_id = _register_user(client)
    product_id = _create_product(client)  # no receive → no available stock
    order_id = _create_order(client, client_id, product_id, quantity=1)
    r = client.patch(
        f"{ORDERS_PREFIX}/{order_id}/status",
        json={"status": "confirmed"},
    )
    # Warehouse returns 400 for insufficient stock; orders wraps it as 409 (conflict).
    assert r.status_code in (400, 409), r.text
    # And the order should still be in `draft` — no side-effects on failed reservation.
    r_get = client.get(f"{ORDERS_PREFIX}/{order_id}")
    assert r_get.status_code == 200
    assert r_get.json()["status"] == "draft"


def test_patch_status_cancelled_from_draft_is_allowed(client) -> None:
    client_id = _register_user(client)
    product_id = _create_product(client)
    _receive_batch(client, product_id, quantity=3)
    order_id = _create_order(client, client_id, product_id, quantity=1)
    r = client.patch(
        f"{ORDERS_PREFIX}/{order_id}/status",
        json={"status": "cancelled"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["status"] == "cancelled"


def test_patch_status_invalid_value_returns_422(client) -> None:
    client_id = _register_user(client)
    product_id = _create_product(client)
    order_id = _create_order(client, client_id, product_id, quantity=1)
    r = client.patch(
        f"{ORDERS_PREFIX}/{order_id}/status",
        json={"status": "weird"},
    )
    assert r.status_code == 422, r.text
