# FlyRank Capstone — Widget Platform

Embeddable Widget & Lead-Capture Platform Backend

## What It Is

FlyRank is a backend platform that enables customers to create embeddable widgets for capturing leads from their websites. Customers receive a JavaScript snippet, place it on their website, and visitor submissions are validated, enriched with geo-data, and stored for review.

## Features

**Phase 1: Design & Foundation**
- JWT authentication (register/login)
- Widget CRUD with tenant isolation
- SQLAlchemy 2.0 async models
- Alembic migrations
- Comprehensive test suite

**Phase 2: Hardened Submission Path**
- Public submission API
- Pydantic v2 validation
- Rate limiting (10 req/min per IP)
- Honeypot spam protection
- Geo enrichment with fallback (ip-api.com → ipapi.co)
- Safe side effects (notification failure doesn't break submission)
- Idempotency key support

**Phase 3: Delivery, Dashboard & Proof**
- Embeddable widget JavaScript
- Public widget config endpoint
- HTTP caching headers
- Versioned widget bundle (widget.v1.js)
- Customer test website (cross-origin demo)
- Owner dashboard API
- Submission list with filtering
- Basic analytics and stats

## Architecture

```
                 ┌───────────────┐
                 │ Widget Owner  │
                 └───────┬───────┘
                         │
                         ▼
              ┌─────────────────────┐
              │   Widget CRUD API   │
              │   (Authenticated)   │
              └──────────┬──────────┘
                         │
                         ▼
                    ┌─────────┐
                    │ MySQL DB │
                    └─────────┘
                         ▲
                         │
Customer Website ──────────────> widget.js
                         │
                         ▼
              ┌─────────────────────┐
              │  Public Submission  │
              │       API           │
              └──────────┬──────────┘
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
      Validation    Rate Limit     Spam Check
          │              │              │
          └──────────────┼──────────────┘
                         │
                         ▼
                   Geo Enrichment
                   A → B fallback
                         │
                         ▼
                      Database
                         │
                         ▼
                    Notification
```

## Setup

### Prerequisites

- Python 3.11+
- MySQL 8.0+
- pip

### 1. Clone Repository

```bash
git clone https://github.com/karan-rai24/flyrank-capstone-widget-platform.git
cd flyrank-capstone-widget-platform
```

### 2. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

Edit `.env` with your MySQL credentials:

```
DATABASE_URL=mysql+aiomysql://user:password@localhost:3306/flyrank_db
JWT_SECRET_KEY=your-secret-key-here
DEBUG=true
```

### 5. Create Database

```sql
CREATE DATABASE flyrank_db;
```

### 6. Run Migrations

```bash
alembic upgrade head
```

### 7. Seed Demo Data (Optional)

```bash
python -m app.scripts.seed
```

### 8. Start API Server

```bash
uvicorn app.main:app --reload --port 8000
```

### 9. Start Customer Website (New Terminal)

```bash
cd customer-site
python -m http.server 5500
```

### 10. Open Customer Website

Visit: http://localhost:5500

## API Documentation

Once running, visit: http://localhost:8000/docs

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/auth/register` | Register new user |
| POST | `/api/v1/auth/login` | Login and get JWT |

### Widgets (Authenticated)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/widgets/` | Create widget |
| GET | `/api/v1/widgets/` | List own widgets |
| GET | `/api/v1/widgets/{id}` | Get widget |
| PATCH | `/api/v1/widgets/{id}` | Update widget |
| DELETE | `/api/v1/widgets/{id}` | Delete widget |

### Public Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/widgets/{id}/config` | Get widget config |
| POST | `/api/v1/submissions/` | Submit form data |
| GET | `/widget.js` | Widget JavaScript |
| GET | `/widget.v1.js` | Versioned widget |

### Dashboard (Authenticated)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/dashboard/submissions` | List submissions |
| GET | `/api/v1/dashboard/stats` | Get statistics |

## Embedding a Widget

After creating a widget, you'll receive an embed snippet:

```html
<script src="http://localhost:8000/widget.js?id=YOUR_WIDGET_ID"></script>
```

Place this on any website to render the widget.

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | MySQL connection string | - |
| `JWT_SECRET_KEY` | Secret for JWT signing | - |
| `JWT_ALGORITHM` | JWT algorithm | HS256 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiry | 30 |
| `API_BASE_URL` | API base URL | http://localhost:8000 |
| `DEBUG` | Debug mode | false |

## Testing

```bash
pytest tests/ -v
```

## Project Structure

```
flyrank-capstone-widget-platform/
├── app/
│   ├── api/v1/         # API routes
│   ├── core/           # Config, security, database
│   ├── models/         # SQLAlchemy models
│   ├── schemas/        # Pydantic schemas
│   └── services/       # Business logic
├── alembic/            # Database migrations
├── customer-site/      # Demo customer website
├── static/             # Widget JavaScript
├── tests/              # Test suite
├── capstone.yaml       # Project configuration
├── DESIGN.md           # Architecture document
├── EVIDENCE.md         # Test evidence
└── BUILDLOG.md         # AI development log
```

## Current Limitations

- In-memory rate limiting (resets on restart)
- In-memory idempotency (expires after 24h)
- Console notification (development only)
- Free geo provider rate limits

## License

MIT License
