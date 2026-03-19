# GastroRoute Frontend Base Spec (Flutter Web, Material 3)

## 1) Scope and product goal

Frontend is a single-page B2B web application for operational work with the GastroRoute ecosystem.
The UI mirrors backend microservice domains and gives one consistent workspace for managers, operators, and dispatchers.

Core domain sections:

- Identity: auth, sessions, access rights, current user profile.
- Catalog: products, categories, units, product cards.
- Warehouse: stock, batches, FEFO reserve/release/receive operations.
- Finance: balances, transactions, invoices.
- Logistics: routes, vehicles, route points, delivery statuses.
- Orders: order lifecycle, composition, statuses, linkage to stock and route flows.

## 2) Tech stack and architectural constraints

- Platform: Flutter Web only.
- UI framework: Material 3 only (`useMaterial3: true`).
- State management: Riverpod.
- Routing: GoRouter with deep links.
- Network layer: Dio with interceptors:
  - access token attach,
  - transparent refresh flow on 401,
  - retry for idempotent requests,
  - uniform error mapping.
- Architecture: feature-first + clean layering per feature:
  - `presentation` (widgets/pages/controllers),
  - `application` (use cases),
  - `domain` (entities/contracts),
  - `data` (dto, repositories, api).

## 3) Folder structure (target)

```text
lib/
  core/
    design_system/
    theme/
    routing/
    network/
    auth/
    widgets/
  features/
    identity/
    catalog/
    warehouse/
    finance/
    logistics/
    orders/
```

Each feature contains:

- `pages/` (route entry screens),
- `widgets/` (feature UI),
- `state/` (riverpod providers/notifiers),
- `domain/`,
- `data/`.

## 4) Theming requirements (mandatory)

The application must support exactly two full themes:

- Light theme.
- Dark theme.

Both themes must be built via Material 3 `ColorScheme` and shared semantic design tokens:

- Brand, success, warning, error, info.
- Surface layers (`surface`, `surfaceContainer*`).
- Stroke/border tokens.
- Typography scale.
- Elevation and radius scale.

Rules:

- No hardcoded colors inside feature widgets.
- Theme switch is global and reactive.
- Persist selected theme in local storage.
- Contrast must stay readable in both themes.

## 5) Visual style and motion requirements

### 5.1 Base background

App background should be a subtle animated layer of flying box emojis (for logistics/warehouse tone).

Requirements:

- Use canvas/custom painter or lightweight positioned animation layer.
- Emojis: box-oriented (`📦`, optionally `🧾`, `🚚` accent).
- Low opacity and low speed, no distraction for data tables.
- Density adapts to screen width.
- Animation can be reduced/disabled in low-performance mode.

### 5.2 Modal windows

All modal windows must look premium and consistent with Material 3.

Mandatory visual rule for modals:

- Everything behind modal uses a bokeh-style blur/background effect.

Implementation notes:

- Use `BackdropFilter` + gradient/noise overlay.
- Keep strong focus ring on modal container.
- Modal elevation and shadow differ for light/dark themes.
- Support ESC close, outside click close (when allowed), and focus trap.

## 6) Navigation and shell layout

- App shell: top app bar + left navigation rail/drawer + content area.
- Adaptive breakpoints:
  - desktop wide,
  - desktop compact,
  - tablet web.
- Deep links for feature pages and detail pages.
- Breadcrumbs on deep operational screens.

Primary navigation nodes:

- Dashboard
- Orders
- Catalog
- Warehouse
- Finance
- Logistics
- Identity/Admin

## 7) Feature requirements by backend domain

### Identity

- Login page with refresh-aware session handling.
- Current user profile (`/users/me` semantics).
- Role/permission-aware guards for routes and actions.
- Session logout flow.

### Catalog

- Product list with pagination, filters, and search.
- Product details page.
- Unit conversion editor for product units.

### Warehouse

- Stock overview (aggregated hot balances).
- Reserve/release operations.
- Receive batch operation with expiry-focused UX.

### Finance

- Client account balance and credit limit view.
- Transaction creation form (idempotency key support from client).
- Invoice generation action with status feedback.

### Logistics

- Route planning form.
- Assignment flow with capacity validation hints.
- Route point status update workflow.

### Orders

- Order list and details.
- Order status pipeline (draft -> confirmed -> in delivery -> closed/cancelled).
- Integration points to reserve stock and bind delivery route.

## 8) Shared UX requirements

- Data grids: sorting, sticky header, empty/loading/error states.
- Global search with debounced requests.
- Toast/inline feedback patterns unified across all features.
- Confirm dialogs for destructive actions.
- Optimistic UI only for safe operations; otherwise explicit pending states.

## 9) Performance and quality requirements

- Initial page load target: fast perceived rendering on modern desktop browsers.
- Avoid heavy animation on low-end devices (feature flag / reduced motion mode).
- Skeleton placeholders for key screens.
- Strict linting and formatting policy.
- Basic widget/integration tests for core flows:
  - auth login/refresh,
  - product list open,
  - stock reserve form,
  - transaction submit,
  - route status update.

## 10) Accessibility and interaction

- Keyboard navigation support in tables/forms/modals.
- Visible focus indicators in both themes.
- Minimum contrast compliance for text and controls.
- Semantic labels for icon-only actions.

## 11) Acceptance checklist (MVP)

- Material 3 enabled globally.
- Light and dark themes fully implemented and switchable.
- Modal bokeh effect is present and consistent.
- Animated emoji-box background is implemented and non-intrusive.
- Feature sections map to all backend domains.
- Route guards and auth refresh are operational.
- Core screens for each feature are reachable from navigation.

## 12) API Contract (Backend Endpoints Required)

### Base URL
All requests to: `http://localhost:8000/api/v1`

### Identity Service (`/api/v1/identity`)

| Method | Endpoint | Purpose | Request | Response |
|--------|----------|---------|---------|----------|
| POST | `/login` | User authentication | `{username, password}` | `{access_token, refresh_token, user}` |
| GET | `/users/me` | Current user profile | - | `{id, username, email, roles}` |
| POST | `/logout` | Logout and revoke token | - | `{status: "ok"}` |

### Catalog Service (`/api/v1/catalog`)

| Method | Endpoint | Purpose | Query Params | Response |
|--------|----------|---------|--------------|----------|
| GET | `/products` | List all products | `skip=0&limit=50&sort=asc` | `[{id, name, category, price, in_stock}]` |
| GET | `/products/{id}` | Product details | - | `{id, name, category, price, description, attributes}` |
| POST | `/products` | Create product | - | `{id, name, ...}` |
| PATCH | `/products/{id}` | Update product | - | `{id, name, ...}` |

### Warehouse Service (`/api/v1/warehouse`)

| Method | Endpoint | Purpose | Body | Response |
|--------|----------|---------|------|----------|
| GET | `/stock` | Hot stock overview | - | `[{product_id, available, reserved, expiry_date, cell}]` |
| POST | `/stock/reserve` | Reserve batch | `{product_id, quantity, order_id}` | `{reservation_id, reserved_qty, status}` |
| POST | `/stock/release` | Release reservation | `{reservation_id}` | `{status: "ok"}` |
| POST | `/stock/receive` | Receive batch | `{product_id, quantity, expiry_date, cell}` | `{batch_id, status}` |

### Finance Service (`/api/v1/finance`)

| Method | Endpoint | Purpose | Params/Body | Response |
|--------|----------|---------|-------------|----------|
| GET | `/accounts/{client_id}/balance` | Account balance | - | `{client_id, balance, credit_limit, currency}` |
| GET | `/transactions` | Transaction history | `client_id, skip, limit` | `[{id, client_id, amount, type, date, status}]` |
| POST | `/transactions` | Create transaction | `{client_id, amount, description, idempotency_key}` | `{id, status, created_at}` |
| POST | `/invoices/generate` | Generate invoice | `{client_id, order_ids}` | `{invoice_id, pdf_url, status}` |

### Logistics Service (`/api/v1/logistics`)

| Method | Endpoint | Purpose | Body | Response |
|--------|----------|---------|------|----------|
| GET | `/routes` | List active routes | `skip, limit` | `[{id, vehicle, driver, status, points_count}]` |
| POST | `/routes/plan` | Create route | `{vehicle_id, start_time, points}` | `{route_id, status}` |
| PUT | `/routes/{id}/assign` | Assign order to route | `{order_id, point_index}` | `{route_id, point_id, status}` |
| PATCH | `/routes/points/{id}/status` | Update delivery status | `{status, notes}` | `{point_id, status}` |

### Orders Service (`/api/v1/orders`)

| Method | Endpoint | Purpose | Query/Body | Response |
|--------|----------|---------|-----------|----------|
| GET | `/` | List orders | `skip=0&limit=50&status=` | `[{id, client, amount, status, date}]` |
| GET | `/{id}` | Order details | - | `{id, client_id, items, total, status, delivery_info}` |
| POST | `/` | Create order | `{client_id, items[{product_id, qty}], delivery_date}` | `{order_id, status}` |
| PATCH | `/{id}/status` | Update status | `{status}` | `{order_id, status}` |

### Health Checks (Common to all services)

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/health` | Liveness probe |
| `GET /api/v1/ready` | Readiness probe |
