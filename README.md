# GastroRoute (infra)

## Быстрый старт

1. **Клон** репозитория с сабмодулями:
   ```bash
   git clone --recurse-submodules <url>
   ```
   Если уже склонировали без сабмодулей: `make clone`.

2. **Переменные окружения:** скопируйте `.env.example` в `.env` в корне и при необходимости поправьте значения.

3. **Запуск:** `make up` (или `docker compose -f docker-compose.yml up`).

Нужны **Docker** (с плагином Compose) и **Git**. Для `make` — GNU Make (на Windows обычно из Git Bash).
