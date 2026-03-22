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
| JWT в **SharedPreferences** (web) | На Web токены в prefs — риск при XSS | Минимизация скриптов, CSP; для максимальной защиты web — отдельная схема (httpOnly cookie + BFF) |
| JWT на **iOS/Android** | — | **Сделано:** **`flutter_secure_storage`** (Keychain / EncryptedSharedPreferences), миграция со старых prefs |
| **CORS** | Было `allow_origins=["*"]` с `allow_credentials=True` (некорректная пара для браузеров) | **Реализовано:** список origin из **`CORS_ORIGINS`**, см. §4 |
| **Traefik** | `--api.insecure=true`, дашборд на **8080** | **Dev:** порт **8080** слушает только **127.0.0.1**; прод: выключить insecure API, не публиковать дашборд наружу |
| **HTTP** | В compose нет TLS | Прод: HTTPS (Traefik + сертификаты) |
| **Секреты** | Учётные данные БД в compose | **Сделано:** **`POSTGRES_USER` / `POSTGRES_PASSWORD`** и **`JWT_SECRET`** задаются через **`.env`** (шаблон **`.env.example`**); прод: Docker secrets / vault |
| **Dio** | Логи тел запросов | Только в **`kDebugMode`** — ок для релиза |
| **JWT_SECRET** (identity) | Дефолт в коде, если переменная не задана | **Dev:** **`JWT_SECRET`** в **`.env`** / compose; прод: длинная случайная строка в secrets |

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

- Регулярно: **`pip audit`** / обновления **FastAPI** и транзитивных пакетов (**в CI:** `python -m pip_audit` по каждому Python-сервису).
- Прод: **HTTPS**, отключение insecure API Traefik, секреты не в git.

### P1

- **Сделано в CI:** **Flutter** `analyze` + `test`, канал **stable**; проверка **`docker compose config`**.
- Держать **`sdk`** в `pubspec.yaml` в актуальном диапазоне относительно образа в CI.
- Web: при необходимости усилить хранение сессии (см. таблицу выше).

### P2

- Сканирование образов (**Trivy** и т.п.), пентест API на стенде.
- При добавлении **fastapi-users** / OAuth — следить за advisory (в т.ч. CVE-2025-68481).

---

## 6. Ссылки

- [Flutter Security](https://github.com/flutter/flutter/security)
- [NVD](https://nvd.nist.gov/) — поиск по CVE
- Сообщения об уязвимостях Flutter: [g.co/vulnz](https://g.co/vulnz)

---

*Последнее обновление: CORS, Traefik dashboard на localhost, `.env.example`, CI (Flutter + pip-audit + compose).*
