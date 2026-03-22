# API integration tests (`tests_api`)

Интеграционные тесты против **уже поднятого** стека (Traefik + сервисы). Без моков — реальные HTTP-запросы.

## Требования

- Запущен `docker compose` (или аналог) с маршрутизацией как в `docker/traefik/dynamic.yml`: префиксы `/catalog`, `/finance`, `/identity`, `/warehouse`, `/logistics`, `/orders`.
- Python 3.11+ (рекомендуется).

## Установка

Из корня репозитория:

```bash
pip install -r tests_api/requirements.txt
```

## Запуск

```bash
# по умолчанию http://localhost
pytest tests_api -v

# другой хост/порт
set API_BASE_URL=http://192.168.1.10:8080
pytest tests_api -v
```

Переменные:

| Переменная | Описание |
|------------|----------|
| `API_BASE_URL` | Базовый URL Traefik без завершающего `/` (по умолчанию `http://localhost`) |
| `API_HTTP_TIMEOUT` | Таймаут HTTP-клиента в секундах (по умолчанию `30`) |

## Что покрыто

- **Все сервисы**: `GET /api/v1/health` и `GET /api/v1/ready` (через префикс сервиса).
- **Warehouse / Logistics / Orders**: `GET .../api/v1/<service>/ping`.
- **Catalog**: список, автодополнение, полный CRUD продукта.
- **Identity**: регистрация → логин → `/users/me` → refresh → logout → второй пользователь → logout-all; негативный логин.
- **Finance**: список транзакций, баланс (200 или 404), структура баланса при 200, выручка по периоду, генерация счёта, создание транзакции и идемпотентность (если в БД есть аккаунт для `client_id=1`).
- **Orders**: список заказов; создание заказа с каталогом и identity (имя клиента и позиции); неизвестный товар → 400.
- **Warehouse**: оприходование партии (`POST .../receive`) — имя товара в остатках совпадает с каталогом.

### Finance: транзакции

Создание транзакции зависит от FK на таблицу `accounts`. Если для `client_id=1` нет строки в `accounts`, тесты создания **пропускаются** (`skipped`). Чтобы они выполнялись, добавьте аккаунт в БД `finance` для `client_id=1` или измените логику сидов.

### Finance: счёт (`POST /invoices/generate`)

Генерация ходит в **orders** за деталями заказов и требует строку в `finance.accounts` для выбранного `client_id`. Тест берёт первый заказ из списка заказов и счёт для его `client_id`; если заказов нет или аккаунта нет — **skip**. Нужен `ORDERS_BASE_URL` у сервиса `finance` (в `docker-compose` задано).

## Структура

- `conftest.py` — `API_BASE_URL`, `httpx.Client`, определение наличия finance-аккаунта.
- `test_health_ready.py`, `test_ping_services.py` — смоук по всем сервисам.
- `test_catalog.py`, `test_identity.py`, `test_finance.py`, `test_orders.py`, `test_warehouse.py` — сценарии по доменам.
