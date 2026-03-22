#!/usr/bin/env python3
"""10k маршрутов + 10k точек + 10k назначений (связь с order_id из orders)."""

from __future__ import annotations

import argparse
import random
import sys
from datetime import datetime, timedelta, timezone

import psycopg2

from common import sync_dsn_from_env

DEFAULT_DSN = "postgresql://gastro:gastro@localhost:5432/logistics"

ROUTE_STATUSES = ("planning", "in_progress", "completed", "cancelled")
POINT_STATUSES = ("pending", "in_transit", "delivered", "failed")
ASSIGN_STATUSES = ("assigned", "picked_up", "delivered", "failed")


def seed(count: int, truncate: bool) -> None:
    dsn = sync_dsn_from_env("LOGISTICS_DATABASE_URL", DEFAULT_DSN)
    now = datetime.now(timezone.utc)

    route_rows = []
    for i in range(count):
        vid = random.randint(1, 500)
        did = random.randint(1, 200)
        dname = f"Driver {did}"
        st = random.choice(ROUTE_STATUSES)
        tw = round(random.uniform(10, 5000), 2)
        tv = round(random.uniform(1, 80), 2)
        td = round(random.uniform(5, 500), 2)
        start = now - timedelta(hours=random.randint(0, 48))
        est = start + timedelta(hours=random.randint(2, 24))
        route_rows.append((vid, did, dname, st, tw, tv, td, start, est, None))

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            if truncate:
                cur.execute("TRUNCATE TABLE route_assignments RESTART IDENTITY CASCADE")
                cur.execute("TRUNCATE TABLE route_points RESTART IDENTITY CASCADE")
                cur.execute("TRUNCATE TABLE routes RESTART IDENTITY CASCADE")

            for i in range(0, len(route_rows), 1000):
                chunk = route_rows[i : i + 1000]
                cur.executemany(
                    """
                    INSERT INTO routes (
                        vehicle_id, driver_id, driver_name, status,
                        total_weight, total_volume, total_distance,
                        start_time, estimated_end_time, actual_end_time
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    chunk,
                )

            cur.execute("SELECT id FROM routes ORDER BY id")
            route_ids = [r[0] for r in cur.fetchall()]

        point_rows = []
        for idx, rid in enumerate(route_ids[:count]):
            cid = random.randint(1, 10_000)
            addr = f"Address {rid}-{idx} City"
            seq = 1
            pst = random.choice(POINT_STATUSES)
            notes = None if random.random() > 0.5 else "call before"
            point_rows.append((rid, cid, addr, seq, pst, notes, None, None))

        with conn.cursor() as cur:
            for i in range(0, len(point_rows), 1000):
                chunk = point_rows[i : i + 1000]
                cur.executemany(
                    """
                    INSERT INTO route_points (
                        route_id, client_id, address, sequence, status,
                        notes, arrived_at, completed_at
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    chunk,
                )

            cur.execute("SELECT id, route_id FROM route_points ORDER BY id")
            rp = cur.fetchall()

        assign_rows = []
        for i, (rpid, rid) in enumerate(rp[:count]):
            oid = i + 1
            ast = random.choice(ASSIGN_STATUSES)
            assign_rows.append((rid, rpid, oid, ast))

        with conn.cursor() as cur:
            for i in range(0, len(assign_rows), 1000):
                chunk = assign_rows[i : i + 1000]
                cur.executemany(
                    """
                    INSERT INTO route_assignments (
                        route_id, route_point_id, order_id, status
                    )
                    VALUES (%s, %s, %s, %s)
                    """,
                    chunk,
                )
        conn.commit()
    finally:
        conn.close()

    print(
        f"logistics: inserted {len(route_ids)} routes, {len(point_rows)} points, {len(assign_rows)} assignments",
        file=sys.stderr,
    )


def main() -> None:
    p = argparse.ArgumentParser(description="Заполнить logistics")
    p.add_argument("--count", type=int, default=10_000)
    p.add_argument("--truncate", action="store_true")
    args = p.parse_args()
    seed(args.count, args.truncate)


if __name__ == "__main__":
    main()
