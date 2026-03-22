#!/usr/bin/env python3
"""10k заказов + по одной позиции (order_items) в БД orders."""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import psycopg2

from common import sync_dsn_from_env

DEFAULT_DSN = "postgresql://gastro:gastro@localhost:5432/orders"

STATUSES = ("draft", "confirmed", "in_delivery", "closed", "cancelled")
ITEM_STATUSES = ("pending", "reserved", "picked", "delivered", "failed")


def seed(count: int, max_product_id: int, truncate: bool) -> None:
    dsn = sync_dsn_from_env("ORDERS_DATABASE_URL", DEFAULT_DSN)
    now = datetime.now(timezone.utc)

    order_rows = []
    for i in range(count):
        cid = random.randint(1, min(10_000, max(1, count)))
        name = f"Client {cid}"
        total = Decimal(str(round(random.uniform(100, 99_999.99), 2)))
        st = random.choice(STATUSES)
        delivery = now + timedelta(days=random.randint(1, 60))
        route = random.choice((None, random.randint(1, 5000)))
        notes = None if random.random() > 0.3 else f"note-{i}"
        order_rows.append((cid, name, total, st, delivery, route, notes))

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            if truncate:
                cur.execute("TRUNCATE TABLE order_status_history RESTART IDENTITY CASCADE")
                cur.execute("TRUNCATE TABLE order_items RESTART IDENTITY CASCADE")
                cur.execute("TRUNCATE TABLE orders RESTART IDENTITY CASCADE")

            for i in range(0, len(order_rows), 1000):
                chunk = order_rows[i : i + 1000]
                cur.executemany(
                    """
                    INSERT INTO orders (
                        client_id, client_name, total_amount, status,
                        delivery_date, route_id, notes
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    chunk,
                )

            cur.execute("SELECT id FROM orders ORDER BY id")
            order_ids = [r[0] for r in cur.fetchall()]

        item_rows = []
        for oid in order_ids[:count]:
            pid = random.randint(1, max(1, max_product_id))
            pname = f"Product {pid}"
            qty = round(random.uniform(1, 100), 2)
            unit_p = Decimal(str(round(random.uniform(10, 5000), 2)))
            total = Decimal(str(round(float(qty) * float(unit_p), 2)))
            ist = random.choice(ITEM_STATUSES)
            item_rows.append((oid, pid, pname, qty, unit_p, total, ist))

        with conn.cursor() as cur:
            for i in range(0, len(item_rows), 1000):
                chunk = item_rows[i : i + 1000]
                cur.executemany(
                    """
                    INSERT INTO order_items (
                        order_id, product_id, product_name, quantity,
                        unit_price, total, status
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """,
                    chunk,
                )
        conn.commit()
    finally:
        conn.close()

    print(f"orders: inserted {len(order_ids)} orders and {len(item_rows)} order_items", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Заполнить orders и order_items")
    p.add_argument("--count", type=int, default=10_000)
    p.add_argument("--max-product-id", type=int, default=10_000)
    p.add_argument("--truncate", action="store_true")
    args = p.parse_args()
    seed(args.count, args.max_product_id, args.truncate)


if __name__ == "__main__":
    main()
