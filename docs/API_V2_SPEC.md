# DevForge API v2 Specification

## Overview

This document defines the v2 REST API endpoints for database-backed operations. The v1 API (`/api/*`) remains unchanged for backward compatibility. All v2 endpoints require authentication via GitHub OAuth or session token.

## Authentication

### OAuth Token (Primary)
```
Authorization: Bearer <github_access_token>
```
Extracted from session or request headers. Verified against GitHub API.

### Session Token (API)
```
Authorization: Bearer <session_token_hash>
```
Optional token-based auth for CLI or headless clients. Validated against `user_sessions` table.

### Response Headers
```
X-DB-Enabled: true|false         # Feature flag status
X-RateLimit-Remaining: N          # API rate limit
```

---

## Base URL
```
/api/v2
```

---

## 1. Conversations Endpoints

### 1.1 List Conversations
**GET** `/api/v2/conversations`

**Query Parameters:**
```
?limit=50        (default: 50, max: 100)
?offset=0        (default: 0)
?sort=created_at (created_at | updated_at | name)
?order=desc      (asc | desc)
```

**Response:**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Chat",
      "repository_id": "uuid|null",
      "is_active": true,
      "message_count": 5,
      "created_at": "2026-06-11T10:00:00Z",
      "updated_at": "2026-06-11T10:05:00Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 120,
    "has_more": true
  }
}
```

**Status Codes:**
- `200 OK`
- `401 Unauthorized` (invalid token)

---

### 1.2 Create Conversation
**POST** `/api/v2/conversations`

**Request Body:**
```json
{
  "name": "Frontend Refactor",
  "repository_id": "uuid|null"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "name": "Frontend Refactor",
  "repository_id": "uuid|null",
  "is_active": true,
  "message_count": 0,
  "created_at": "2026-06-11T10:00:00Z",
  "updated_at": "2026-06-11T10:00:00Z"
}
```

**Validation:**
- `name` required, max 255 chars
- `repository_id` optional (UUID format if provided)

**Status Codes:**
- `201 Created`
- `400 Bad Request` (validation error)
- `401 Unauthorized`
- `404 Not Found` (repository doesn't exist)

---

### 1.3 Get Conversation
**GET** `/api/v2/conversations/{id}`

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "Frontend Refactor",
  "repository_id": "uuid|null",
  "is_active": true,
  "message_count": 5,
  "created_at": "2026-06-11T10:00:00Z",
  "updated_at": "2026-06-11T10:05:00Z"
}
```

**Status Codes:**
- `200 OK`
- `401 Unauthorized`
- `403 Forbidden` (not your conversation)
- `404 Not Found`

---

### 1.4 Update Conversation
**PUT** `/api/v2/conversations/{id}`

**Request Body:**
```json
{
  "name": "New Name",
  "is_active": false
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "name": "New Name",
  "repository_id": "uuid|null",
  "is_active": false,
  "message_count": 5,
  "created_at": "2026-06-11T10:00:00Z",
  "updated_at": "2026-06-11T10:10:00Z"
}
```

**Status Codes:**
- `200 OK`
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

---

### 1.5 Delete Conversation
**DELETE** `/api/v2/conversations/{id}`

**Response (204 No Content)**

**Status Codes:**
- `204 No Content` (success, no body)
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

---

## 2. Messages Endpoints

### 2.1 List Messages (Paginated)
**GET** `/api/v2/conversations/{conversation_id}/messages`

**Query Parameters:**
```
?limit=50        (default: 50, max: 200)
?offset=0        (default: 0)
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "uuid",
      "conversation_id": "uuid",
      "role": "user",
      "content": "Fix the login button",
      "tokens_used": 150,
      "created_at": "2026-06-11T10:00:00Z"
    },
    {
      "id": "uuid",
      "conversation_id": "uuid",
      "role": "assistant",
      "content": "I'll update the button...",
      "tokens_used": 300,
      "created_at": "2026-06-11T10:00:05Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 25,
    "has_more": false
  }
}
```

**Status Codes:**
- `200 OK`
- `401 Unauthorized`
- `403 Forbidden` (not your conversation)
- `404 Not Found` (conversation doesn't exist)

---

### 2.2 Create Message
**POST** `/api/v2/conversations/{conversation_id}/messages`

**Request Body:**
```json
{
  "role": "user",
  "content": "Fix the login button",
  "tokens_used": 150
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "conversation_id": "uuid",
  "role": "user",
  "content": "Fix the login button",
  "tokens_used": 150,
  "created_at": "2026-06-11T10:00:00Z"
}
```

**Validation:**
- `role` required, must be 'user' or 'assistant'
- `content` required, max 100,000 chars
- `tokens_used` optional, defaults to 0

**Status Codes:**
- `201 Created`
- `400 Bad Request`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

---

### 2.3 Delete Message
**DELETE** `/api/v2/conversations/{conversation_id}/messages/{message_id}`

**Response (204 No Content)**

**Status Codes:**
- `204 No Content`
- `401 Unauthorized`
- `403 Forbidden`
- `404 Not Found`

---

## 3. Repositories Endpoints

### 3.1 List Repositories
**GET** `/api/v2/repositories`

**Query Parameters:**
```
?limit=50
?offset=0
?sort=last_accessed|created_at
?order=desc|asc
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "uuid",
      "owner": "faju85",
      "name": "devforge",
      "branch": "main",
      "last_accessed": "2026-06-11T10:00:00Z",
      "created_at": "2026-06-10T15:00:00Z"
    }
  ],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 5,
    "has_more": false
  }
}
```

---

### 3.2 Create Repository
**POST** `/api/v2/repositories`

**Request Body:**
```json
{
  "owner": "faju85",
  "name": "devforge",
  "branch": "main"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "owner": "faju85",
  "name": "devforge",
  "branch": "main",
  "last_accessed": null,
  "created_at": "2026-06-11T10:00:00Z"
}
```

**Validation:**
- `owner` required, max 255 chars (validate against GitHub)
- `name` required, max 255 chars
- `branch` optional, defaults to "main"

**Status Codes:**
- `201 Created`
- `400 Bad Request`
- `401 Unauthorized`
- `409 Conflict` (duplicate owner/name)

---

### 3.3 Update Repository
**PUT** `/api/v2/repositories/{id}`

**Request Body:**
```json
{
  "branch": "develop",
  "last_accessed": "2026-06-11T10:05:00Z"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "owner": "faju85",
  "name": "devforge",
  "branch": "develop",
  "last_accessed": "2026-06-11T10:05:00Z",
  "created_at": "2026-06-10T15:00:00Z"
}
```

---

### 3.4 Delete Repository
**DELETE** `/api/v2/repositories/{id}`

**Response (204 No Content)**

*Note: Cascade deletes conversations linked to this repo.*

---

## 4. Snippets Endpoints

### 4.1 List Snippets
**GET** `/api/v2/snippets`

**Query Parameters:**
```
?limit=100
?offset=0
?language=python|typescript  (filter)
?sort=created_at|title
?order=asc|desc
```

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "uuid",
      "title": "JWT Helper",
      "language": "typescript",
      "content": "export function decode(token) { ... }",
      "created_at": "2026-06-10T10:00:00Z",
      "updated_at": "2026-06-10T10:00:00Z"
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "total": 12,
    "has_more": false
  }
}
```

---

### 4.2 Create Snippet
**POST** `/api/v2/snippets`

**Request Body:**
```json
{
  "title": "JWT Helper",
  "language": "typescript",
  "content": "export function decode(token) { ... }"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "title": "JWT Helper",
  "language": "typescript",
  "content": "export function decode(token) { ... }",
  "created_at": "2026-06-11T10:00:00Z",
  "updated_at": "2026-06-11T10:00:00Z"
}
```

**Validation:**
- `title` required, max 255 chars
- `language` optional, max 50 chars
- `content` required, max 1,000,000 chars

**Status Codes:**
- `201 Created`
- `400 Bad Request`
- `401 Unauthorized`

---

### 4.3 Update Snippet
**PUT** `/api/v2/snippets/{id}`

**Request Body:**
```json
{
  "title": "JWT Decoder",
  "content": "export function decode(token) { /* updated */ }"
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "title": "JWT Decoder",
  "language": "typescript",
  "content": "export function decode(token) { /* updated */ }",
  "created_at": "2026-06-10T10:00:00Z",
  "updated_at": "2026-06-11T10:05:00Z"
}
```

---

### 4.4 Delete Snippet
**DELETE** `/api/v2/snippets/{id}`

**Response (204 No Content)**

---

## 5. Presets Endpoints

### 5.1 List Presets
**GET** `/api/v2/presets`

**Response (200 OK):**
```json
{
  "data": [
    {
      "id": "uuid",
      "preset_name": "Quick Review",
      "instructions": "Review code for bugs and security issues",
      "rules": "- Check error handling\n- Validate inputs",
      "skills": ["Security", "Tests"],
      "ai_model": "sonnet",
      "provider": "anthropic",
      "created_at": "2026-06-10T10:00:00Z",
      "updated_at": "2026-06-10T10:00:00Z"
    }
  ],
  "pagination": {
    "limit": 100,
    "offset": 0,
    "total": 3,
    "has_more": false
  }
}
```

---

### 5.2 Create Preset
**POST** `/api/v2/presets`

**Request Body:**
```json
{
  "preset_name": "Quick Review",
  "instructions": "Review code for bugs and security issues",
  "rules": "- Check error handling\n- Validate inputs",
  "skills": ["Security", "Tests"],
  "ai_model": "sonnet",
  "provider": "anthropic"
}
```

**Response (201 Created):**
```json
{
  "id": "uuid",
  "preset_name": "Quick Review",
  "instructions": "Review code for bugs and security issues",
  "rules": "- Check error handling\n- Validate inputs",
  "skills": ["Security", "Tests"],
  "ai_model": "sonnet",
  "provider": "anthropic",
  "created_at": "2026-06-11T10:00:00Z",
  "updated_at": "2026-06-11T10:00:00Z"
}
```

**Validation:**
- `preset_name` required, max 255 chars, unique per user
- `ai_model` optional
- `skills` optional, array of strings

**Status Codes:**
- `201 Created`
- `400 Bad Request`
- `401 Unauthorized`
- `409 Conflict` (duplicate preset name)

---

### 5.3 Update Preset
**PUT** `/api/v2/presets/{id}`

**Request Body:**
```json
{
  "instructions": "Updated instructions",
  "skills": ["Security", "Tests", "Performance"]
}
```

**Response (200 OK):**
```json
{
  "id": "uuid",
  "preset_name": "Quick Review",
  "instructions": "Updated instructions",
  "rules": "- Check error handling\n- Validate inputs",
  "skills": ["Security", "Tests", "Performance"],
  "ai_model": "sonnet",
  "provider": "anthropic",
  "created_at": "2026-06-10T10:00:00Z",
  "updated_at": "2026-06-11T10:05:00Z"
}
```

---

### 5.4 Delete Preset
**DELETE** `/api/v2/presets/{id}`

**Response (204 No Content)**

---

## 6. Secrets Endpoints

### 6.1 Get Secret
**GET** `/api/v2/secrets/{type}`

**Path Parameters:**
```
{type}: anthropic_key | groq_key | hf_token | openrouter_key | etc.
```

**Response (200 OK):**
```json
{
  "secret_type": "anthropic_key",
  "created_at": "2026-06-10T10:00:00Z",
  "updated_at": "2026-06-10T10:00:00Z"
}
```

*Note: Returns metadata only, not the decrypted value (for security).*

---

### 6.2 Create/Update Secret
**POST** `/api/v2/secrets`

**Request Body:**
```json
{
  "secret_type": "anthropic_key",
  "secret_value": "sk-ant-xxxxxxxxxxxxxxxxxxxxx"
}
```

**Response (201 Created or 200 OK):**
```json
{
  "secret_type": "anthropic_key",
  "created_at": "2026-06-10T10:00:00Z",
  "updated_at": "2026-06-11T10:00:00Z"
}
```

**Validation:**
- `secret_type` required, max 50 chars
- `secret_value` required, max 10,000 chars (encrypted)

**Status Codes:**
- `201 Created` (new)
- `200 OK` (updated)
- `400 Bad Request`
- `401 Unauthorized`

---

### 6.3 Delete Secret
**DELETE** `/api/v2/secrets/{type}`

**Response (204 No Content)**

---

## 7. Utility Endpoints

### 7.1 Health Check
**GET** `/api/v2/health`

**Response (200 OK):**
```json
{
  "status": "ok",
  "db": "ok|error",
  "latency_ms": 5
}
```

---

### 7.2 Configuration
**GET** `/api/v2/config`

**Response (200 OK):**
```json
{
  "db_enabled": true,
  "version": "2.0.0",
  "features": {
    "extended_thinking": true,
    "code_scanning": true
  }
}
```

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request body",
    "details": [
      {
        "field": "name",
        "message": "must be at most 255 characters"
      }
    ]
  }
}
```

**Common Error Codes:**
- `VALIDATION_ERROR` (400)
- `UNAUTHORIZED` (401)
- `FORBIDDEN` (403)
- `NOT_FOUND` (404)
- `CONFLICT` (409)
- `RATE_LIMITED` (429)
- `INTERNAL_ERROR` (500)

---

## Rate Limiting

- **Tier:** Per-user, per-endpoint
- **Default:** 1000 requests / hour
- **Headers:**
  ```
  X-RateLimit-Limit: 1000
  X-RateLimit-Remaining: 999
  X-RateLimit-Reset: 1686475200
  ```
- **Exceeded:** Returns `429 Too Many Requests`

---

## Pagination

All list endpoints support pagination:

**Query Parameters:**
```
?limit=50   (1-200, default 50)
?offset=0   (≥0, default 0)
```

**Response Metadata:**
```json
{
  "data": [...],
  "pagination": {
    "limit": 50,
    "offset": 0,
    "total": 1000,
    "has_more": true
  }
}
```

---

## Feature Flags

Controlled by response header:

```
X-DB-Enabled: true|false
```

Use this to decide whether frontend routes to `/api/v2/*` or old `/api/*` endpoints.

---

## Testing Examples

### Create a conversation and add messages
```bash
# Create conversation
CONV_ID=$(curl -X POST http://localhost:7860/api/v2/conversations \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name":"Test"}' | jq -r '.id')

# Add message
curl -X POST http://localhost:7860/api/v2/conversations/$CONV_ID/messages \
  -H "Authorization: Bearer $GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"role":"user","content":"Hello","tokens_used":10}'
```

---

## Versioning

Future API versions will use:
- `/api/v3` (next breaking change)
- `/api/v2.1` (backward-compatible addition)

Old endpoints remain available for at least 12 months after deprecation notice.

---

## Changelog

### v2.0.0 (2026-06-11)
- Initial release
- Conversations, Messages, Repositories, Snippets, Presets, Secrets endpoints
- Feature flag support for gradual rollout
