"""Orders API: create order uses catalog + identity integration."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

CATALOG_PREFIX = "/catalog/api/v1/catalog"
IDENTITY_PREFIX = "/identity/api/v1/identity"
ORDERS_PREFIX = "/orders/api/v1/orders"


def _unique_user() -> tuple[str, str, str]:
    suffix = uuid.uuid4().hex[:10]
    username = f"ordtest_{suffix}"
    email = f"{username}@example.com"
    password = "TestPass123!"
    return username, email, password


def test_create_order_resolves_catalog_and_identity(client) -> None:
    """Register user, create product, POST order — client_name and line names match services."""
    username, email, password = _unique_user()
    r = client.post(
        f"{IDENTITY_PREFIX}/users",
        json={"username": username, "email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    client_id = r.json()["id"]

    suffix = uuid.uuid4().hex[:8]
    sku = f"ord-sku-{suffix}"
    r = client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": f"Order Int Product {suffix}",
            "category": "integration",
            "price": 42.5,
            "sku": sku,
        },
    )
    assert r.status_code == 201, r.text
    product = r.json()
    product_id = product["id"]
    product_name = product["name"]

    delivery = (datetime.now(timezone.utc) + timedelta(days=14)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post(
        f"{ORDERS_PREFIX}",
        json={
            "client_id": client_id,
            "items": [{"product_id": product_id, "quantity": 2}],
            "delivery_date": delivery,
            "notes": "api integration",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["client_id"] == client_id
    assert body["client_name"] == username
    assert len(body["items"]) == 1
    line = body["items"][0]
    assert line["product_id"] == product_id
    assert line["product_name"] == product_name
    assert line["unit_price"] == 42.5
    assert line["total"] == 85.0


def test_create_order_unknown_product_returns_400(client) -> None:
    username, email, password = _unique_user()
    r = client.post(
        f"{IDENTITY_PREFIX}/users",
        json={"username": username, "email": email, "password": password},
    )
    assert r.status_code == 201, r.text
    client_id = r.json()["id"]
    delivery = (datetime.now(timezone.utc) + timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post(
        f"{ORDERS_PREFIX}",
        json={
            "client_id": client_id,
            "items": [{"product_id": 999_999_991, "quantity": 1}],
            "delivery_date": delivery,
        },
    )
    assert r.status_code == 400, r.text


def test_list_orders_ok(client) -> None:
    r = client.get(f"{ORDERS_PREFIX}", params={"skip": 0, "limit": 5})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data
