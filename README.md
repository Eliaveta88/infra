# GastroRoute (infra)

## Быстрый старт

1. **Клон** репозитория с сабмодулями:
   ```bash
   git clone --recurse-submodules <url>
   ```
   Если уже склонировали без сабмодулей: `make clone`.

2. **Переменные окружения:** скопируйте `.env.example` в `.env` в корне и при необходимости поправьте значения.

3. **Запуск:** `make up` (или `docker compose -f docker-compose.yml up`).

При первом старте сервис **identity** создаёт начального админа из **`ADMIN_USERNAME`** / **`ADMIN_PASSWORD`** / **`ADMIN_EMAIL`** (дефолт — `admin` / `admin` / `admin@local.dev`). Гостевого режима нет: фронт всегда требует логин.

Если после обновления логин падает из‑за невалидного email в БД (например `admin@local`): `UPDATE users SET email = 'admin@local.dev' WHERE username = 'admin';` в базе **identity** (или пересоздайте том Postgres).

Дашборд Traefik (`:8080`) и прямые порты сервисов на хост: второй файл **`docker-compose.local.yml`** — см. комментарий внутри него.

Нужны **Docker** (с плагином Compose) и **Git**. Для `make` — GNU Make (на Windows обычно из Git Bash).

## Генератор данных (Postgres)

Один прогон всех сидов (каталог → финансы → склад → заказы → логистика):

- `bash scripts/run_data_generator.sh --count 10000 --truncate`  
- или `make data-generator ARGS="--count 10000 --truncate"` (нужен bash)

Подробности: [data_generator/README.md](data_generator/README.md).

## Интеграционные API-тесты

Скрипт поднимает compose, ждёт health и запускает `pytest tests_api`:

- `make integration-tests` (через `scripts/run_integration_tests.sh`, нужен bash)
- или вручную: см. [docs/INTEGRATION_TESTS.md](docs/INTEGRATION_TESTS.md)
