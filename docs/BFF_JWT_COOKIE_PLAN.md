# BFF + httpOnly Cookie Plan (Web JWT hardening)

Статус: **design** — задача зафиксирована в [docs/SECURITY.md](SECURITY.md) (секция 3, строка «JWT в SharedPreferences (web)»). Ниже — согласованный план перехода.

## Цель

Убрать хранение JWT в браузере (`localStorage` / `SharedPreferences`) и перейти на схему **BFF (Backend-for-Frontend) + httpOnly Secure cookie**. Это устраняет XSS-кражу токенов и минимизирует поверхность атаки.

## Текущая модель

- Фронт (Flutter Web, nginx) -> напрямую через Traefik в `identity`, `orders`, `catalog`, `warehouse`, `finance`, `logistics`.
- Access/refresh JWT хранятся в `SharedPreferences` (см. [frontend/lib/core/auth/auth_token_storage.dart](../frontend/lib/core/auth/auth_token_storage.dart)).
- Dio подставляет `Authorization: Bearer ...` (см. `core/network/api_client.dart`).

## Целевая модель

```
[ Browser ] --(httpOnly cookie)--> [ BFF ] --(Bearer JWT внутренний)--> [ identity / orders / ... ]
```

- Новый сервис `bff` (FastAPI или Go), публикуется за Traefik под тем же хостом, что и фронт.
- Эндпоинты BFF: `/bff/login`, `/bff/logout`, `/bff/refresh`, `/bff/me`, + прокси для доменных API (`/api/v1/**`).
- BFF держит пару `access`/`refresh` в памяти/Redis на сессию, ставит клиенту **Set-Cookie**:
  - `grauth=<opaque-session-id>; HttpOnly; Secure; SameSite=Strict; Path=/`.
- Клиент (Flutter) не видит JWT. Для CSRF — либо `SameSite=Strict` + обязательный `Origin/Referer` check, либо double-submit token (`grauth_csrf`).

## Поэтапная миграция

1. **BFF скелет.** Добавить сервис `bff/` (FastAPI, httpx к identity), reverse-proxy для доменных API. Traefik route: `PathPrefix(/bff)` и `/api/v1` -> bff.
2. **Session store.** Redis: `bff:sess:{sid}` -> `{access, refresh, user_id, exp}`. TTL = refresh TTL.
3. **Эндпоинты.**
   - `POST /bff/login` — принимает `username/password`, зовёт `identity /login`, создаёт сессию, ставит `Set-Cookie`.
   - `POST /bff/logout` — чистит cookie + session в redis.
   - `POST /bff/refresh` — автоматически BFF делает refresh перед upstream.
   - `GET /bff/me` — из `identity /users/me`.
4. **Прокси.** `ANY /api/v1/{service}/**` -> прокси в соответствующий сервис, BFF подставляет `Authorization: Bearer <access>` из сессии.
5. **Frontend.**
   - Удалить `AuthTokenStorage`, `authenticatedDio`, `Authorization` header.
   - Dio с `withCredentials: true` на web (`BrowserHttpClientAdapter.withCredentials = true`).
   - `apiBaseUrlProvider` -> `/api/v1` (тот же origin).
   - `authProvider.login` -> `POST /bff/login` (cookie), `authProvider.logout` -> `POST /bff/logout`.
6. **CSRF.** Для небезопасных методов (`POST/PUT/PATCH/DELETE`) включить double-submit: BFF выдаёт `grauth_csrf` cookie (не HttpOnly) + требует заголовок `X-CSRF-Token` с тем же значением. Dio перехватчик добавляет заголовок на web.
7. **CORS.** После миграции frontend и BFF живут на одном origin → CORS не нужен для клиентских запросов. Идентити/оркестрации остаются внутри сети.
8. **Удаление web-ветки в `auth_token_storage.dart`.** Остаётся только native vault (secure storage) — либо модуль целиком удаляется, если web — единственный таргет.

## Что уже сделано (на момент этого плана)

- Native JWT хранится в `flutter_secure_storage` (Keychain/EncryptedSharedPreferences).
- Web — `SharedPreferences` (ограничение платформы, без BFF).
- RBAC-guard на `/admin` во фронте (go_router redirect), UI скрывает пункт меню «Админ» без роли `admin`.

## Риски и следствия

- Дополнительный сервис = +1 узел отказа и +1 слой латентности (~1–3 мс при локальном деплое).
- Рефреш и logout теперь серверные → BFF должен уметь инвалидировать сессию.
- Добавится Redis-зависимость для BFF (у нас уже есть Redis на infra).
- Нужно покрыть интеграционными тестами login → защищённый вызов → logout.

## Ссылки

- [docs/SECURITY.md](SECURITY.md) — общие меры и упоминание httpOnly cookie + BFF.
- [docs/base_tech.md](base_tech.md) — архитектура сервисов.
