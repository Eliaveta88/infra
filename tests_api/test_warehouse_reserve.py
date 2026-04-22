"""Warehouse API: reserve / release stock against a freshly-received batch."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

CATALOG_PREFIX = "/catalog/api/v1/catalog"
WAREHOUSE_PREFIX = "/warehouse/api/v1/warehouse"


def _create_product(client) -> tuple[int, str]:
    suffix = uuid.uuid4().hex[:8]
    r = client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": f"Reserve Int Product {suffix}",
            "category": "integration",
            "price": 5.0,
            "sku": f"rsv-{suffix}",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    return body["id"], body["name"]


def _receive_batch(client, product_id: int, quantity: int = 10) -> None:
    exp = (datetime.now(timezone.utc) + timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
    r = client.post(
        f"{WAREHOUSE_PREFIX}/receive",
        json={
            "product_id": product_id,
            "quantity": quantity,
            "unit_type": "unit",
            "expiry_date": exp,
            "cell_location": "A-RSV",
            "batch_reference": f"BR-{uuid.uuid4().hex[:6]}",
        },
    )
    assert r.status_code == 201, r.text


def test_reserve_then_release_stock(client) -> None:
    product_id, _ = _create_product(client)
    _receive_batch(client, product_id, quantity=10)

    fake_order_id = 1_000_000_000 + int(uuid.uuid4().int % 1_000_000)
    r = client.post(
        f"{WAREHOUSE_PREFIX}/stock/reserve",
        json={
            "product_id": product_id,
            "quantity": 3,
            "order_id": fake_order_id,
            "unit_type": "unit",
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["product_id"] == product_id
    assert body["reserved_qty"] == 3
    reservation_id = body["reservation_id"]

    r = client.post(
        f"{WAREHOUSE_PREFIX}/stock/release",
        json={"reservation_id": reservation_id},
    )
    assert r.status_code == 200, r.text
    assert r.json().get("status") == "released"


def test_reserve_insufficient_stock_returns_400(client) -> None:
    product_id, _ = _create_product(client)
    _receive_batch(client, product_id, quantity=2)

    fake_order_id = 1_000_000_000 + int(uuid.uuid4().int % 1_000_000)
    r = client.post(
        f"{WAREHOUSE_PREFIX}/stock/reserve",
        json={
            "product_id": product_id,
            "quantity": 999,
            "order_id": fake_order_id,
            "unit_type": "unit",
        },
    )
    assert r.status_code == 400, r.text


def test_release_unknown_reservation_returns_404(client) -> None:
    r = client.post(
        f"{WAREHOUSE_PREFIX}/stock/release",
        json={"reservation_id": 999_999_991},
    )
    assert r.status_code == 404, r.text
