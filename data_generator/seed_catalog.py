#!/usr/bin/env python3
"""~10k товаров в БД catalog."""

from __future__ import annotations

import argparse
import random
import sys

import psycopg2

from common import sync_dsn_from_env

DEFAULT_DSN = "postgresql://gastro:gastro@localhost:5432/catalog"

CATEGORIES = (
    "dairy",
    "meat",
    "bakery",
    "produce",
    "frozen",
    "beverages",
    "dry_goods",
    "spices",
)


def seed(count: int, truncate: bool) -> None:
    dsn = sync_dsn_from_env("CATALOG_DATABASE_URL", DEFAULT_DSN)
    rows = []
    for i in range(1, count + 1):
        name = f"Generated product {i}"
        category = random.choice(CATEGORIES)
        price = round(random.uniform(5.0, 9_999.0), 2)
        sku = f"GEN-{i:08d}"
        rows.append((name, category, price, sku, True, False))

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            if truncate:
                cur.execute("TRUNCATE TABLE products RESTART IDENTITY CASCADE")
            for chunk_start in range(0, len(rows), 1000):
                chunk = rows[chunk_start : chunk_start + 1000]
                cur.executemany(
                    """
                    INSERT INTO products (name, category, price, sku, in_stock, is_deleted)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    chunk,
                )
        conn.commit()
    finally:
        conn.close()
    print(f"catalog: inserted {count} products", file=sys.stderr)


def main() -> None:
    p = argparse.ArgumentParser(description="Заполнить catalog.products")
    p.add_argument(
        "--count",
        type=int,
        default=10_000,
        help="Количество строк (по умолчанию 10000)",
    )
    p.add_argument(
        "--truncate",
        action="store_true",
        help="Очистить products перед вставкой (TRUNCATE ... RESTART IDENTITY)",
    )
    args = p.parse_args()
    seed(args.count, args.truncate)


if __name__ == "__main__":
    main()
