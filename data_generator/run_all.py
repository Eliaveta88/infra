#!/usr/bin/env python3
"""
Полный прогон генерации (в порядке зависимостей между БД).

Порядок:
1. catalog — товары (product_id 1..N)
2. finance — счета и транзакции
3. warehouse — партии и stock (product_id ссылается на каталог)
4. orders — заказы и позиции (order_id 1..N)
5. logistics — маршруты; route_assignments order_id=1..N (уникально)

Identity не трогаем.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd), file=sys.stderr)
    r = subprocess.run(cmd, cwd=ROOT)
    if r.returncode != 0:
        sys.exit(r.returncode)


def main() -> None:
    p = argparse.ArgumentParser(description="Запустить все seed_* скрипты")
    p.add_argument("--count", type=int, default=10_000)
    p.add_argument(
        "--truncate",
        action="store_true",
        help="TRUNCATE перед вставкой во всех сервисах",
    )
    args = p.parse_args()
    c = args.count
    py = sys.executable

    run(
        [py, str(ROOT / "seed_catalog.py"), "--count", str(c)]
        + (["--truncate"] if args.truncate else [])
    )
    run(
        [
            py,
            str(ROOT / "seed_finance.py"),
            "--accounts",
            str(c),
            "--transactions",
            str(c),
        ]
        + (["--truncate"] if args.truncate else [])
    )
    run(
        [
            py,
            str(ROOT / "seed_warehouse.py"),
            "--count",
            str(c),
            "--max-product-id",
            str(c),
        ]
        + (["--truncate"] if args.truncate else [])
    )
    run(
        [
            py,
            str(ROOT / "seed_orders.py"),
            "--count",
            str(c),
            "--max-product-id",
            str(c),
        ]
        + (["--truncate"] if args.truncate else [])
    )
    run(
        [py, str(ROOT / "seed_logistics.py"), "--count", str(c)]
        + (["--truncate"] if args.truncate else [])
    )
    print("run_all: готово", file=sys.stderr)


if __name__ == "__main__":
    main()
