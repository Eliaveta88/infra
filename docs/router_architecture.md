# GastroRoute Router Architecture Guide

## Overview

All 6 backend services follow a **consistent, modular layered architecture** inspired by professional FastAPI templates.

## Per-Service Structure

Each service `src/routers/v1/{service}/` contains:

### 1. `endpoints.py` — HTTP Interface
- **Role**: HTTP declarations only
- **What it does**:
  - `@router.get/post/patch/delete()` decorators
  - `response_model=SchemaClass` (Pydantic validation)
  - `summary`, `description` documentation
  - `Depends(get_dal)`, `Depends(get_session)` dependency injection
  - **Calls**: Business logic from `actions.py`
  - **Returns**: Pydantic Schema (never raw dict)

```python
@router.get("/products")
async def list_products(
    skip: int = 0,
    limit: int = 50,
    dal: ProductDAL = Depends(get_dal),
) -> ProductListResponse:
    return await _list_products(dal, skip, limit)
```

### 2. `actions.py` — Business Logic
- **Role**: Orchestrates DAL calls and response building
- **What it does**:
  - Validation logic (e.g., idempotency checks)
  - Calls DAL methods
  - Transforms DAL results into Pydantic Schemas
  - Error handling (raises HTTPException)
  - Returns Pydantic Response models

```python
async def _list_products(
    dal: ProductDAL,
    skip: int = 0,
    limit: int = 50,
) -> ProductListResponse:
    products = await dal.get_all(skip, limit)
    total = await dal.count()
    return ProductListResponse(
        items=[ProductResponse(**p) for p in products],
        total=total,
        skip=skip,
        limit=limit,
    )
```

### 3. `dal.py` — Database Access Layer
- **Role**: Pure database operations
- **What it does**:
  - SQLAlchemy queries
  - Returns raw dicts or ORM objects (NOT Pydantic)
  - **Zero HTTP knowledge**
  - Simple, focused methods

```python
class ProductDAL:
    async def get_all(self, skip: int, limit: int) -> list[dict]:
        # SELECT products LIMIT limit OFFSET skip
        # Returns: [{"id": 1, "name": "...", ...}]
        stmt = select(Product).offset(skip).limit(limit)
        result = await self.session.execute(stmt)
        return [p.to_dict() for p in result.scalars().all()]
    
    async def count(self) -> int:
        # SELECT COUNT(*) FROM products
        stmt = select(func.count(Product.id))
        result = await self.session.execute(stmt)
        return result.scalar() or 0
```

### 4. `schemas.py` — Pydantic Models
- **Role**: Request/Response validation only
- **What it does**:
  - `BaseModel` subclasses
  - Field validation (min_length, gt, etc)
  - NO business logic
  - Reusable for multiple endpoints

```python
class ProductResponse(BaseModel):
    id: int
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    
class ProductListResponse(BaseModel):
    items: List[ProductResponse]
    total: int
    skip: int
    limit: int
```

### 5. `enums.py` — Enumerations
- **Role**: Service-specific enums
- **What it does**:
  - Status values: `ProductStatus.ACTIVE`, `ProductStatus.DELETED`
  - Action types: `ProductAction.CREATE`, `ProductAction.UPDATE`
  - Filter types: `SortOrder.ASC`, `SortOrder.DESC`

```python
class ProductStatus(str, Enum):
    ACTIVE = "active"
    DELETED = "deleted"

class SortOrder(str, Enum):
    ASC = "asc"
    DESC = "desc"
```

### 6. `summary.py` — Documentation Summaries
- **Role**: One-line endpoint descriptions
- **What it does**:
  - Short, action-oriented strings
  - Used in OpenAPI docs (Swagger)

```python
LIST_PRODUCTS_SUMMARY = "List all products"
CREATE_PRODUCT_SUMMARY = "Create new product"
DELETE_PRODUCT_SUMMARY = "Delete product"
```

### 7. `description.py` — Documentation Details
- **Role**: Detailed endpoint descriptions
- **What it does**:
  - Multi-line explanations
  - Business context
  - Special notes (e.g., "Action: CREATE")

```python
LIST_PRODUCTS_DESC = (
    "Retrieve all products with pagination support. "
    "Returns list of products available in the catalog. "
    "Action: LIST"
)
```

## Data Flow

```
┌─────────────────────────────────────────────┐
│ HTTP Request                                │
│ GET /api/v1/products?skip=0&limit=50       │
└────────────────────┬────────────────────────┘
                     ↓
         ┌───────────────────────┐
         │ endpoints.list_product│  ← HTTP declaration
         │ response_model=       │    validation
         │ ProductListResponse   │    dependency inject
         └─────────┬─────────────┘
                   ↓
      ┌────────────────────────────┐
      │ actions._list_products()   │  ← Business logic
      │ dal.get_all()              │    Validation
      │ dal.count()                │    Build response
      │ → ProductListResponse      │
      └─────────────┬──────────────┘
                    ↓
         ┌──────────────────────┐
         │ dal.get_all()        │  ← Database ops
         │ SELECT ...           │    Returns dicts
         │ → [{"id": 1, ...}]   │
         └──────────────────────┘
                    ↓
         ┌──────────────────────┐
         │ PostgreSQL Database  │
         └──────────────────────┘
                    ↑
     ┌──────────────────────────┐
     │ ProductListResponse      │  ← Back up
     │ {items: [...], total:..} │    as JSON
     └──────────────────────────┘
                    ↓
         ┌──────────────────────┐
         │ HTTP 200 OK          │
         │ Content-Type: JSON   │
         └──────────────────────┘
```

## Services Using This Pattern

All 6 services implement this architecture:

1. **Identity** (`/api/v1/identity`)
   - Login, logout, user profile
   - JWT token management
   
2. **Catalog** (`/api/v1/catalog`)
   - Products, pagination, search
   - Categories, units

3. **Warehouse** (`/api/v1/warehouse`)
   - Stock overview, hot balances
   - Reserve (FEFO), release, receive batches
   
4. **Finance** (`/api/v1/finance`)
   - Transactions, account balance
   - Invoice generation with idempotency
   
5. **Logistics** (`/api/v1/logistics`)
   - Route planning, delivery point assignment
   - Status tracking
   
6. **Orders** (`/api/v1/orders`)
   - Order creation, status pipeline
   - Integration to warehouse and logistics

## Best Practices

✅ **DO**:
- Keep endpoints simple (just HTTP concerns)
- Put business logic in actions
- Keep DAL focused on queries
- Return Pydantic models from all endpoints
- Use Depends() for injection
- Write summary + description for each endpoint

❌ **DON'T**:
- Mix HTTP and business logic
- Return raw dicts from endpoints
- Put queries directly in endpoints
- Use global state
- Skip error handling
- Ignore documentation

## Example: Complete Endpoint

```python
# endpoints.py
@catalog_router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary=GET_PRODUCT_SUMMARY,
    description=GET_PRODUCT_DESC,
)
async def get_product(
    product_id: int,
    dal: ProductDAL = Depends(get_dal),
) -> ProductResponse:
    return await _get_product_detail(product_id, dal)

# actions.py
async def _get_product_detail(
    product_id: int,
    dal: ProductDAL,
) -> ProductResponse:
    product = await dal.get_by_id(product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return ProductResponse(**product)

# dal.py
async def get_by_id(self, product_id: int) -> dict | None:
    stmt = select(Product).where(Product.id == product_id)
    result = await self.session.execute(stmt)
    product = result.scalar_one_or_none()
    return product.to_dict() if product else None

# schemas.py
class ProductResponse(BaseModel):
    id: int
    name: str = Field(..., min_length=1)
    price: float = Field(..., gt=0)
    class Config:
        from_attributes = True

# summary.py
GET_PRODUCT_SUMMARY = "Get product details"

# description.py
GET_PRODUCT_DESC = (
    "Get full product information by ID. "
    "Includes pricing, availability, and attributes. "
    "Action: GET_DETAIL"
)
```

## Integration Points

Services communicate via HTTP:
- Orders → Warehouse: Reserve stock
- Orders → Logistics: Assign route
- Frontend → Identity: Login/JWT
- Frontend → All services: Data retrieval

Each service is **independent** with its own database.

## Migration Checklist

✅ All 6 services refactored
✅ Consistent patterns across all services
✅ API contract documented
✅ Endpoint summaries and descriptions completed
✅ DAL placeholders with TODO comments ready for ORM integration

**Next steps**: Implement ORM models and connect DAL methods to actual database operations.
