# FlyRank Capstone — Widget Platform

Embeddable Widget & Lead-Capture Platform Backend

## Project Overview

This is the backend for the FlyRank Capstone project - a platform that allows customers to create embeddable widgets, receive a JavaScript snippet, place it on their website, and capture visitor submissions with geo-enrichment.

## Technology Stack

- **Python 3.11+**
- **FastAPI** - Modern, fast web framework
- **SQLAlchemy 2.0** - SQL toolkit and ORM
- **MySQL** - Relational database
- **Alembic** - Database migrations
- **Pydantic v2** - Data validation
- **JWT** - Authentication

## Project Structure

```
flyrank-capstone-widget-platform/
├── app/
│   ├── core/           # Configuration, security, database
│   ├── api/v1/         # API routes
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── alembic/            # Database migrations
├── tests/              # Test suite
├── DESIGN.md           # Architecture & design document
├── EVIDENCE.md         # Test evidence & proofs
└── BUILDLOG.md         # AI-assisted development log
```

## Current Status

**Phase 1: Design & Foundation** ✅

- [x] Project structure
- [x] Design document
- [x] Database models
- [x] Authentication
- [x] Widget CRUD
- [x] Tenant isolation
- [x] Tests

## Installation

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- pip or poetry

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/karan-rai24/flyrank-capstone-widget-platform.git
   cd flyrank-capstone-widget-platform
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   copy .env.example .env
   # Edit .env with your database credentials
   ```

5. Run migrations:
   ```bash
   alembic upgrade head
   ```

6. Start the server:
   ```bash
   uvicorn app.main:app --reload
   ```

## API Documentation

Once running, visit: `http://localhost:8000/docs`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT |

### Widgets

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| POST | `/api/v1/widgets` | Create widget | ✅ |
| GET | `/api/v1/widgets` | List own widgets | ✅ |
| GET | `/api/v1/widgets/{id}` | Get widget | ✅ |
| PATCH | `/api/v1/widgets/{id}` | Update widget | ✅ |
| DELETE | `/api/v1/widgets/{id}` | Delete widget | ✅ |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | - |
| `JWT_SECRET_KEY` | Secret for JWT signing | - |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 30 |

## Testing

```bash
pytest tests/ -v
```

## License

MIT License - see [LICENSE](LICENSE)

## Phase 1 Completion

See [DESIGN.md](DESIGN.md) for architecture details.
See [EVIDENCE.md](EVIDENCE.md) for test proofs.
See [BUILDLOG.md](BUILDLOG.md) for development log.
