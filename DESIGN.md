# FlyRank Capstone — Design Document

## Problem

Businesses need to capture leads from their websites but existing solutions are either expensive, complex to integrate, or lack customization. The FlyRank Widget Platform solves this by providing an embeddable widget system where customers can:

1. Create custom lead-capture widgets through an API
2. Receive a simple JavaScript snippet to embed on their website
3. Capture visitor submissions with validation and abuse protection
4. Enrich submissions with geographical information
5. Access captured leads through a dashboard

## Users

### Widget Owner/Customer
- Registers and authenticates via JWT
- Creates and manages widgets through API
- Receives embeddable JavaScript snippet
- Views submissions captured by their widgets

### Website Visitor
- Interacts with embedded widget on customer's website
- Submits form data (name, email, etc.)
- Submissions are validated and stored
- IP address is captured for geo-enrichment

## Main Flows

### Owner Flow

```
Owner
  ↓
Authentication (Register/Login)
  ↓
Widget Management API (CRUD)
  ↓
Database (Store widget config)
  ↓
Widget Created
  ↓
Embed Snippet Generated
  ↓
<script src="https://api.flyrank.com/widget.js?id=WIDGET_ID"></script>
```

### Website Flow

```
Customer Website
  ↓
<script> tag loads widget.js
  ↓
widget.js fetches Widget Config from API
  ↓
Widget renders on page (form, button, styling)
  ↓
Visitor interacts with widget
```

### Visitor Flow

```
Visitor
  ↓
Fills out widget form
  ↓
Submits data
  ↓
Validation (required fields, email format)
  ↓
Abuse Protection (rate limiting, IP tracking)
  ↓
Geo Enrichment (country, city from IP)
  ↓
Database (Store submission)
  ↓
Notification (Webhook/Email - Phase 2)
```

## Data Model

### User

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID |
| email | VARCHAR(255) | UNIQUE, NOT NULL, INDEXED | User email |
| password_hash | VARCHAR(255) | NOT NULL | Bcrypt hashed password |
| created_at | TIMESTAMP | NOT NULL | Account creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

### Widget

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID |
| owner_id | VARCHAR(36) | FOREIGN KEY → users.id, NOT NULL, INDEXED | Widget owner |
| type | VARCHAR(50) | NOT NULL | Widget type (lead_capture) |
| title | VARCHAR(255) | NOT NULL | Widget title |
| description | TEXT | NULLABLE | Widget description |
| form_config | JSON | NULLABLE | Form field configuration |
| button_text | VARCHAR(100) | NOT NULL | Submit button text |
| display_options | JSON | NULLABLE | Styling/display options |
| created_at | TIMESTAMP | NOT NULL | Creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update time |

### Submission

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| id | VARCHAR(36) | PRIMARY KEY | UUID |
| widget_id | VARCHAR(36) | FOREIGN KEY → widgets.id, NOT NULL, INDEXED | Parent widget |
| submission_data | JSON | NOT NULL | Form submission data |
| visitor_ip | VARCHAR(45) | NULLABLE | Visitor IP address |
| country | VARCHAR(100) | NULLABLE | Geo-enriched country |
| city | VARCHAR(100) | NULLABLE | Geo-enriched city |
| created_at | TIMESTAMP | NOT NULL | Submission time |

## API Contracts

### Authentication

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/auth/register` | No | Register new user |
| POST | `/api/v1/auth/login` | No | Login, get JWT |

### Widgets

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/widgets` | Yes | Create widget |
| GET | `/api/v1/widgets` | Yes | List own widgets |
| GET | `/api/v1/widgets/{id}` | Yes | Get widget by ID |
| PATCH | `/api/v1/widgets/{id}` | Yes | Update widget |
| DELETE | `/api/v1/widgets/{id}` | Yes | Delete widget |

### Submissions (Phase 2)

| Method | Endpoint | Auth | Description |
|--------|----------|------|-------------|
| POST | `/api/v1/submissions` | No (Public) | Submit form data |
| GET | `/api/v1/widgets/{id}/submissions` | Yes | List widget submissions |

## Indexes

| Table | Column | Index Type | Reason |
|-------|--------|------------|--------|
| users | email | UNIQUE | Fast login lookup |
| widgets | owner_id | INDEX | Fast owner-based queries |
| submissions | widget_id | INDEX | Fast widget-based queries |

### Why These Indexes?

1. **users.email**: Login requires finding user by email. Unique constraint prevents duplicates.
2. **widgets.owner_id**: Most widget queries filter by owner (list user's widgets, tenant isolation check).
3. **submissions.widget_id**: Most submission queries filter by widget (list widget's submissions).

## Tenancy

### Tenant Isolation Strategy

Every widget and submission is owned by a user. The system enforces tenant isolation by:

1. **Database Level**: All widget queries include `WHERE owner_id = current_user.id`
2. **API Level**: Endpoints use `get_current_user` dependency to extract user from JWT
3. **Query Level**: Widget retrieval always filters by both `id` and `owner_id`

### Isolation Examples

```
User A (ID: user_a) → Widget A (owner_id: user_a)
User B (ID: user_b) → Widget B (owner_id: user_b)

User A GET /widgets/widget_b_id
  → Query: SELECT * FROM widgets WHERE id = 'widget_b_id' AND owner_id = 'user_a'
  → Result: Empty (404)
  → User A cannot see User B's widget

User A PATCH /widgets/widget_b_id
  → Query: SELECT * FROM widgets WHERE id = 'widget_b_id' AND owner_id = 'user_a'
  → Result: Empty (404)
  → User A cannot modify User B's widget

User A DELETE /widgets/widget_b_id
  → Query: SELECT * FROM widgets WHERE id = 'widget_b_id' AND owner_id = 'user_a'
  → Result: Empty (404)
  → User A cannot delete User B's widget
```

### Why This Works

- JWT token contains user ID
- Every request extracts user from token
- Every widget query includes owner_id filter
- No way to bypass this check without modifying backend code

## Explicit Non-Goal

**No drag-and-drop form builder.**

The platform will NOT include a visual form builder interface. Widget form configuration is done through JSON configuration in the API. This keeps the project focused on:

- Backend API and authentication
- Widget embedding and rendering
- Submission capture and validation
- Multi-tenant isolation

A form builder would be a significant UI/frontend effort that is out of scope for this capstone.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     FlyRank Backend                         │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Application                                       │
│  ├── Authentication (JWT)                                  │
│  ├── Widget CRUD API                                       │
│  └── Submission API (Phase 2)                              │
├─────────────────────────────────────────────────────────────┤
│  SQLAlchemy 2.0 (Async)                                    │
│  ├── User Model                                            │
│  ├── Widget Model                                          │
│  └── Submission Model                                      │
├─────────────────────────────────────────────────────────────┤
│  Alembic Migrations                                        │
├─────────────────────────────────────────────────────────────┤
│  MySQL Database                                            │
└─────────────────────────────────────────────────────────────┘
         ↑
         │
┌─────────────────────────────────────────────────────────────┐
│  Customer Website                                          │
│  ├── <script> embed snippet                                │
│  └── widget.js (Phase 2)                                   │
└─────────────────────────────────────────────────────────────┘
```

## Phase 1 Scope

This design document covers Phase 1: Design & Foundation.

**Implemented in Phase 1:**
- Project structure
- Database models
- Authentication (register/login)
- Widget CRUD with tenant isolation
- Alembic migrations
- Test suite

**Not in Phase 1 (Phase 2+):**
- Widget JavaScript snippet
- Submission API
- Geo-enrichment
- Dashboard
- Abuse protection
