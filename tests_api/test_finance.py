"""Finance API: transactions list, balance, create transaction, invoice."""

from __future__ import annotations

import uuid

import pytest

FINANCE_PREFIX = "/finance/api/v1/finance"
ORDERS_PREFIX = "/orders/api/v1/orders"


def test_revenue_summary_ok(client) -> None:
    r = client.get(
        f"{FINANCE_PREFIX}/accounts/1/revenue",
        params={
            "from": "2020-01-01T00:00:00+00:00",
            "to": "2030-01-01T00:00:00+00:00",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["client_id"] == 1
    assert "total_amount" in body
    assert body.get("currency") == "RUB"


def test_revenue_summary_invalid_range(client) -> None:
    r = client.get(
        f"{FINANCE_PREFIX}/accounts/1/revenue",
        params={
            "from": "2030-01-01T00:00:00+00:00",
            "to": "2020-01-01T00:00:00+00:00",
        },
    )
    assert r.status_code == 422, r.text


def test_list_transactions_empty_or_ok(client) -> None:
    r = client.get(
        f"{FINANCE_PREFIX}/transactions",
        params={"client_id": 1, "skip": 0, "limit": 10},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "items" in body
    assert "total" in body


def test_get_balance_not_found_or_ok(client) -> None:
    r = client.get(f"{FINANCE_PREFIX}/accounts/999999001/balance")
    assert r.status_code in (200, 404), r.text


def test_get_balance_structure_when_exists(client) -> None:
    r = client.get(f"{FINANCE_PREFIX}/accounts/1/balance")
    if r.status_code == 404:
        pytest.skip("No finance account for client_id=1")
    assert r.status_code == 200, r.text
    body = r.json()
    assert "balance" in body
    assert "credit_limit" in body
    assert body.get("currency") == "RUB"


def test_generate_invoice(client) -> None:
    """Uses a real order from the orders list + finance account for that client."""
    r = client.get(f"{ORDERS_PREFIX}", params={"skip": 0, "limit": 20})
    assert r.status_code == 200, r.text
    items = r.json().get("items") or []
    if not items:
        pytest.skip("No orders — cannot test invoice generation end-to-end")
    order = items[0]
    client_id = order["client_id"]
    order_id = order["id"]
    b = client.get(f"{FINANCE_PREFIX}/accounts/{client_id}/balance")
    if b.status_code == 404:
        pytest.skip("No finance account for this client")
    r = client.post(
        f"{FINANCE_PREFIX}/invoices/generate",
        json={"client_id": client_id, "order_ids": [order_id]},
    )
    assert r.status_code == 201, r.text
    data = r.json()
    assert "invoice_id" in data
    assert data["client_id"] == client_id
    assert "pdf_url" in data
    assert "created_at" in data


def test_create_transaction_requires_account(
    client,
    finance_client_id_with_account: int | None,
) -> None:
    if finance_client_id_with_account is None:
        pytest.skip(
            "No row in finance.accounts for client_id=1 — create account or run migrations with seed."
        )
    key = f"test-{uuid.uuid4()}"
    r = client.post(
        f"{FINANCE_PREFIX}/transactions",
        json={
            "client_id": finance_client_id_with_account,
            "amount": "10.00",
            "description": "integration test",
            "idempotency_key": key,
            "transaction_type": "payment",
        },
        headers={"Idempotency-Key": key},
    )
    assert r.status_code == 201, r.text
    body = r.json()
    assert body["client_id"] == finance_client_id_with_account
    assert body["status"] == "pending"


def test_create_transaction_idempotent(
    client, finance_client_id_with_account: int | None
) -> None:
    if finance_client_id_with_account is None:
        pytest.skip("No finance account for client_id=1")
    key = f"idem-{uuid.uuid4()}"
    payload = {
        "client_id": finance_client_id_with_account,
        "amount": "5.00",
        "description": "idempotency test",
        "idempotency_key": key,
        "transaction_type": "payment",
    }
    r1 = client.post(
        f"{FINANCE_PREFIX}/transactions",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    r2 = client.post(
        f"{FINANCE_PREFIX}/transactions",
        json=payload,
        headers={"Idempotency-Key": key},
    )
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json().get("id") == r2.json().get("id")
