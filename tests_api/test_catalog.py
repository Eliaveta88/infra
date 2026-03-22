"""Catalog API: list, autocomplete, CRUD."""

from __future__ import annotations

import uuid


CATALOG_PREFIX = "/catalog/api/v1/catalog"


def test_list_products(client) -> None:
    r = client.get(f"{CATALOG_PREFIX}/products", params={"skip": 0, "limit": 10})
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


def test_autocomplete_products(client) -> None:
    r = client.get(
        f"{CATALOG_PREFIX}/products/autocomplete",
        params={"query": "test", "limit": 5},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body
    assert "total" in body


def test_product_crud_flow(client) -> None:
    suffix = uuid.uuid4().hex[:8]
    sku = f"api-test-{suffix}"
    create_payload = {
        "name": f"API Test Product {suffix}",
        "category": "integration",
        "price": 99.5,
        "sku": sku,
    }
    r = client.post(f"{CATALOG_PREFIX}/products", json=create_payload)
    assert r.status_code == 201, r.text
    created = r.json()
    product_id = created["id"]
    assert created["name"] == create_payload["name"]
    assert created["sku"] == sku

    r = client.get(f"{CATALOG_PREFIX}/products/{product_id}")
    assert r.status_code == 200, r.text
    assert r.json()["id"] == product_id

    r = client.patch(
        f"{CATALOG_PREFIX}/products/{product_id}",
        json={"name": f"Updated {suffix}"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["name"] == f"Updated {suffix}"

    r = client.delete(f"{CATALOG_PREFIX}/products/{product_id}")
    assert r.status_code == 204, r.text

    r = client.get(f"{CATALOG_PREFIX}/products/{product_id}")
    assert r.status_code == 404


def test_get_product_not_found(client) -> None:
    r = client.get(f"{CATALOG_PREFIX}/products/999999999")
    assert r.status_code == 404
