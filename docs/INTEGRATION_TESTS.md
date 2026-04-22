# Интеграционные API-тесты (`tests_api`)

Тесты ходят в **живой** стек через Traefik (как и клиенты): переменная **`API_BASE_URL`** (по умолчанию `http://localhost`).

## Локально

1. Поднять сервисы: `make up` или `docker compose -f docker-compose.yml up -d --build`.
2. Дождаться готовности (health сервисов).
3. Установить зависимости и запустить pytest:

   ```bash
   pip install -r tests_api/requirements.txt
   API_BASE_URL=http://localhost pytest tests_api -v
   ```

## Один скрипт (compose + ожидание + pytest)

- **Linux / macOS / Git Bash:**  
  `bash scripts/run_integration_tests.sh`  
  Доп. аргументы передаются в pytest, например:  
  `bash scripts/run_integration_tests.sh -k test_list_routes`

- **Windows (PowerShell):**  
  `powershell -ExecutionPolicy Bypass -File scripts/run_integration_tests.ps1`

Переменные окружения:

| Переменная | Назначение |
|------------|------------|
| `COMPOSE_FILE` | Файл compose (по умолчанию `docker-compose.yml`) |
| `API_BASE_URL` | База для httpx (по умолчанию `http://localhost`) |
| `MAX_WAIT_SEC` / `$env:MAX_WAIT_SEC` | Таймаут ожидания health (по умолчанию 120) |

## Flutter (unit / widget)

Из каталога `frontend/`:

```bash
flutter pub get
flutter test
```

Docker для этого не нужен: HTTP мокируется подменой `dioProvider` / перехватчиков, а сохранение токенов в тестах auth — через `PrefsOnlyAuthPersistence` и `SharedPreferences.setMockInitialValues`.
