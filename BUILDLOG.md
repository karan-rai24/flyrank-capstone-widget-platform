# BUILDLOG.md — AI-Assisted Development Log

This document records how AI assisted in building the FlyRank Widget Platform.

---

## Phase 1: Design & Foundation

### What AI Helped With

1. **Project Structure**
   - AI suggested the directory layout: `app/core/`, `app/api/v1/`, `app/models/`, etc.
   - This follows FastAPI best practices for scalable projects.

2. **Database Models**
   - AI designed the User, Widget, and Submission models with proper relationships.
   - Suggested using UUIDs for primary keys (better for distributed systems).
   - Recommended JSON columns for flexible form_config and display_options.

3. **Authentication Implementation**
   - AI implemented JWT authentication with bcrypt password hashing.
   - Created the `get_current_user` dependency for protecting routes.
   - Used `python-jose` for JWT and `passlib` for password hashing.

4. **Alembic Configuration**
   - AI configured Alembic for async SQLAlchemy.
   - Created the initial migration with proper table definitions.

5. **Test Suite**
   - AI created comprehensive tests for:
     - Authentication (register, login, token validation)
     - Widget CRUD (create, read, update, delete)
     - Tenant isolation (cross-user access prevention)

6. **Design Document**
   - AI structured the DESIGN.md with:
     - Problem statement
     - User personas
     - Main flows (owner, website, visitor)
     - Data model with field descriptions
     - API contracts table
     - Indexes explanation
     - Tenancy strategy
     - Explicit non-goal

### What AI Suggested

- **Use async SQLAlchemy** for better performance with FastAPI.
- **JSON columns** for form_config and display_options (flexible schema).
- **UUID primary keys** for better distributed system support.
- **Pydantic v2** for request/response validation.
- **Bearer token authentication** (standard for APIs).

### Errors in AI Suggestions

1. **Alembic env.py**
   - Initial suggestion used sync engine, but project requires async.
   - Fixed by using `async_engine_from_config` and `asyncio.run()`.

2. **Test Configuration**
   - Initial test setup tried to use MySQL, but SQLite is better for testing.
   - Fixed by creating separate test database configuration.

3. **CORS Configuration**
   - AI initially suggested restricting origins.
   - Changed to `allow_origins=["*"]` for development flexibility.

### What I Changed

1. **Project Structure**
   - Added `services/` directory for business logic separation.
   - Added `utils/` for utility functions.

2. **Environment Variables**
   - Used `pydantic-settings` for type-safe configuration.
   - Added validation for required fields.

3. **Error Handling**
   - Added specific HTTP status codes (400, 401, 404).
   - Added descriptive error messages.

### What I Learned

1. **FastAPI Dependencies**
   - How to use `Depends()` for dependency injection.
   - Creating reusable dependencies like `get_db` and `get_current_user`.

2. **SQLAlchemy 2.0**
   - Modern async SQLAlchemy patterns.
   - Using `Mapped` and `mapped_column` for type hints.

3. **JWT Authentication**
   - Token-based authentication flow.
   - Secure password hashing with bcrypt.

4. **Tenant Isolation**
   - Database-level isolation using foreign key filters.
   - Ensuring queries always include owner_id check.

5. **Alembic Migrations**
   - Async migration configuration.
   - Creating initial database schema.

---

## AI Tools Used

- **Code Generation**: Project structure, models, routes, tests
- **Documentation**: DESIGN.md, README.md, EVIDENCE.md
- **Configuration**: Alembic, environment variables, dependencies
- **Testing**: Test suite structure and assertions

---

## Key Decisions

1. **SQLite for Testing**
   - Faster than MySQL for test runs.
   - No external database required for CI/CD.

2. **JSON Columns for Flexibility**
   - form_config and display_options use JSON.
   - Allows different widget types without schema changes.

3. **UUID Primary Keys**
   - Better for distributed systems.
   - No sequential ID guessing.

4. **Async Throughout**
   - FastAPI is async-native.
   - SQLAlchemy async for non-blocking DB operations.

---

## Phase 2: Hardened Submission Path

### What AI Helped With

1. **Geo Enrichment Service**
   - AI implemented dual-provider fallback chain (ip-api.com → ipapi.co).
   - Created abstract GeoProvider interface for testability.
   - Designed graceful degradation when both providers fail.

2. **Rate Limiting**
   - AI created in-memory rate limiter with configurable limits.
   - Added HTTP headers for rate limit info.
   - Integrated as FastAPI middleware.

3. **Spam Protection**
   - AI implemented honeypot field in submission schema.
   - Designed silent rejection (returns success to not tip off bots).

4. **Idempotency**
   - AI added Idempotency-Key header support.
   - Created in-memory cache with TTL expiration.

5. **Notification Service**
   - AI created notification service with provider pattern.
   - Designed failure-tolerant side effects.

### What AI Suggested

- **In-memory storage** for rate limiting and idempotency (simpler for capstone).
- **Silent honeypot rejection** (returns success to confuse bots).
- **Provider pattern** for geo and notification services.
- **Async notification** to not block main request.

### Errors in AI Suggestions

1. **Rate Limiting Key**
   - AI initially suggested widget-based rate limiting.
   - Changed to IP-based for public endpoint (more appropriate).

2. **Idempotency Storage**
   - AI suggested Redis for production.
   - Kept in-memory for capstone simplicity.

### What I Changed

1. **Notification Design**
   - Added console provider for development.
   - Made webhook provider configurable.

2. **Error Handling**
   - Ensured all errors return clean JSON.
   - Never expose internal details.

### What I Learned

1. **Fallback Chains**
   - How to implement provider fallback with graceful degradation.
   - Importance of not failing the main operation.

2. **Spam Protection**
   - Honeypot technique effectiveness.
   - Silent rejection vs explicit blocking.

3. **Idempotency**
   - Header-based idempotency for safe retries.
   - TTL-based cache expiration.

---

## Phase 3: Delivery, Dashboard & Proof

### What AI Helped With

1. **Widget JavaScript**
   - AI created client-side widget renderer.
   - Implemented form generation from config.
   - Added honeypot field automatically.

2. **Public Config Endpoint**
   - AI designed minimal config response.
   - Added cache headers for performance.

3. **Dashboard API**
   - AI created submission list with filtering.
   - Implemented basic analytics/stats.
   - Ensured tenant isolation.

4. **Versioned Bundle**
   - AI suggested cache-busting via URL versioning.
   - Implemented /widget.v1.js endpoint.

### What AI Suggested

- **URL-based versioning** for cache busting (simple, effective).
- **Immutable cache headers** for widget.js (changes rarely).
- **Short cache** for config (5 minutes).
- **Separate customer-site directory** for demo.

### Errors in AI Suggestions

1. **Widget Rendering**
   - AI initially used innerHTML (XSS risk).
   - Changed to textContent for safe rendering.

2. **Cache Headers**
   - AI suggested no-cache for config.
   - Changed to max-age=300 for better performance.

### What I Changed

1. **Customer Website**
   - Added clear instructions for widget ID replacement.
   - Added visual styling for demo.

2. **Dashboard Stats**
   - Added geo breakdown (countries, cities).
   - Added recent submissions count.

### What I Learned

1. **Cross-Origin Widget Loading**
   - How to serve JavaScript from different origin.
   - CORS configuration for script tags.

2. **Cache Strategy**
   - Immutable for versioned assets.
   - Short TTL for dynamic config.

3. **Dashboard Design**
   - Essential metrics for widget owners.
   - Tenant isolation in queries.

---

## AI Tools Used (All Phases)

- **Code Generation**: Models, routes, services, tests, JavaScript
- **Documentation**: DESIGN.md, README.md, EVIDENCE.md, BUILDLOG.md
- **Architecture**: Service patterns, fallback chains, middleware
- **Testing**: Test structure, mock providers, assertions
- **Configuration**: Environment variables, CORS, rate limiting

---

## Key Decisions (All Phases)

1. **Service Pattern**
   - Separate services for geo, notification, rate limiting.
   - Enables testing with mocks.

2. **In-Memory Storage**
   - Simpler for capstone scope.
   - Would use Redis in production.

3. **Silent Failures**
   - Honeypot returns success.
   - Notification failure doesn't break submission.

4. **URL Versioning**
   - Simple cache busting.
   - Easy to understand and maintain.

---

## What I Would Do Differently

1. **Add Redis** for rate limiting and idempotency in production.
2. **Add webhook signatures** for notification security.
3. **Add widget analytics** (impressions, clicks).
4. **Add email notifications** for submissions.
5. **Add admin dashboard** for platform owner.
