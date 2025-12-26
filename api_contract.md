# UJMP API Contract

**Version:** 1.0.0  
**Status:** FROZEN - This contract is immutable  
**Last Updated:** 2024-01-15

---

## Table of Contents

1. [Authentication](#authentication)
2. [Request/Response Format](#requestresponse-format)
3. [Error Format](#error-format)
4. [Pagination Format](#pagination-format)
5. [Endpoint Specifications](#endpoint-specifications)
6. [Data Models](#data-models)

---

## Authentication

### JWT Token Authentication

All authenticated endpoints require a JWT Bearer token in the Authorization header.

**Header Format:**
```
Authorization: Bearer <access_token>
```

**Token Lifetime:**
- Access Token: 1 hour
- Refresh Token: 7 days

**Token Refresh:**
When access token expires, use refresh token to obtain new access token:
```
POST /api/auth/token/refresh/
Body: { "refresh": "<refresh_token>" }
```

---

## Request/Response Format

### Content Type
- **Request:** `application/json`
- **Response:** `application/json`

### Character Encoding
- **UTF-8**

### Date/Time Format
- **ISO 8601:** `YYYY-MM-DDTHH:mm:ssZ` (e.g., `2024-01-15T10:30:00Z`)
- **Date only:** `YYYY-MM-DD` (e.g., `2024-01-15`)

---

## Error Format

### Standard Error Response

All errors follow this structure:

```json
{
  "error": "Human-readable error message",
  "detail": "Detailed error description (optional)",
  "code": "ERROR_CODE (optional)"
}
```

### HTTP Status Codes

- `200 OK` - Success
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required
- `403 Forbidden` - Insufficient permissions
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict (e.g., duplicate)
- `422 Unprocessable Entity` - Validation error
- `500 Internal Server Error` - Server error

### Validation Errors

Validation errors return `400 Bad Request` with field-level errors:

```json
{
  "field_name": ["Error message for this field"],
  "another_field": ["Another error message"]
}
```

---

## Pagination Format

All list endpoints support pagination.

### Query Parameters
- `page` - Page number (default: 1)
- `page_size` - Items per page (default: 20, max: 100)

### Response Format

```json
{
  "count": 150,
  "next": "http://api.example.com/api/articles/?page=3",
  "previous": "http://api.example.com/api/articles/?page=1",
  "results": [
    // ... array of items
  ]
}
```

---

## Endpoint Specifications

### Authentication Endpoints

#### Register User
```
POST /api/auth/register/
```

**Request:**
```json
{
  "email": "user@example.com",
  "username": "username",
  "password": "secure_password",
  "password_confirm": "secure_password",
  "first_name": "John",
  "last_name": "Doe",
  "role": "AUTHOR",
  "phone": "+1234567890",
  "affiliation": "University Name"
}
```

**Response:** `201 Created`
```json
{
  "user": {
    "id": 1,
    "email": "user@example.com",
    "username": "username",
    "role": "AUTHOR",
    "first_name": "John",
    "last_name": "Doe"
  },
  "message": "User registered successfully"
}
```

#### Login
```
POST /api/auth/login/
```

**Request:**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "role": "AUTHOR"
  }
}
```

#### Refresh Token
```
POST /api/auth/token/refresh/
```

**Request:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

**Response:** `200 OK`
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Get Profile
```
GET /api/auth/profile/
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "username": "username",
  "role": "AUTHOR",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890",
  "affiliation": "University Name",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z"
}
```

---

### Journal Endpoints

#### List Journals
```
GET /api/journals/
```

**Query Parameters:**
- `apc_enabled` - Filter by APC enabled (boolean)
- `search` - Search in name, ISSN, scope
- `ordering` - Order by: `name`, `created_at`, `-name`, `-created_at`

**Response:** `200 OK`
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Journal of Science",
      "issn": "1234-5678",
      "scope": "Scientific research",
      "apc_enabled": true,
      "apc_amount": "500.00",
      "currency": "USD",
      "logo": "http://example.com/media/journals/logos/journal.jpg",
      "is_active": true
    }
  ]
}
```

#### Get Journal Detail
```
GET /api/journals/{id}/
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "name": "Journal of Science",
  "issn": "1234-5678",
  "scope": "Scientific research articles...",
  "apc_enabled": true,
  "apc_amount": "500.00",
  "currency": "USD",
  "logo": "http://example.com/media/journals/logos/journal.jpg",
  "publication_base_url": "https://journal.example.com",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### Create Journal (Admin Only)
```
POST /api/journals/
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "name": "New Journal",
  "issn": "9876-5432",
  "scope": "Journal description",
  "apc_enabled": true,
  "apc_amount": "500.00",
  "currency": "USD",
  "publication_base_url": "https://journal.example.com",
  "is_active": true
}
```

**Response:** `201 Created` (same as Get Journal Detail)

#### Reviewer-Journal Assignments (Admin Only)

##### List Assignments
```
GET /api/journals/assignments/
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `reviewer` - Filter by reviewer ID
- `journal` - Filter by journal ID

**Response:** `200 OK`
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "reviewer": 3,
      "reviewer_email": "reviewer@example.com",
      "journal": 1,
      "journal_name": "Journal of Science",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ]
}
```

##### Get Assignment Detail
```
GET /api/journals/assignments/{id}/
Authorization: Bearer <admin_token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "reviewer": 3,
  "reviewer_email": "reviewer@example.com",
  "journal": 1,
  "journal_name": "Journal of Science",
  "created_at": "2024-01-15T10:30:00Z"
}
```

##### Create Assignment
```
POST /api/journals/assignments/
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "reviewer": 3,
  "journal": 1
}
```

**Response:** `201 Created`
```json
{
  "id": 1,
  "reviewer": 3,
  "reviewer_email": "reviewer@example.com",
  "journal": 1,
  "journal_name": "Journal of Science",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**Error:** `409 Conflict` - If assignment already exists (unique constraint violation)

##### Update Assignment
```
PUT /api/journals/assignments/{id}/
PATCH /api/journals/assignments/{id}/
Authorization: Bearer <admin_token>
```

**Request (PATCH example):**
```json
{
  "journal": 2
}
```

**Response:** `200 OK` (same as Get Assignment Detail)

##### Delete Assignment
```
DELETE /api/journals/assignments/{id}/
Authorization: Bearer <admin_token>
```

**Response:** `204 No Content`

---

## Architecture Overview

### Scientific vs Business Lifecycle Separation

**Important:** The API separates scientific workflow from payment workflow:

1. **Article.status** (Scientific Lifecycle):
   - Tracks ONLY the editorial/scientific review process
   - Flow: `DRAFT → SUBMITTED → DESK_CHECK → UNDER_REVIEW → REVISION_REQUIRED → UNDER_REVIEW → ACCEPTED → PRODUCTION → PUBLISHED`
   - Payment operations **NEVER** modify `Article.status`

2. **Article.payment_status** (Business Lifecycle):
   - Tracks payment independently from scientific workflow
   - Values: `NONE`, `PENDING`, `PAID`, `NOT_REQUIRED`
   - Set when article is `ACCEPTED` (invoice creation)
   - Updated when payment is confirmed (webhook or admin)

3. **Payment Gates**:
   - `move_to_production` and `publish` actions check `payment_status`
   - Require `payment_status` to be `PAID` or `NOT_REQUIRED`
   - Block action with clear error if gate fails

**Key Principle:** Payment is a business concern that gates publication, but does NOT drive the scientific workflow.

---

### Article Endpoints

#### List Articles
```
GET /api/articles/
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` - Filter by status (DRAFT, SUBMITTED, etc.)
- `journal` - Filter by journal ID
- `search` - Search in title, submission_id, abstract
- `ordering` - Order by: `created_at`, `updated_at`, `submitted_at`, `-created_at`, etc.

**Response:** `200 OK`
```json
{
  "count": 25,
  "next": "http://api.example.com/api/articles/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "submission_id": "SUB-20240115-A3B2C1",
      "title": "Article Title",
      "journal": {
        "id": 1,
        "name": "Journal of Science",
        "issn": "1234-5678"
      },
      "corresponding_author_email": "author@example.com",
      "status": "UNDER_REVIEW",
      "created_at": "2024-01-15T10:30:00Z",
      "updated_at": "2024-01-15T11:00:00Z",
      "submitted_at": "2024-01-15T10:35:00Z"
    }
  ]
}
```

#### Get Article Detail
```
GET /api/articles/{id}/
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "submission_id": "SUB-20240115-A3B2C1",
  "title": "Article Title",
  "abstract": "Article abstract...",
  "keywords": "keyword1, keyword2",
  "corresponding_author": {
    "id": 1,
    "email": "author@example.com",
    "first_name": "John",
    "last_name": "Doe"
  },
  "authors": [
    {
      "name": "John Doe",
      "affiliation": "University Name",
      "email": "john@example.com"
    }
  ],
  "journal": {
    "id": 1,
    "name": "Journal of Science",
    "issn": "1234-5678"
  },
  "status": "UNDER_REVIEW",
  "ethics_declaration": true,
  "originality_declaration": true,
  "publication_url": null,
  "publication_date": null,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T11:00:00Z",
  "submitted_at": "2024-01-15T10:35:00Z",
  "versions": [
    {
      "id": 1,
      "version_number": 1,
      "manuscript_file": "http://example.com/media/articles/manuscripts/file.pdf",
      "revision_type": "INITIAL",
      "notes": "",
      "created_at": "2024-01-15T10:30:00Z",
      "created_by_email": "author@example.com"
    }
  ],
  "reviews": [
    {
      "id": 1,
      "reviewer_email": "reviewer@example.com",
      "reviewer_name": "Jane Reviewer",
      "recommendation": "REVISE",
      "comments_to_author": "Please revise section 3",
      "confidential_comments": "",
      "created_at": "2024-01-15T11:00:00Z",
      "updated_at": "2024-01-15T11:00:00Z"
    }
  ],
  "allowed_transitions": ["ACCEPTED", "REJECTED", "REVISION_REQUIRED"],
  "payment_status": "NONE",
  "has_certificate": false
}
```

**Note:** The `payment_status` field is separate from `status` and tracks payment independently:
- `payment_status: "NONE"` - No invoice yet (article not accepted)
- `payment_status: "PENDING"` - Invoice created, awaiting payment
- `payment_status: "PAID"` - Payment completed
- `payment_status: "NOT_REQUIRED"` - APC not required for this article
```

#### Create Article
```
POST /api/articles/
Authorization: Bearer <author_token>
Content-Type: multipart/form-data
```

**Request:**
```json
{
  "title": "Article Title",
  "abstract": "Article abstract...",
  "keywords": "keyword1, keyword2",
  "authors": [
    {
      "name": "John Doe",
      "affiliation": "University Name",
      "email": "john@example.com"
    }
  ],
  "journal": 1,
  "ethics_declaration": true,
  "originality_declaration": true
}
```

**Response:** `201 Created` (same as Get Article Detail)

#### Update Article (Draft Only)
```
PATCH /api/articles/{id}/
Authorization: Bearer <author_token>
```

**Request:** (same fields as Create Article)

**Response:** `200 OK` (same as Get Article Detail)

#### Upload Initial Manuscript
```
POST /api/articles/{id}/upload_manuscript/
Authorization: Bearer <author_token>
Content-Type: multipart/form-data
```

**When to Use:**
- Upload the **initial manuscript file** when article is in `DRAFT` status
- Upload **revised manuscript** when article is in `REVISION_REQUIRED` status

**Request:**
- `manuscript_file` - File (required, PDF/DOCX)
- `notes` - String (optional)

**Response:** `201 Created`
```json
{
  "id": 1,
  "version_number": 1,
  "manuscript_file": "http://example.com/media/articles/manuscripts/file.pdf",
  "revision_type": "INITIAL",
  "notes": "",
  "created_at": "2024-01-15T10:30:00Z",
  "created_by_email": "author@example.com"
}
```

**Important Notes:**
- For **DRAFT** status: Uploads initial manuscript (version 1). Article must not have any versions yet.
- For **REVISION_REQUIRED** status: Uploads revised manuscript (next version number). Article **automatically transitions to `UNDER_REVIEW` status** (SYSTEM-driven, no manual intervention needed).
- Only the corresponding author can upload manuscripts.
- At least one manuscript file must be uploaded before submitting the article.

#### Workflow Action
```
POST /api/articles/{id}/workflow_action/
Authorization: Bearer <token>
```

**Request:**
```json
{
  "action": "submit",
  "revision_type": "MINOR",
  "publication_url": "https://journal.example.com/article/123",
  "comments": "Optional comments"
}
```

**Actions:**
- `submit` - Submit article (Author only)
  - **Auto-transition**: After submission, article automatically transitions from `SUBMITTED` to `DESK_CHECK` status
  - **Requirements**: Article must be in `DRAFT` status, have title, abstract, ethics/originality declarations, and at least one manuscript file uploaded
  - **Response status**: Article will be in `DESK_CHECK` status in the response
- `desk_reject` - Desk reject (Admin only)
  - **Valid from**: `DESK_CHECK` or `SUBMITTED` status
- `send_to_review` - Send to review (Admin only)
  - **Valid from**: `DESK_CHECK` status only
  - Transitions: `DESK_CHECK` → `UNDER_REVIEW`
- `request_revision` - Request revision (Reviewer/Admin, requires `revision_type`)
  - **Valid from**: `UNDER_REVIEW` status only
  - Transitions: `UNDER_REVIEW` → `REVISION_REQUIRED`
- `accept` - Accept article (Admin only)
  - **Valid from**: `UNDER_REVIEW` or `REVISED_SUBMITTED` status
  - **Transitions**: `UNDER_REVIEW` → `ACCEPTED`
  - **Payment**: Invoice is created if APC is required, `payment_status` is set to `PENDING` or `NOT_REQUIRED`
  - **Important**: `Article.status` transitions to `ACCEPTED` only. Payment does NOT change `Article.status`.
- `reject` - Reject article (Admin only)
  - **Valid from**: `UNDER_REVIEW` or `REVISED_SUBMITTED` status
- `move_to_production` - Move article to production (Admin only)
  - **Valid from**: `ACCEPTED` status only
  - **Payment Gate**: Requires `payment_status` to be `PAID` or `NOT_REQUIRED`
  - **Transitions**: `ACCEPTED` → `PRODUCTION`
  - **Error Response** (`400 Bad Request`): 
    ```json
    {
      "error": "Article cannot move to production. Payment status must be PAID or NOT_REQUIRED, but is currently PENDING."
    }
    ```
- `publish` - Publish article (Admin only, requires `publication_url`)
  - **Valid from**: `ACCEPTED` or `PRODUCTION` status
  - **Payment Gate**: Requires `payment_status` to be `PAID` or `NOT_REQUIRED`
  - **Transitions**: `ACCEPTED`/`PRODUCTION` → `PUBLISHED`
  - **Error Response** (`400 Bad Request`):
    ```json
    {
      "error": "Article cannot be published. Payment status must be PAID or NOT_REQUIRED, but is currently PENDING."
    }
    ```

**Response:** `200 OK` (same as Get Article Detail)

**Note**: The `submit` action transitions the article from `DRAFT` → `SUBMITTED` → `DESK_CHECK` automatically. The response will show the article in `DESK_CHECK` status, ready for reviewer desk check.

#### Upload Revision
```
POST /api/articles/{id}/upload_revision/
Authorization: Bearer <author_token>
Content-Type: multipart/form-data
```

**Note**: This endpoint is kept for backward compatibility. The `upload_manuscript` endpoint can also handle revisions when article is in `REVISION_REQUIRED` status. Both endpoints work identically for revisions.

**Request:**
- `manuscript_file` - File (required)
- `notes` - String (optional)

**Response:** `201 Created`
```json
{
  "id": 2,
  "version_number": 2,
  "manuscript_file": "http://example.com/media/articles/manuscripts/file_v2.pdf",
  "revision_type": "MINOR",
  "notes": "Revised based on reviewer comments",
  "created_at": "2024-01-16T10:30:00Z",
  "created_by_email": "author@example.com"
}
```

**Important Notes:**
- Article must be in `REVISION_REQUIRED` status
- Uploading a revision **automatically transitions article to `UNDER_REVIEW` status** (SYSTEM-driven)
- Review process automatically resumes after revision upload - no manual `send_to_review` action needed
- Only the corresponding author can upload revisions

#### Get Article Timeline
```
GET /api/articles/{id}/timeline/
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
[
  {
    "id": 1,
    "actor_email": "author@example.com",
    "actor_name": "John Doe",
    "action": "ARTICLE_SUBMITTED",
    "entity_type": "ARTICLE",
    "entity_id": 1,
    "metadata": {
      "submission_id": "SUB-20240115-A3B2C1"
    },
    "created_at": "2024-01-15T10:35:00Z"
  }
]
```

---

### Payment Endpoints

#### Invoice Creation

**Important:** Invoices are **automatically created by the system** - there is no manual API endpoint to create invoices.

**When Invoices Are Created:**
- Invoices are automatically generated when an article is **accepted** (status changes to `ACCEPTED`)
- This happens in the article workflow when a Reviewer or Admin accepts an article
- Location: Triggered by `ArticleWorkflowService.accept_article()` method

**Conditions for Invoice Creation:**
1. Article status must be `ACCEPTED`
2. Journal must have APC enabled (`apc_enabled = true`)
3. Journal must have APC amount > 0 (`apc_amount > 0`)

**Automatic Invoice Generation:**
```json
{
  "invoice_number": "INV-ABC123DEF456",  // Auto-generated: INV-{12-char-hex}
  "article": <article_id>,              // One-to-one relationship
  "amount": "500.00",                    // From journal.apc_amount
  "currency": "USD",                     // From journal.currency
  "status": "PENDING",                   // Initial status
  "created_at": "2024-01-15T12:00:00Z"
}
```

**Payment Status After Invoice Creation:**
- If APC is required: `Article.payment_status` is set to `PENDING`, Invoice is created
- If no APC required: `Article.payment_status` is set to `NOT_REQUIRED`, no Invoice is created

**Important:**
- `Article.status` remains `ACCEPTED` (payment does NOT change scientific workflow status)
- Payment is tracked separately via `Article.payment_status` field

**Business Rule:**
> "Invoice generated only after article is ACCEPTED. Payment never modifies Article.status."

---

#### Payment Workflow

The complete payment flow from invoice creation to successful payment:

**Step 1: Article Acceptance → Invoice Creation**
```
Article Status: UNDER_REVIEW → ACCEPTED
↓
System checks: journal.apc_enabled && journal.apc_amount > 0
↓
If APC required:
  - Invoice automatically created with status: PENDING
  - Article.payment_status set to: PENDING
If no APC:
  - Article.payment_status set to: NOT_REQUIRED
  - No invoice created
↓
Article.status remains: ACCEPTED (payment does NOT change status)
```

**Step 2: Author Initiates Payment**
```
Author calls: POST /api/payments/invoices/{id}/initiate_payment/
↓
System returns payment URL from provider (Payme/Click)
↓
Author redirected to payment provider
```

**Step 3: Payment Processing**
```
Author completes payment on provider website
↓
Payment provider processes payment
↓
Provider sends webhook notification to backend
```

**Step 4: Webhook Processing → Payment Success**
```
POST /api/payments/webhooks/payme/ (or /click/)
↓
System verifies webhook signature
↓
System creates Payment record
↓
System updates Invoice.status: PENDING → PAID
↓
System updates Article.payment_status: PENDING → PAID
↓
System sends payment confirmation email
↓
System creates audit log entry
↓
Article.status remains: ACCEPTED (payment does NOT change scientific workflow)
```

**Step 5: Success State**
```
Invoice Status: PAID
Article.payment_status: PAID
Article.status: ACCEPTED (unchanged by payment)
Payment Record: COMPLETED
Article can now proceed to PRODUCTION → PUBLISHED (payment gate satisfied)
```

---

#### List Invoices
```
GET /api/payments/invoices/
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` - Filter by status (PENDING, PAID, FAILED, CANCELLED)
- `payment_provider` - Filter by provider (PAYME, CLICK)
- `search` - Search in invoice_number, article submission_id, article title
- `ordering` - Order by: `created_at`, `paid_at`, `-created_at`, etc.

**Response:** `200 OK`
```json
{
  "count": 10,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "invoice_number": "INV-ABC123DEF456",
      "article_submission_id": "SUB-20240115-A3B2C1",
      "article_title": "Article Title",
      "amount": "500.00",
      "currency": "USD",
      "status": "PENDING",
      "payment_provider": null,
      "created_at": "2024-01-15T12:00:00Z",
      "paid_at": null
    }
  ]
}
```

#### Get Invoice Detail
```
GET /api/payments/invoices/{id}/
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "invoice_number": "INV-ABC123DEF456",
  "article": {
    "id": 1,
    "submission_id": "SUB-20240115-A3B2C1",
    "title": "Article Title"
  },
  "amount": "500.00",
  "currency": "USD",
  "status": "PAID",
  "payment_provider": "PAYME",
  "provider_transaction_id": "TXN123456",
  "created_at": "2024-01-15T12:00:00Z",
  "updated_at": "2024-01-15T13:00:00Z",
  "paid_at": "2024-01-15T13:00:00Z",
  "payments": [
    {
      "id": 1,
      "provider": "PAYME",
      "provider_transaction_id": "TXN123456",
      "amount": "500.00",
      "currency": "USD",
      "status": "COMPLETED",
      "created_at": "2024-01-15T13:00:00Z",
      "updated_at": "2024-01-15T13:00:00Z",
      "completed_at": "2024-01-15T13:00:00Z"
    }
  ]
}
```

#### Initiate Payment
```
POST /api/payments/invoices/{id}/initiate_payment/
Authorization: Bearer <token>
```

**Request:**
```json
{
  "provider": "PAYME",
  "return_url": "https://frontend.example.com/payment/success"
}
```

**Response:** `200 OK`
```json
{
  "payment_url": "https://payme.example.com/pay/INV-ABC123DEF456",
  "invoice_number": "INV-ABC123DEF456",
  "amount": "500.00",
  "currency": "USD"
}
```

**Important Notes:**
- This endpoint **does NOT change** `Article.status` or `Article.payment_status`
- It only prepares the external payment session and returns a redirect URL
- Payment status changes occur only when payment is confirmed via webhook or `mark_as_paid`

#### Mark as Paid (Admin Only)
```
POST /api/payments/invoices/{id}/mark_as_paid/
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "provider_transaction_id": "MANUAL-123",
  "payment_provider": "MANUAL"
}
```

**Response:** `200 OK` (same as Get Invoice Detail)

**Side Effects:**
- `Invoice.status` → `PAID`
- `Article.payment_status` → `PAID`
- **Important**: `Article.status` is **NOT modified** (remains `ACCEPTED`)

#### Mark as Paid (Admin Only)
```
POST /api/payments/invoices/{id}/mark_as_paid/
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "provider_transaction_id": "MANUAL-123",
  "payment_provider": "MANUAL"
}
```

**Response:** `200 OK` (same as Get Invoice Detail)

#### Payment Webhooks

Payment providers (Payme and Click) send webhook notifications when payment status changes. These endpoints are called by the payment providers, not by clients.

##### Payme Webhook
```
POST /api/payments/webhooks/payme/
Content-Type: application/json
X-Payme-Signature: <signature>
```

**Request (from Payme):**
```json
{
  "transaction_id": "TXN123456789",
  "invoice_number": "INV-ABC123DEF456",
  "amount": "500.00",
  "status": "paid",
  "timestamp": "2024-01-15T13:00:00Z"
}
```

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

**Idempotency:**
- If the same `transaction_id` is received multiple times, the webhook returns `{"status": "already_processed"}` without creating duplicate records
- This ensures safe retry behavior from payment providers

**Webhook Processing:**
1. Verifies signature using `PAYME_SECRET_KEY`
2. Checks if payment already exists (idempotency check)
3. Creates `Payment` record with status `COMPLETED` or `FAILED`
4. If status is `paid`:
   - Updates `Invoice.status` to `PAID`
   - Updates `Article.payment_status` to `PAID`
   - Sets `Invoice.paid_at` timestamp
   - Creates audit log entry
   - Sends payment confirmation email
   - **Important**: `Article.status` is **NOT modified** (remains `ACCEPTED`)

**Error Responses:**
- `401 Unauthorized` - Invalid signature
- `400 Bad Request` - Missing required fields or invalid JSON
- `404 Not Found` - Invoice not found

##### Click Webhook
```
POST /api/payments/webhooks/click/
Content-Type: application/json
X-Click-Signature: <signature>
```

**Request (from Click):**
```json
{
  "transaction_id": "CLK987654321",
  "invoice_number": "INV-ABC123DEF456",
  "amount": "500.00",
  "status": "paid",
  "timestamp": "2024-01-15T13:00:00Z"
}
```

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

**Behavior:** Same as Payme webhook (idempotent, same processing flow)

**Security:**
- Webhooks are protected by signature verification
- IP whitelist can be configured via `WEBHOOK_ALLOWED_IPS` environment variable
- Rate limiting applied via `WebhookRateThrottle`

---

#### Payment Success Flow Example

**Complete example from invoice creation to successful payment:**

1. **Article Accepted** (Admin action)
   ```
   POST /api/articles/{id}/workflow_action/
   {
     "action": "accept",
     "comments": "Article accepted for publication"
   }
   ```
   - Article.status: `UNDER_REVIEW` → `ACCEPTED`
   - Invoice automatically created: `INV-ABC123DEF456` (if APC required)
   - Article.payment_status: Set to `PENDING` (if APC required) or `NOT_REQUIRED` (if no APC)
   - **Important**: Article.status remains `ACCEPTED` (payment does NOT change scientific workflow)

2. **Author Views Invoice**
   ```
   GET /api/payments/invoices/{id}/
   ```
   Response shows invoice with status `PENDING`

3. **Author Initiates Payment**
   ```
   POST /api/payments/invoices/{id}/initiate_payment/
   {
     "provider": "PAYME"
   }
   ```
   Response: `{"payment_url": "https://payme.example.com/pay/..."}`

4. **Author Completes Payment on Provider Site**
   - Redirected to Payme payment page
   - Completes payment
   - Provider processes payment

5. **Provider Sends Webhook**
   ```
   POST /api/payments/webhooks/payme/
   {
     "transaction_id": "TXN123456",
     "invoice_number": "INV-ABC123DEF456",
     "status": "paid"
   }
   ```

6. **System Updates Payment Status**
   - Invoice.status: `PENDING` → `PAID`
   - Article.payment_status: `PENDING` → `PAID`
   - Payment record created
   - Email notification sent
   - Audit log created
   - **Important**: Article.status remains `ACCEPTED` (payment does NOT change scientific workflow)

7. **Author Verifies Payment**
   ```
   GET /api/payments/invoices/{id}/
   ```
   Response shows:
   ```json
   {
     "status": "PAID",
     "paid_at": "2024-01-15T13:00:00Z",
     "payment_provider": "PAYME",
     "provider_transaction_id": "TXN123456"
   }
   ```

8. **Article Can Proceed to Production/Publication**
   - Article.status: `ACCEPTED` (unchanged)
   - Article.payment_status: `PAID` (payment gate satisfied)
   - Admin can now call `move_to_production` or `publish` actions
   - Admin can move article to `PRODUCTION` → `PUBLISHED` (payment gate satisfied)

---

### Certificate Endpoints

#### List Certificates
```
GET /api/certificates/
Authorization: Bearer <token>
```

**Query Parameters:**
- `status` - Filter by status (ACTIVE, REVOKED)
- `search` - Search in certificate_id, article submission_id, article title
- `ordering` - Order by: `issued_at`, `-issued_at`

**Response:** `200 OK`
```json
{
  "count": 5,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
      "article_submission_id": "SUB-20240115-A3B2C1",
      "article_title": "Article Title",
      "status": "ACTIVE",
      "issued_at": "2024-01-15T14:00:00Z",
      "revoked_at": null
    }
  ]
}
```

#### Get Certificate Detail
```
GET /api/certificates/{id}/
Authorization: Bearer <token>
```

**Response:** `200 OK`
```json
{
  "id": 1,
  "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
  "article": {
    "id": 1,
    "submission_id": "SUB-20240115-A3B2C1",
    "title": "Article Title"
  },
  "pdf_file": "http://example.com/media/certificates/certificate-550e8400.pdf",
  "status": "ACTIVE",
  "issued_at": "2024-01-15T14:00:00Z",
  "revoked_at": null,
  "revoked_by": null,
  "revocation_reason": "",
  "verification_url": "http://api.example.com/verify/certificate/550e8400-e29b-41d4-a716-446655440000"
}
```

#### Download Certificate PDF
```
GET /api/certificates/{id}/download/
Authorization: Bearer <token>
```

**Response:** `200 OK`
- Content-Type: `application/pdf`
- Content-Disposition: `attachment; filename="certificate-{certificate_id}.pdf"`

#### Revoke Certificate (Admin Only)
```
POST /api/certificates/{id}/revoke/
Authorization: Bearer <admin_token>
```

**Request:**
```json
{
  "reason": "Certificate revoked due to article retraction"
}
```

**Response:** `200 OK` (same as Get Certificate Detail)

#### Public Certificate Verification
```
GET /verify/certificate/{certificate_id}/
```

**Response:** `200 OK`
```json
{
  "certificate_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "ACTIVE",
  "article_title": "Article Title",
  "article_submission_id": "SUB-20240115-A3B2C1",
  "journal_name": "Journal of Science",
  "publication_date": "2024-01-15",
  "publication_url": "https://journal.example.com/article/123",
  "issued_at": "2024-01-15T14:00:00Z",
  "revoked": false
}
```

**Error Response:** `404 Not Found`
```json
{
  "error": "Certificate not found or invalid."
}
```

---

### Audit Endpoints (Admin Only)

#### List Audit Logs
```
GET /api/audit/
Authorization: Bearer <admin_token>
```

**Query Parameters:**
- `action` - Filter by action type
- `entity_type` - Filter by entity type (ARTICLE, INVOICE, CERTIFICATE)
- `actor` - Filter by actor user ID
- `search` - Search in entity_type, metadata
- `ordering` - Order by: `created_at`, `-created_at`

**Response:** `200 OK`
```json
{
  "count": 100,
  "next": "http://api.example.com/api/audit/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "actor_email": "reviewer@example.com",
      "actor_name": "Jane Reviewer",
      "action": "STATUS_CHANGE",
      "entity_type": "ARTICLE",
      "entity_id": 1,
      "metadata": {
        "from_status": "UNDER_REVIEW",
        "to_status": "ACCEPTED",
        "submission_id": "SUB-20240115-A3B2C1"
      },
      "created_at": "2024-01-15T12:00:00Z"
    }
  ]
}
```

---

## Data Models

### User Roles
- `AUTHOR` - Can submit and manage own articles
- `REVIEWER` - Can review, decide, and publish articles
- `ADMIN` - Platform-level operator

### Article Statuses (Scientific Lifecycle)

**Important:** `Article.status` represents **ONLY the scientific/editorial lifecycle**. Payment is tracked separately via `Article.payment_status`.

- `DRAFT` - Not submitted (author can edit and upload initial manuscript)
- `SUBMITTED` - Submitted (intermediate state, auto-transitions to `DESK_CHECK`)
- `DESK_CHECK` - Under desk review (automatic after submission)
- `UNDER_REVIEW` - Under peer review
- `REVISION_REQUIRED` - Author action required (revision requested)
- `REVISED_SUBMITTED` - Legacy state (not used in normal workflow - revisions auto-transition to UNDER_REVIEW)
- `ACCEPTED` - Accepted for publication (final scientific decision)
- `PRODUCTION` - In production
- `PUBLISHED` - Published
- `CERTIFICATE_ISSUED` - Certificate generated
- `REJECTED` - Rejected
- `ARCHIVED` - Archived

**Legacy Statuses (Not Used in Active Workflow):**
- `PAYMENT_PENDING` - Legacy: Payment is now tracked via `payment_status` field
- `PAID` - Legacy: Payment is now tracked via `payment_status` field

### Payment Statuses (Business Lifecycle)

**Important:** `Article.payment_status` is a **separate field** that tracks payment independently from the scientific workflow.

- `NONE` - No invoice yet (article not yet accepted)
- `PENDING` - Invoice created, payment not completed
- `PAID` - Payment completed
- `NOT_REQUIRED` - APC not required for this article (journal has no APC or APC disabled)

### Invoice Statuses
- `PENDING` - Payment pending
- `PAID` - Payment confirmed
- `FAILED` - Payment failed
- `CANCELLED` - Payment cancelled

### Certificate Statuses
- `ACTIVE` - Certificate is active
- `REVOKED` - Certificate revoked

### Payment Providers
- `PAYME` - Payme payment provider
- `CLICK` - Click payment provider

### Revision Types
- `INITIAL` - Initial submission
- `MINOR` - Minor revision
- `MAJOR` - Major revision

### Review Recommendations
- `ACCEPT` - Accept article
- `REVISE` - Request revision
- `REJECT` - Reject article

---

## Webhook Endpoints

### Payme Webhook
```
POST /api/payments/webhooks/payme/
Content-Type: application/json
X-Payme-Signature: <signature>
```

**Request:**
```json
{
  "transaction_id": "TXN123456",
  "invoice_number": "INV-ABC123DEF456",
  "amount": "500.00",
  "status": "paid"
}
```

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

### Click Webhook
```
POST /api/payments/webhooks/click/
Content-Type: application/json
X-Click-Signature: <signature>
```

**Request:** (same format as Payme)

**Response:** `200 OK`
```json
{
  "status": "success"
}
```

---

## Notes

1. **Immutable Contract:** This API contract is frozen and must not be changed without versioning.
2. **Backward Compatibility:** All changes must maintain backward compatibility or introduce new API versions.
3. **Rate Limiting:** API endpoints are rate-limited (see security documentation).
4. **CORS:** CORS is configured for specific origins only (see security documentation).

---

**End of API Contract**

