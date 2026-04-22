# GastroRoute API Contract v1.0

Base URL (через Traefik): `http://localhost/{service}/api/v1/{service}` — префикс сервиса дублируется, потому что сначала Traefik маршрутизирует по `/{service}/*`, а затем FastAPI-роутер внутри сервиса имеет prefix `/{service}`. Примеры:

- `GET http://localhost/orders/api/v1/orders` — список заказов;
- `POST http://localhost/warehouse/api/v1/warehouse/stock/reserve` — резерв;
- `GET http://localhost/finance/api/v1/finance/accounts/{id}/balance` — баланс.

Все тела — JSON, временные метки — ISO 8601.

## Architecture Pattern

All backend services follow a modular layered architecture (reference: `ai_chat_bot` template):

```
HTTP Request
    ↓
endpoints.py (HTTP declarations only)
    ├── @router.get/post/patch/delete()
    ├── response_model: Pydantic Schema
    ├── summary, description
    └── Depends(get_dal)
    ↓
actions.py (Business logic)
    ├── Validates input
    ├── Calls DAL methods
    ├── Transforms DAL results to Schemas
    └── Returns Pydantic Response
    ↓
dal.py (Database Access Layer)
    ├── Database queries
    ├── Returns raw dicts/ORM objects
    └── No HTTP knowledge
    ↓
PostgreSQL Database
```

### Per-Service Module Structure

```
src/routers/v1/{service}/
├── __init__.py           # Router export
├── endpoints.py          # HTTP routes (request/response/validation)
├── actions.py            # Business logic functions
├── dal.py                # Database queries
├── schemas.py            # Pydantic models (Request, Response)
├── enums.py              # Service-specific enums (Status, Type, etc)
├── summary.py            # Endpoint summary strings
└── description.py        # Endpoint description strings
```

### Key Principles

1. **Separation of Concerns**: endpoints ↔ actions ↔ dal → no mixing
2. **Pydantic Only**: All HTTP responses are Pydantic models, never raw dicts
3. **Explicit Dependencies**: All injections via `Depends()`
4. **Error Handling**: HTTPException with proper status codes
5. **Documentation**: Every endpoint has summary + description strings
6. **Consistency**: All services follow identical pattern

## Identity Service (`/api/v1/identity`)

### POST /login
Authenticate user and return tokens.

**Request:**
```json
{
  "username": "string",
  "password": "string"
}
```

**Response (200):**
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "user": {
    "id": "int",
    "username": "string",
    "email": "string",
    "roles": ["string"]
  }
}
```

### GET /users/me
Get current authenticated user profile.

**Response (200):**
```json
{
  "id": "int",
  "username": "string",
  "email": "string",
  "roles": ["string"],
  "permissions": ["string"]
}
```

### GET /users/{user_id}
Public profile by numeric user id (orders client label, logistics driver name). No authentication required in the reference deployment.

**Response (200):** same shape as user object (no password).

**404** if the user does not exist or is inactive.

### POST /logout
Revoke current session.

**Response (200):**
```json
{
  "status": "ok"
}
```

---

## Catalog Service (`/api/v1/catalog`)

### GET /products
List all products with pagination and filtering.

**Query Parameters:**
- `skip`: int (default: 0)
- `limit`: int (default: 50, max: 100)
- `sort`: "asc" | "desc" (default: "asc")
- `category`: string (optional)

**Response (200):**
```json
[
  {
    "id": "int",
    "name": "string",
    "category": "string",
    "price": "float",
    "in_stock": "bool",
    "sku": "string"
  }
]
```

### GET /products/{id}
Get product details with attributes.

**Response (200):**
```json
{
  "id": "int",
  "name": "string",
  "category": "string",
  "price": "float",
  "description": "string",
  "sku": "string",
  "units": [
    {
      "id": "int",
      "name": "string",
      "conversion_factor": "float"
    }
  ],
  "attributes": {
    "protein": "float",
    "fat": "float",
    "carbs": "float",
    "gost": "string"
  }
}
```

### POST /products
Create new product. Admin only.

**Request:**
```json
{
  "name": "string",
  "category": "string",
  "price": "float",
  "description": "string",
  "sku": "string"
}
```

**Response (201):** Product object

---

## Warehouse Service (`/api/v1/warehouse`)

### GET /stock
List inventory with hot stock balances.

**Query Parameters:**
- `skip`: int
- `limit`: int

**Response (200):**
```json
[
  {
    "product_id": "int",
    "product_name": "string",
    "available": "int",
    "reserved": "int",
    "total": "int",
    "expiry_date": "ISO 8601",
    "cell_location": "string",
    "batch_id": "int"
  }
]
```

### POST /stock/reserve
Reserve stock for order (FEFO algorithm).

**Request:**
```json
{
  "product_id": "int",
  "quantity": "float",
  "order_id": "int",
  "unit_type": "string"
}
```

**Response (201):**
```json
{
  "reservation_id": "int",
  "product_id": "int",
  "reserved_qty": "float",
  "batch_id": "int",
  "expiry_date": "ISO 8601",
  "status": "active"
}
```

### POST /stock/release
Release previously made reservation.

**Request:**
```json
{
  "reservation_id": "int"
}
```

**Response (200):**
```json
{
  "status": "released"
}
```

### POST /receive
Receive new batch with expiry tracking. (Путь — именно `/receive`, без `/stock/` префикса, как в endpoints.py.)

**Request:**
```json
{
  "product_id": "int",
  "quantity": "float",
  "unit_type": "string",
  "expiry_date": "ISO 8601",
  "cell_location": "string",
  "batch_reference": "string"
}
```

**Response (201):**
```json
{
  "batch_id": "int",
  "product_id": "int",
  "quantity_received": "float",
  "status": "in_stock"
}
```

---

## Finance Service (`/api/v1/finance`)

### GET /accounts/{client_id}/balance
Get account balance and credit limits.

**Response (200):**
```json
{
  "client_id": "int",
  "balance": "float",
  "credit_limit": "float",
  "currency": "RUB",
  "status": "active"
}
```

### GET /accounts/{client_id}/revenue
Sum of **completed** transactions with **positive** `amount` in the half-open interval **`[from, to)`** (use the same UTC bounds as the dashboard for “today”, e.g. local midnight converted to UTC).

**Query parameters:**
- `from`: ISO 8601 datetime (inclusive)
- `to`: ISO 8601 datetime (exclusive)

**Response (200):**
```json
{
  "client_id": "int",
  "total_amount": "decimal",
  "currency": "RUB",
  "period_from": "ISO 8601",
  "period_to": "ISO 8601"
}
```

**Errors:** `422` if `from >= to`.

### GET /transactions
List transactions with pagination.

**Query Parameters:**
- `client_id`: int (required)
- `skip`: int
- `limit`: int

**Response (200):**
```json
[
  {
    "id": "int",
    "client_id": "int",
    "amount": "float",
    "type": "payment|invoice|refund",
    "description": "string",
    "date": "ISO 8601",
    "status": "completed|pending|failed"
  }
]
```

### POST /transactions
Create transaction with idempotency.

**Request:**
```json
{
  "client_id": "int",
  "amount": "float",
  "description": "string",
  "transaction_type": "payment",
  "idempotency_key": "string (UUID)"
}
```

**Response (201):**
```json
{
  "id": "int",
  "status": "completed",
  "created_at": "ISO 8601"
}
```

### POST /invoices/generate
Aggregate **orders** service data: loads each order by id via `GET /api/v1/orders/{id}`, checks `client_id` matches, sums `total_amount`, persists an **invoices** row. Requires a finance **account** for `client_id`.

**Side-effects on success:** создаётся запись в `transactions` (`transaction_type="invoice"`, `status="completed"`, `idempotency_key="invoice:{invoice_id}"`) и списывается сумма со `accounts.balance` клиента. Операция идемпотентна по `invoice_id`: повторный вызов на тот же уже созданный invoice не удвоит проводку.

**Request:**
```json
{
  "client_id": "int",
  "order_ids": ["int"]
}
```

**Response (201):**
```json
{
  "invoice_id": "int",
  "client_id": "int",
  "pdf_url": "string (API path to future PDF; see GET below)",
  "status": "generated",
  "created_at": "ISO 8601"
}
```

**Errors:** `404` if account missing; `400` if an order is missing or belongs to another client, or total is not positive; `503` if orders HTTP fails.

### GET /invoices/{invoice_id}/pdf
Reserved for PDF binary export. **501** until implemented.

---

## Logistics Service (`/api/v1/logistics`)

### GET /routes
List active routes.

**Query Parameters:**
- `skip`: int
- `limit`: int
- `status`: "planning|in_progress|completed"

**Response (200):**
```json
[
  {
    "id": "int",
    "vehicle_id": "int",
    "driver_name": "string",
    "status": "planning|in_progress|completed",
    "points_count": "int",
    "total_weight": "float",
    "total_volume": "float"
  }
]
```

### POST /
Create new route. (Путь — корень `""` в logistics-роутере, не `/routes/plan`.)

**Request:**
```json
{
  "vehicle_id": "int",
  "driver_id": "int",
  "start_time": "ISO 8601",
  "points": [
    {
      "client_id": "int",
      "address": "string",
      "sequence": "int"
    }
  ]
}
```

**Response (201):**
```json
{
  "route_id": "int",
  "status": "planning",
  "created_at": "ISO 8601"
}
```

### PUT /routes/{id}/assign
Assign order to route point.

**Request:**
```json
{
  "order_id": "int",
  "point_index": "int"
}
```

**Response (200):**
```json
{
  "route_id": "int",
  "point_id": "int",
  "order_id": "int",
  "status": "assigned"
}
```

### PATCH /routes/points/{id}/status
Update delivery point status.

**Request:**
```json
{
  "status": "pending|in_transit|delivered|failed",
  "notes": "string"
}
```

**Response (200):**
```json
{
  "point_id": "int",
  "status": "delivered",
  "updated_at": "ISO 8601"
}
```

---

## Orders Service (`/api/v1/orders`)

### GET /
List orders.

**Query Parameters:**
- `skip`: int
- `limit`: int
- `status`: "draft|confirmed|in_delivery|closed|cancelled"

**Response (200):**
```json
[
  {
    "id": "int",
    "client_name": "string",
    "total_amount": "float",
    "status": "string",
    "created_at": "ISO 8601"
  }
]
```

### GET /{id}
Get order details with items and delivery info.

**Response (200):**
```json
{
  "id": "int",
  "client_id": "int",
  "client_name": "string",
  "items": [
    {
      "product_id": "int",
      "product_name": "string",
      "quantity": "float",
      "unit_price": "float",
      "total": "float"
    }
  ],
  "total_amount": "float",
  "status": "string",
  "delivery_date": "ISO 8601",
  "route_id": "int",
  "created_at": "ISO 8601"
}
```

### POST /
Create new order.

**Request:**
```json
{
  "client_id": "int",
  "items": [
    {
      "product_id": "int",
      "quantity": "float"
    }
  ],
  "delivery_date": "ISO 8601",
  "notes": "string"
}
```

**Response (201):**
```json
{
  "id": "int",
  "status": "draft",
  "created_at": "ISO 8601"
}
```

### PATCH /{id}/status
Update order status in pipeline.

**Request:**
```json
{
  "status": "confirmed|in_delivery|closed|cancelled"
}
```

**Response (200):** полная карточка заказа (`OrderResponse`), включая `items` и `route_id`.

**Side-effects:**

- `status="confirmed"` (переход из не-confirmed) → orders вызывает `POST /warehouse/api/v1/warehouse/stock/reserve` по каждой позиции; при нехватке стока возвращает `409` и статус не меняется. Список полученных `reservation_id` сохраняется в Redis.
- `status="cancelled"` (переход из не-cancelled) → orders вызывает `POST /stock/release` для ранее сохранённых резервов (best-effort).

**Errors:** `404` если заказ не найден, `409` если не удалось зарезервировать сток при переходе в `confirmed`, `422` если статус неизвестен.

---

## Common Endpoints (All Services)

### GET /health
Liveness probe.

**Response (200):**
```json
{
  "status": "ok",
  "service": "service_name"
}
```

### GET /ready
Readiness probe.

**Response (200):**
```json
{
  "status": "ready",
  "service": "service_name"
}
```

---

## Error Responses

All error responses use HTTP status codes:

- `400 Bad Request`: Invalid input
- `401 Unauthorized`: Missing/invalid authentication
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `409 Conflict`: Idempotency key collision (finance)
- `500 Internal Server Error`: Server error

Error body:
```json
{
  "detail": "error message"
}
```
