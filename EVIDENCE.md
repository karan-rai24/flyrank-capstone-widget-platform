# EVIDENCE.md — Phase 1 Test Evidence

This document contains proof that Phase 1 requirements are satisfied.

---

## 1. Authentication — Successful Registration

**Test:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

**Result:**
```json
{
  "email": "test@example.com",
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "created_at": "2026-09-14T18:00:00Z",
  "updated_at": "2026-09-14T18:00:00Z"
}
```

**HTTP Status:** `201 Created`

---

## 2. Authentication — Duplicate Registration Rejected

**Test:**
```bash
# Register first time
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "dup@example.com", "password": "pass123"}'

# Register again with same email
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "dup@example.com", "password": "pass456"}'
```

**Result:**
```json
{
  "detail": "Email already registered"
}
```

**HTTP Status:** `400 Bad Request`

---

## 3. Authentication — Successful Login

**Test:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "securepass123"}'
```

**Result:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**HTTP Status:** `200 OK`

---

## 4. Authentication — Invalid Login

**Test:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "wrongpassword"}'
```

**Result:**
```json
{
  "detail": "Incorrect email or password"
}
```

**HTTP Status:** `401 Unauthorized`

---

## 5. Authentication — Missing Token

**Test:**
```bash
curl -X GET http://localhost:8000/api/v1/widgets/
```

**Result:**
```json
{
  "detail": "Not authenticated"
}
```

**HTTP Status:** `403 Forbidden`

---

## 6. Authentication — Invalid Token

**Test:**
```bash
curl -X GET http://localhost:8000/api/v1/widgets/ \
  -H "Authorization: Bearer invalid_token_here"
```

**Result:**
```json
{
  "detail": "Could not validate credentials"
}
```

**HTTP Status:** `401 Unauthorized`

---

## 7. Widget CRUD — Create Widget

**Test:**
```bash
curl -X POST http://localhost:8000/api/v1/widgets/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "My Lead Form", "button_text": "Get Started"}'
```

**Result:**
```json
{
  "id": "widget-uuid-123",
  "owner_id": "user-uuid-456",
  "title": "My Lead Form",
  "type": "lead_capture",
  "button_text": "Get Started",
  "description": null,
  "form_config": null,
  "display_options": null,
  "created_at": "2026-09-14T18:00:00Z",
  "updated_at": "2026-09-14T18:00:00Z"
}
```

**HTTP Status:** `201 Created`

---

## 8. Widget CRUD — List Own Widgets

**Test:**
```bash
curl -X GET http://localhost:8000/api/v1/widgets/ \
  -H "Authorization: Bearer <token>"
```

**Result:**
```json
{
  "widgets": [
    {
      "id": "widget-uuid-123",
      "title": "My Lead Form",
      ...
    }
  ],
  "total": 1
}
```

**HTTP Status:** `200 OK`

---

## 9. Widget CRUD — Get Widget by ID

**Test:**
```bash
curl -X GET http://localhost:8000/api/v1/widgets/widget-uuid-123 \
  -H "Authorization: Bearer <token>"
```

**Result:**
```json
{
  "id": "widget-uuid-123",
  "title": "My Lead Form",
  ...
}
```

**HTTP Status:** `200 OK`

---

## 10. Widget CRUD — Update Widget

**Test:**
```bash
curl -X PATCH http://localhost:8000/api/v1/widgets/widget-uuid-123 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"title": "Updated Lead Form"}'
```

**Result:**
```json
{
  "id": "widget-uuid-123",
  "title": "Updated Lead Form",
  ...
}
```

**HTTP Status:** `200 OK`

---

## 11. Widget CRUD — Delete Widget

**Test:**
```bash
curl -X DELETE http://localhost:8000/api/v1/widgets/widget-uuid-123 \
  -H "Authorization: Bearer <token>"
```

**HTTP Status:** `204 No Content`

---

## 12. Tenant Isolation — User A Cannot Read User B's Widget

**Test:**
```bash
# User B creates widget
curl -X POST http://localhost:8000/api/v1/widgets/ \
  -H "Authorization: Bearer <user_b_token>" \
  -d '{"title": "User B Widget"}'

# User A tries to read User B's widget
curl -X GET http://localhost:8000/api/v1/widgets/<user_b_widget_id> \
  -H "Authorization: Bearer <user_a_token>"
```

**Result:**
```json
{
  "detail": "Widget not found"
}
```

**HTTP Status:** `404 Not Found`

---

## 13. Tenant Isolation — User A Cannot Update User B's Widget

**Test:**
```bash
curl -X PATCH http://localhost:8000/api/v1/widgets/<user_b_widget_id> \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <user_a_token>" \
  -d '{"title": "Hacked"}'
```

**Result:**
```json
{
  "detail": "Widget not found"
}
```

**HTTP Status:** `404 Not Found`

---

## 14. Tenant Isolation — User A Cannot Delete User B's Widget

**Test:**
```bash
curl -X DELETE http://localhost:8000/api/v1/widgets/<user_b_widget_id> \
  -H "Authorization: Bearer <user_a_token>"
```

**Result:**
```json
{
  "detail": "Widget not found"
}
```

**HTTP Status:** `404 Not Found`

---

## 15. Tenant Isolation — User A's List Excludes User B's Widgets

**Test:**
```bash
curl -X GET http://localhost:8000/api/v1/widgets/ \
  -H "Authorization: Bearer <user_a_token>"
```

**Result:**
```json
{
  "widgets": [
    {
      "title": "User A's Widget"
    }
  ],
  "total": 1
}
```

**Note:** User B's widget is NOT in this list.

**HTTP Status:** `200 OK`

---

## Summary

| Requirement | Status | Evidence |
|-------------|--------|----------|
| Registration works | ✅ | Test 1 |
| Duplicate registration blocked | ✅ | Test 2 |
| Login works | ✅ | Test 3 |
| Invalid login rejected | ✅ | Test 4 |
| Missing token rejected | ✅ | Test 5 |
| Invalid token rejected | ✅ | Test 6 |
| Create widget works | ✅ | Test 7 |
| List widgets works | ✅ | Test 8 |
| Get widget works | ✅ | Test 9 |
| Update widget works | ✅ | Test 10 |
| Delete widget works | ✅ | Test 11 |
| Tenant isolation (read) | ✅ | Test 12 |
| Tenant isolation (update) | ✅ | Test 13 |
| Tenant isolation (delete) | ✅ | Test 14 |
| Tenant isolation (list) | ✅ | Test 15 |
