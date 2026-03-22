#!/usr/bin/env python3
"""10k партий (batches) + 10k строк stock в БД warehouse."""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone

import psycopg2

from common import sync_dsn_from_env

DEFAULT_DSN = "postgresql://gastro:gastro@localhost:5432/warehouse"

UNITS = ("unit", "kg", "liter", "piece")


def seed(count: int, max_product_id: int, truncate: bool) -> None:
    dsn = sync_dsn_from_env("WAREHOUSE_DATABASE_URL", DEFAULT_DSN)
    now = datetime.now(timezone.utc)

    batches_rows = []
    for i in range(1, count + 1):
        product_id = random.randint(1, max(1, max_product_id))
        qty = round(random.uniform(1, 500), 2)
        unit = random.choice(UNITS)
        expiry = now + timedelta(days=random.randint(30, 730))
        bref = f"GEN-BREF-{i:08d}"
        status = random.choice(("in_stock", "partially_reserved", "fully_reserved", "expired"))
        batches_rows.append((product_id, qty, unit, expiry, bref, status))

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            if truncate:
                cur.execute("TRUNCATE TABLE reservations RESTART IDENTITY CASCADE")
                cur.execute("TRUNCATE TABLE stock RESTART IDENTITY CASCADE")
                cur.execute("TRUNCATE TABLE batches RESTART IDENTITY CASCADE")

            for i in range(0, len(batches_rows), 1000):
                chunk = batches_rows[i : i + 1000]
                cur.executemany(
                    """
                    INSERT INTO batches (
                        product_id, quantity_received, unit_type, expiry_date,
                        batch_reference, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    chunk,
                )

            cur.execute(
                "SELECT id, product_id, quantity_received, unit_type, expiry_date, batch_reference FROM batches ORDER BY id"
            )
            batch_rows = cur.fetchall()

        stock_rows = []
        for row in batch_rows[:count]:
            bid, pid, qty_rec, unit, exp, bref = row
            pname = f"Product {pid}"
            qav = float(qty_rec) * random.uniform(0.3, 1.0)
            qrs = float(qty_rec) - qav
            cell = f"A-{random.randint(1, 99)}-{random.randint(1, 99)}"
            stock_rows.append(
                (bid, pid, pname, round(qav, 2), round(max(0, qrs), 2), unit, cell, exp, bref)
            )

        with conn.cursor() as cur:
            for i in range(0, len(stock_rows), 1000):
                chunk = stock_rows[i : i + 1000]
                cur.executemany(
                    """
                    INSERT INTO stock (
                        batch_id, product_id, product_name,
                        quantity_available, quantity_reserved, unit_type,
                        cell_location, expiry_date, batch_reference
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    chunk,
                )
        conn.commit()
    finally:
        conn.close()

    print(f"warehouse: inserted {count} batches and {len(stock_rows)} stock rows", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Заполнить warehouse.batches и stock")
    p.add_argument("--count", type=int, default=10_000)
    p.add_argument(
        "--max-product-id",
        type=int,
        default=10_000,
        help="Случайный product_id в [1..N] (согласуйте с числом товаров в catalog)",
    )
    p.add_argument("--truncate", action="store_true")
    args = p.parse_args()
    seed(args.count, args.max_product_id, args.truncate)


if __name__ == "__main__":
    main()
