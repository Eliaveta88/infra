# Безопасность GastroRoute

Документ фиксирует известные риски (CVE/экосистема), что уже сделано в коде и инфраструктуре, и что остаётся на стороне эксплуатации.

---

## Статус мер (кратко)

| Тема | Состояние |
|------|-----------|
| CORS (`CORS_ORIGINS`) | Реализовано во всех API |
| Traefik dashboard / API | Dev: порт **8080** на **127.0.0.1** через **`docker-compose.local.yml`**; в базовом compose порт не публикуется; прод: `docker-compose.prod.yml` отключает dashboard и insecure API |
| Заголовки ответа | Traefik: middleware **security-headers**; Flutter Web: заголовки в **nginx** |
| Секреты БД / JWT | Через **`.env`** (шаблон **`.env.example`**) |
| Redis | Пароль **`REDIS_PASSWORD`** (по умолчанию dev: `devredis`), одинаковый в redis и сервисах |
| Starlette CVE-2025-62727 (Range) | Явная зависимость **`starlette>=0.49.1`** во всех Python-сервисах |
| JWT на мобильных | **`flutter_secure_storage`** |
| JWT на Web | Ограничение платформы: prefs; усиление — httpOnly + BFF, план в [BFF_JWT_COOKIE_PLAN.md](BFF_JWT_COOKIE_PLAN.md) |
| TLS / HTTPS | Не в dev compose; на проде — reverse-proxy или Traefik ACME (см. ниже) |
| Сканирование образов / пентест | Рекомендуется на стенде или в пайплайне деплоя (Trivy и т.п.) |

---

## 1. Внешние уязвимости (FastAPI / стек)

| ID | Суть | Когда актуально | Устранение |
|----|------|-----------------|------------|
| **CVE-2025-68481** | CSRF / OAuth state в **`fastapi-users`** (до 15.0.2) | Используется **`fastapi-users`** + OAuth | Обновить **`fastapi-users` ≥ 15.0.2** |
| **CVE-2025-46814** | Подмена IP через **`X-Forwarded-For`** в **`fastapi-guard`** (до 2.0.0) | Используется **`fastapi-guard`** | Обновить **`fastapi-guard` ≥ 2.0.0** |
| **CVE-2025-62727** | DoS по **`Range`** в **Starlette** `FileResponse` / `StaticFiles` (0.39.0–0.49.0) | Отдача файлов / статики через Starlette | **Сделано:** **`starlette>=0.49.1`** в `pyproject.toml` всех сервисов |
| Зависимости | Уязвимости в **uvicorn**, **pydantic** и т.д. | Всегда | Регулярно **`pip audit`** / обновления |

В сервисах нет **`fastapi-users`** и **`fastapi-guard`** — первые две строки на будущее, если пакеты появятся.

---

## 2. Flutter / Dart

| ID | Суть | Меры |
|----|------|------|
| **CVE-2026-27704** | Path traversal в **`dart pub`** (старые SDK) | **`sdk: ^3.11.1`** в `pubspec.yaml`; следить за **flutter-announce** |
| **CVE-2024-54461 / CVE-2024-54462** | Плагины **`file_selector`** / **`image_picker`** на Android | Не используются; при добавлении — актуальные версии плагинов |

---

## 3. Инфраструктура и код (детали)

| Область | Риск | Меры |
|---------|------|------|
| JWT в **SharedPreferences** (web) | Риск при XSS | Минимизация скриптов; целевая защита — httpOnly cookie + BFF (см. [BFF_JWT_COOKIE_PLAN.md](BFF_JWT_COOKIE_PLAN.md)) |
| **Traefik** | Insecure API | Dev: **8080** на **127.0.0.1** через **`docker-compose.local.yml`**; прод: **`docker-compose.prod.yml`** (без dashboard / insecure API) |
| **HTTP** | Нет TLS в dev | Прод: терминация TLS перед Traefik или Traefik + ACME Let’s Encrypt |
| **Секреты** | Утечки в git | **`.env`** + **`.env.example`**; в проде — Docker secrets / vault |
| **Redis** | Доступ без пароля | **`REDIS_PASSWORD`** в compose и во всех сервисах |
| **Dio** (фронт) | Логи тел запросов | Только в **`kDebugMode`** |

---

## 4. CORS

Переменная **`CORS_ORIGINS`**:

- **`CORS_ORIGINS=*`** (если не задана) — любой origin, **`allow_credentials=False`**.
- Список через запятую — **`allow_credentials=True`**, например для локального UI:  
  `http://localhost`, `http://127.0.0.1`.

В продакшене задайте реальные домены фронта в **`CORS_ORIGINS`** для каждого API-сервиса.

---

## 5. Продакшен: HTTPS

В репозитории **нет** включённого TLS для dev (по умолчанию HTTP на порту 80). Типичные варианты:

1. **Внешний балансировщик / CDN** (TLS на периметре), до Traefik — HTTP внутри сети.
2. **Traefik + Let’s Encrypt**: entrypoint **websecure** `:443`, resolver **acme**, правила с **`Host(\`ваш-домен\`)`**, редирект HTTP→HTTPS. Сертификаты и домен настраиваются под конкретный хост (не автоматизировано в этом репозитории).

После включения HTTPS имеет смысл добавить **HSTS** (например, в middleware Traefik для **websecure**).

---

## 6. Что остаётся процессом эксплуатации

- Регулярный **`pip audit`** и обновления зависимостей в репозиториях API/фронта.
- Сканирование образов (**Trivy** и аналоги), пентест API на стенде.
- Политика секретов и резервного копирования БД.

---

## 7. Ссылки

- [Flutter Security](https://github.com/flutter/flutter/security)
- [NVD](https://nvd.nist.gov/)
- [g.co/vulnz](https://g.co/vulnz)

---

*Последнее обновление: Redis auth, Traefik/nginx security headers, `starlette>=0.49.1`, `docker-compose.prod.yml`.*
