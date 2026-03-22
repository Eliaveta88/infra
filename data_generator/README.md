# Генератор данных (без Identity)

Скрипты на **Python 3** + **psycopg2-binary** заполняют Postgres **~10 000 записей** на сервис (или заданное `--count`):

| Скрипт | БД | Что вставляется |
|--------|-----|-----------------|
| `seed_catalog.py` | `catalog` | `products` |
| `seed_finance.py` | `finance` | `accounts` (N шт.) + `transactions` (M шт.) |
| `seed_warehouse.py` | `warehouse` | `batches` + `stock` (по N строк) |
| `seed_orders.py` | `orders` | `orders` + `order_items` (по одной позиции на заказ) |
| `seed_logistics.py` | `logistics` | `routes` + `route_points` + `route_assignments` |

**Identity не трогаем.**

## Установка

```bash
cd data_generator
pip install -r requirements.txt
```

## Подключение к Postgres

По умолчанию: `postgresql://gastro:gastro@localhost:5432/<имя_бд>`.

Переопределение (как в docker-compose):

```bash
set CATALOG_DATABASE_URL=postgresql://gastro:gastro@localhost:5432/catalog
set FINANCE_DATABASE_URL=postgresql://gastro:gastro@localhost:5432/finance
set WAREHOUSE_DATABASE_URL=postgresql://gastro:gastro@localhost:5432/warehouse
set ORDERS_DATABASE_URL=postgresql://gastro:gastro@localhost:5432/orders
set LOGISTICS_DATABASE_URL=postgresql://gastro:gastro@localhost:5432/logistics
```

URL с `postgresql+asyncpg://` из сервисов тоже подходят — в коде они приводятся к обычному `postgresql://`.

Если Postgres **не проброшен** на хост, смотри `docker-compose.local.yml` или выполняй скрипты из контейнера в сети `docker compose` (хост `postgres`, порт `5432`).

## Полный прогон (рекомендуется с `--truncate`)

Порядок важен: сначала каталог и финансы, затем склад, заказы, логистика.

```bash
python run_all.py --count 10000 --truncate
```

Отдельно:

```bash
python seed_catalog.py --count 10000 --truncate
python seed_finance.py --accounts 10000 --transactions 10000 --truncate
python seed_warehouse.py --count 10000 --max-product-id 10000 --truncate
python seed_orders.py --count 10000 --max-product-id 10000 --truncate
python seed_logistics.py --count 10000 --truncate
```

### Заметки

- **`--truncate`** очищает таблицы в целевой БД перед вставкой (CASCADE / порядок учтён). Без него возможны ошибки уникальности по `sku`, `idempotency_key` и т.д.
- **Finance**: транзакции ссылаются на `accounts.client_id` — сначала создаются счета `client_id = 1..N`.
- **Warehouse**: `product_id` случайный в `[1..max-product-id]` — согласуйте с числом товаров в каталоге.
- **Logistics**: `route_assignments.order_id` = **1..N** по порядку, уникальны. Имеет смысл после `seed_orders` с тем же `--count` и **truncate**, чтобы `orders.id` были `1..N`.

## Файлы

- `common.py` — нормализация DSN.
- `run_all.py` — запуск всех скриптов по цепочке.
