#!/usr/bin/env python3
"""10k счетов + 10k транзакций в БД finance (FK: transactions -> accounts.client_id)."""

from __future__ import annotations

import argparse
import random
import sys
import uuid

import psycopg2
from decimal import Decimal

from common import sync_dsn_from_env

DEFAULT_DSN = "postgresql://gastro:gastro@localhost:5432/finance"


def seed_accounts(count: int, truncate: bool, conn) -> None:
    rows = []
    for client_id in range(1, count + 1):
        balance = Decimal(str(round(random.uniform(0, 50_000), 2)))
        credit = Decimal("100000.00")
        rows.append((client_id, balance, credit, "active"))

    with conn.cursor() as cur:
        if truncate:
            cur.execute("TRUNCATE TABLE transactions RESTART IDENTITY CASCADE")
            cur.execute("TRUNCATE TABLE accounts RESTART IDENTITY CASCADE")
        for i in range(0, len(rows), 1000):
            chunk = rows[i : i + 1000]
            cur.executemany(
                """
                INSERT INTO accounts (client_id, balance, credit_limit, status)
                VALUES (%s, %s, %s, %s)
                """,
                chunk,
            )


def seed_transactions(count: int, n_accounts: int, conn) -> None:
    types = ("payment", "invoice", "refund")
    statuses = ("pending", "completed", "failed", "cancelled")
    rows = []
    hi = max(1, n_accounts)
    for _ in range(count):
        client_id = random.randint(1, hi)
        amount = Decimal(str(round(random.uniform(1.0, 5_000.0), 2)))
        desc = f"tx {uuid.uuid4().hex[:12]}"
        tx_type = random.choice(types)
        status = random.choice(statuses)
        idem = f"idem-{uuid.uuid4().hex}"
        rows.append((client_id, amount, desc, tx_type, status, idem))

    with conn.cursor() as cur:
        for i in range(0, len(rows), 1000):
            chunk = rows[i : i + 1000]
            cur.executemany(
                """
                INSERT INTO transactions (
                    client_id, amount, description, transaction_type, status, idempotency_key
                )
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                chunk,
            )


def seed(account_count: int, tx_count: int, truncate: bool) -> None:
    dsn = sync_dsn_from_env("FINANCE_DATABASE_URL", DEFAULT_DSN)
    conn = psycopg2.connect(dsn)
    try:
        seed_accounts(account_count, truncate, conn)
        seed_transactions(tx_count, account_count, conn)
        conn.commit()
    finally:
        conn.close()
    print(
        f"finance: inserted {account_count} accounts, {tx_count} transactions",
        file=sys.stderr,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Заполнить finance.accounts и transactions")
    p.add_argument("--accounts", type=int, default=10_000, help="Количество счетов (client_id 1..N)")
    p.add_argument("--transactions", type=int, default=10_000, help="Количество транзакций")
    p.add_argument("--truncate", action="store_true", help="TRUNCATE transactions и accounts")
    args = p.parse_args()
    if args.transactions > 0 and args.accounts < 1:
        print("Нужен хотя бы 1 счёт для транзакций", file=sys.stderr)
        sys.exit(1)
    seed(args.accounts, args.transactions, args.truncate)


if __name__ == "__main__":
    main()
