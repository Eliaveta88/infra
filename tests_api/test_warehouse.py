"""Warehouse API: receive batch resolves product name from catalog."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

CATALOG_PREFIX = "/catalog/api/v1/catalog"
WAREHOUSE_PREFIX = "/warehouse/api/v1/warehouse"


def test_list_stock_ok(client) -> None:
    r = client.get(f"{WAREHOUSE_PREFIX}", params={"skip": 0, "limit": 20})
    assert r.status_code == 200, r.text
    data = r.json()
    assert "items" in data
    assert "total" in data
    assert isinstance(data["items"], list)


def _find_stock_by_batch_id(client, batch_id: int) -> dict | None:
    """Paginate stock list (FEFO order — new batch may be on last page)."""
    skip = 0
    limit = 100
    while True:
        r = client.get(f"{WAREHOUSE_PREFIX}", params={"skip": skip, "limit": limit})
        if r.status_code != 200:
            return None
        data = r.json()
        items = data.get("items") or []
        for row in items:
            if row.get("batch_id") == batch_id:
                return row
        total = data.get("total") or 0
        skip += len(items)
        if skip >= total or not items:
            return None


def test_receive_batch_uses_catalog_product_name(client) -> None:
    suffix = uuid.uuid4().hex[:8]
    sku = f"wh-{suffix}"
    name = f"WH Int Product {suffix}"
    r = client.post(
        f"{CATALOG_PREFIX}/products",
        json={
            "name": name,
            "category": "integration",
            "price": 10.0,
            "sku": sku,
        },
    )
    assert r.status_code == 201, r.text
    product_id = r.json()["id"]

    exp = (datetime.now(timezone.utc) + timedelta(days=180)).strftime("%Y-%m-%dT%H:%M:%SZ")
    batch_ref = f"BR-{suffix}"
    r = client.post(
        f"{WAREHOUSE_PREFIX}/receive",
        json={
            "product_id": product_id,
            "quantity": 5,
            "unit_type": "unit",
            "expiry_date": exp,
            "cell_location": "A-1",
            "batch_reference": batch_ref,
        },
    )
    assert r.status_code == 201, r.text
    receive_body = r.json()
    assert receive_body.get("product_id") == product_id
    batch_id = receive_body["batch_id"]

    match = _find_stock_by_batch_id(client, batch_id)
    assert match is not None, "expected stock row for received batch"
    assert match.get("product_name") == name
    assert match.get("product_id") == product_id
