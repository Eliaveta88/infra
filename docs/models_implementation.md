# ORM Models and DAL Implementation

All 6 backend services now have complete SQLAlchemy ORM models and fully functional Data Access Layer implementations.

## Overview

Each service has a `models.py` file containing SQLAlchemy ORM models, and the `dal.py` layer uses these models to implement database operations.

**Pattern**:
```
endpoints.py → actions.py → dal.py (uses models) → Database
```

---

## Service Models Summary

### 1. GastroRoute_catalog

**File**: `src/routers/v1/catalog/models.py`

#### Product Model
```python
class Product(Base):
    id: int (PK)
    name: str (indexed)
    category: str (indexed)
    price: float
    sku: str (unique, indexed)
    in_stock: bool
    is_deleted: bool (soft delete)
    created_at: datetime
    updated_at: datetime
```

**DAL Methods**:
- `create(product_in)` → Insert new product
- `get_by_id(product_id)` → Query (exclude soft deleted)
- `get_all(skip, limit)` → Paginated list
- `count()` → Total count
- `update(product_id, updates)` → Update fields
- `delete(product_id)` → Soft delete

---

### 2. GastroRoute_finance

**File**: `src/routers/v1/finance/models.py`

#### Transaction Model
```python
class Transaction(Base):
    id: int (PK)
    client_id: int (indexed)
    amount: DECIMAL(15,2)
    description: str
    transaction_type: str (indexed) # payment, invoice, refund
    status: str (indexed) # pending, completed, failed, cancelled
    idempotency_key: str (unique, indexed)
    created_at: datetime (indexed)
    updated_at: datetime
```

#### Account Model
```python
class Account(Base):
    id: int (PK)
    client_id: int (unique, indexed)
    balance: DECIMAL(15,2)
    credit_limit: DECIMAL(15,2)
    status: str (indexed) # active, suspended, closed
    created_at: datetime
    updated_at: datetime
```

**DAL Methods**:
- `create(tx_in)` → Insert with idempotency key
- `get_by_id(tx_id)` → Query transaction
- `get_by_idempotency_key(key)` → Deduplication
- `get_client_balance(client_id)` → Account balance
- `list_client_transactions(client_id, skip, limit)` → History
- `count_client_transactions(client_id)` → Count

---

### 3. GastroRoute_identity

**File**: `src/routers/v1/identity/models.py`

#### User Model
```python
class User(Base):
    id: int (PK)
    username: str (unique, indexed)
    email: str (unique, indexed)
    password_hash: str
    is_active: bool (indexed)
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
```

#### Role Model
```python
class Role(Base):
    id: int (PK)
    user_id: int (indexed)
    role_name: str (indexed) # admin, manager, operator, viewer
    created_at: datetime
```

#### Session Model
```python
class Session(Base):
    id: int (PK)
    user_id: int (indexed)
    token: str (unique, indexed)
    refresh_token: str (unique, indexed)
    ip_address: str
    user_agent: str
    is_active: bool (indexed)
    expires_at: datetime (indexed)
    created_at: datetime
```

**DAL Methods**:
- `create(user_in)` → Hash password, insert user
- `get_by_username(username)` → Query active user
- `get_by_email(email)` → Query by email
- `get_by_id(user_id)` → Query by ID
- `hash_password(password)` → Password hashing
- `verify_password(plain, hashed)` → Verification

---

### 4. GastroRoute_warehouse

**File**: `src/routers/v1/warehouse/models.py`

#### Stock Model
```python
class Stock(Base):
    id: int (PK)
    batch_id: int (indexed)
    product_id: int (indexed)
    product_name: str
    quantity_available: float
    quantity_reserved: float
    unit_type: str # unit, kg, liter, piece
    cell_location: str (indexed)
    expiry_date: datetime (indexed) ← FEFO ordering!
    batch_reference: str (indexed)
    created_at: datetime
    updated_at: datetime
```

#### Batch Model
```python
class Batch(Base):
    id: int (PK)
    product_id: int (indexed)
    quantity_received: float
    unit_type: str
    expiry_date: datetime (indexed)
    batch_reference: str (unique, indexed)
    status: str # in_stock, partially_reserved, fully_reserved, expired
    created_at: datetime
```

#### Reservation Model
```python
class Reservation(Base):
    id: int (PK)
    stock_id: int (indexed)
    order_id: int (indexed)
    product_id: int (indexed)
    quantity: float
    status: str (indexed) # active, released, fulfilled
    created_at: datetime (indexed)
    updated_at: datetime
```

**DAL Methods with FEFO Algorithm**:
- `list_stock(skip, limit)` → Ordered by expiry_date ASC (oldest first!)
- `count_stock()` → Total stock items
- `reserve(reserve_req)` → **FEFO**: Find oldest batch → Create Reservation → Update quantities
- `release(reservation_id)` → Revert reservation → Restore available quantity
- `receive(receive_req)` → Create Batch → Create Stock record

---

### 5. GastroRoute_logistics

**File**: `src/routers/v1/logistics/models.py`

#### Route Model
```python
class Route(Base):
    id: int (PK)
    vehicle_id: int (indexed)
    driver_id: int (indexed)
    driver_name: str
    status: str (indexed) # planning, in_progress, completed, cancelled
    total_weight: float
    total_volume: float
    total_distance: float
    start_time: datetime
    estimated_end_time: datetime
    actual_end_time: datetime
    created_at: datetime
    updated_at: datetime
```

#### RoutePoint Model
```python
class RoutePoint(Base):
    id: int (PK)
    route_id: int (indexed)
    client_id: int (indexed)
    address: str
    sequence: int
    status: str (indexed) # pending, in_transit, delivered, failed
    notes: str
    arrived_at: datetime
    completed_at: datetime
    created_at: datetime
    updated_at: datetime
```

#### RouteAssignment Model
```python
class RouteAssignment(Base):
    id: int (PK)
    route_id: int (indexed)
    route_point_id: int (indexed)
    order_id: int (indexed, unique)
    status: str (indexed) # assigned, picked_up, delivered, failed
    created_at: datetime
    updated_at: datetime
```

**DAL Methods**:
- `list_routes(skip, limit)` → Active routes only
- `count_routes()` → Total active routes
- `create_route(plan_req)` → Create Route + RoutePoints
- `assign_order_to_point(route_id, assign_req)` → Create assignment
- `update_point_status(point_id, status_req)` → Update with timestamps

---

### 6. GastroRoute_orders

**File**: `src/routers/v1/orders/models.py`

#### Order Model
```python
class Order(Base):
    id: int (PK)
    client_id: int (indexed)
    client_name: str
    total_amount: DECIMAL(15,2)
    status: str (indexed) # draft, confirmed, in_delivery, closed, cancelled
    delivery_date: datetime (indexed)
    route_id: int (indexed, nullable)
    notes: str
    created_at: datetime (indexed)
    updated_at: datetime
```

#### OrderItem Model
```python
class OrderItem(Base):
    id: int (PK)
    order_id: int (indexed)
    product_id: int (indexed)
    product_name: str
    quantity: float
    unit_price: DECIMAL(15,2)
    total: DECIMAL(15,2)
    status: str (indexed) # pending, reserved, picked, delivered, failed
    created_at: datetime
    updated_at: datetime
```

#### OrderStatusHistory Model
```python
class OrderStatusHistory(Base):
    id: int (PK)
    order_id: int (indexed)
    old_status: str
    new_status: str
    changed_by: str
    notes: str
    created_at: datetime (indexed)
```

**DAL Methods**:
- `list_orders(skip, limit)` → Paginated by created_at DESC
- `count_orders()` → Total count
- `get_by_id(order_id)` → Order with items
- `create(order_in)` → Create Order + OrderItems, calculate totals
- `update_status(order_id, new_status)` → Update with history

---

## Key Features

### Soft Deletes
- **Catalog**: `Product.is_deleted` flag
- All queries filter `is_deleted = False`
- Preserves historical data

### Idempotency
- **Finance**: `Transaction.idempotency_key` (unique)
- Prevents duplicate charges on retry
- `get_by_idempotency_key()` checks before creating

### FEFO Algorithm
- **Warehouse**: Stock ordered by `expiry_date ASC`
- `reserve()` always picks oldest batch first
- Minimizes waste of perishable goods

### Audit Trail
- **Orders**: `OrderStatusHistory` logs all state changes
- Tracks `old_status → new_status` transitions
- Timestamps for compliance

### Relationships
- `Order → OrderItem` (1:N)
- `Order → Route` (M:1)
- `Reservation → Stock` (M:1)
- `RoutePoint → RouteAssignment` (1:N)

---

## Database Requirements

### PostgreSQL Setup

Create databases for each service:
```sql
CREATE DATABASE gastroroute_catalog;
CREATE DATABASE gastroroute_finance;
CREATE DATABASE gastroroute_identity;
CREATE DATABASE gastroroute_warehouse;
CREATE DATABASE gastroroute_logistics;
CREATE DATABASE gastroroute_orders;
```

### Alembic Migrations

Each service should use Alembic to manage schema:
```bash
# In each service directory
alembic init migrations
alembic revision --autogenerate -m "Initial schema"
alembic upgrade head
```

---

## Timestamps

All models use timezone-aware timestamps:
```python
created_at = DateTime(timezone=True), server_default=func.now()
updated_at = DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
```

**Database handles**: Creation and update timestamps automatically via triggers.

---

## Constraints and Indexes

| Model | Key Constraint | Purpose |
|-------|---------------|---------|
| Product | sku UNIQUE | Unique SKU per product |
| Transaction | idempotency_key UNIQUE | Deduplication |
| User | username UNIQUE | Unique login credentials |
| User | email UNIQUE | Unique email |
| Stock | expiry_date INDEX | FEFO ordering |
| RouteAssignment | order_id UNIQUE | One assignment per order |

All models include indexes on frequently queried columns (client_id, status, created_at, etc).

---

## Next Steps

1. ✅ ORM models defined
2. ✅ DAL methods implemented
3. ⏳ **Alembic migrations** (auto-generate from models)
4. ⏳ **Database initialization**
5. ⏳ **Connection pooling** (async sqlalchemy pool config)
6. ⏳ **Integration testing**

---

## Usage Example

```python
# In actions.py
from src.routers.v1.catalog.dal import ProductDAL

async def _list_products(dal: ProductDAL, skip: int, limit: int):
    # DAL handles all database operations
    products = await dal.get_all(skip, limit)  # Returns list of dicts
    total = await dal.count()
    
    # Convert to Pydantic for response
    return ProductListResponse(
        items=[ProductResponse(**p) for p in products],
        total=total,
        skip=skip,
        limit=limit,
    )
```

---

**Status**: ✅ All ORM models and DAL methods fully implemented
**Ready for**: Database initialization and Alembic migrations
