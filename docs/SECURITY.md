# Безопасность GastroRoute

Документ фиксирует известные риски (CVE/экосистема), находки по текущему коду и план мероприятий. Обновляйте при смене зависимостей или инфраструктуры.

---

## 1. Внешние уязвимости (FastAPI / стек)

| ID | Суть | Когда актуально | Устранение |
|----|------|-----------------|------------|
| **CVE-2025-68481** | CSRF / OAuth state в пакете **`fastapi-users`** (до 15.0.2) | Используется **`fastapi-users`** + OAuth | Обновить **`fastapi-users` ≥ 15.0.2** |
| **CVE-2025-46814** | Подмена IP через **`X-Forwarded-For`** в **`fastapi-guard`** (до 2.0.0) | Используется **`fastapi-guard`** | Обновить **`fastapi-guard` ≥ 2.0.0** |
| **CVE-2025-62727** | DoS по заголовку **`Range`** в **Starlette** `FileResponse` / `StaticFiles` (0.39.0–0.49.0) | Отдача файлов / статики через Starlette | Обновить **Starlette ≥ 0.49.1** (через обновление **FastAPI**) |
| Зависимости | Уязвимости в **uvicorn**, **pydantic** и т.д. | Всегда | **`pip audit`** / Dependabot, регулярные обновления |

В наших сервисах в `pyproject.toml` указан **`fastapi`**, без **`fastapi-users`** и **`fastapi-guard`** — CVE первых двух строк относятся к экосистеме «на будущее», если эти пакеты появятся.

---

## 2. Flutter / Dart

| ID | Суть | Меры |
|----|------|------|
| **CVE-2026-27704** | Path traversal при распаковке пакетов в **`dart pub`** (старые SDK) | Во фронте задано **`sdk: ^3.11.1`** — держать не ниже исправленной ветки; следить за **flutter-announce** |
| **CVE-2024-54461 / CVE-2024-54462** | Плагины **`file_selector`** / **`image_picker`** на Android | Не используются в текущем `pubspec.yaml`; при добавлении — обновлять плагины |

---

## 3. Находки по текущему коду и инфраструктуре

| Область | Риск | Рекомендация |
|---------|------|--------------|
| JWT в **SharedPreferences** | Токены не в защищённом хранилище на мобильных | Прод: **`flutter_secure_storage`** для refresh (и при необходимости access) |
| **CORS** | Было `allow_origins=["*"]` с `allow_credentials=True` (некорректная пара для браузеров) | **Реализовано:** список origin из **`CORS_ORIGINS`**, см. §4 |
| **Traefik** | `--api.insecure=true`, порт **8080** | Прод: выключить insecure API, не публиковать дашборд наружу |
| **HTTP** | В compose нет TLS | Прод: HTTPS (Traefik + сертификаты) |
| **Секреты** | Пароль БД в `docker-compose.yml` | Прод: **secrets** / `.env` вне репозитория |
| **Dio** | Логи тел запросов | Только в **`kDebugMode`** — ок для релиза |
| **JWT_SECRET** (identity) | Дефолт в коде для dev | Прод: задать **`JWT_SECRET`** в окружении (длинная случайная строка) |

---

## 4. Реализовано в коде: CORS

Переменная окружения **`CORS_ORIGINS`**:

- **`CORS_ORIGINS=*`** (по умолчанию, если переменная не задана) — разрешён любой origin, **`allow_credentials=False`** (корректно для `*`).
- Список через запятую, например:  
  `CORS_ORIGINS=http://localhost,http://127.0.0.1`  
  — тогда **`allow_credentials=True`**, браузер может слать cookies/Authorization в сценариях с credentials.

В **`docker-compose.yml`** для сервисов API заданы origin’ы для локального UI за Traefik (`http://localhost`, `http://127.0.0.1`). Для продакшена подставьте свой домен.

---

## 5. План дальнейших мер (приоритеты)

### P0

- Регулярно: **`pip audit`** / обновления **FastAPI** и транзитивных пакетов.
- Прод: **HTTPS**, ограничение **Traefik dashboard**, секреты вне git.

### P1

- Мобильный клиент: **secure storage** для токенов.
- Зафиксировать в CI версию **Dart/Flutter** (`sdk` в `pubspec.yaml`).

### P2

- Сканирование образов (**Trivy** и т.п.), пентест API на стенде.
- При добавлении **fastapi-users** / OAuth — следить за advisory (в т.ч. CVE-2025-68481).

---

## 6. Ссылки

- [Flutter Security](https://github.com/flutter/flutter/security)
- [NVD](https://nvd.nist.gov/) — поиск по CVE
- Сообщения об уязвимостях Flutter: [g.co/vulnz](https://g.co/vulnz)

---

*Последнее обновление: зафиксировано вместе с внедрением `CORS_ORIGINS`.*
