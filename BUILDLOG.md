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

## Next Steps (Phase 2)

- Implement widget JavaScript snippet
- Add submission API
- Geo-enrichment service
- Rate limiting and abuse protection
- Dashboard API
