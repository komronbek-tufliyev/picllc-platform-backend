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
- `desk_reject` - Desk reject (Reviewer/Admin)
- `send_to_review` - Send to review (Reviewer/Admin)
- `request_revision` - Request revision (Reviewer/Admin, requires `revision_type`)
- `accept` - Accept article (Reviewer/Admin)
- `reject` - Reject article (Reviewer/Admin)
- `publish` - Publish article (Reviewer/Admin, requires `publication_url`)

**Response:** `200 OK` (same as Get Article Detail)

#### Upload Revision
```
POST /api/articles/{id}/upload_revision/
Authorization: Bearer <author_token>
Content-Type: multipart/form-data
```

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

### Article Statuses
- `DRAFT` - Not submitted
- `SUBMITTED` - Submitted, awaiting desk check
- `DESK_CHECK` - Under desk review
- `UNDER_REVIEW` - Under peer review
- `REVISION_REQUIRED` - Author action required
- `REVISED_SUBMITTED` - Revision submitted
- `ACCEPTED` - Accepted for publication
- `PAYMENT_PENDING` - Payment required
- `PAID` - Payment confirmed
- `PRODUCTION` - In production
- `PUBLISHED` - Published
- `CERTIFICATE_ISSUED` - Certificate generated
- `REJECTED` - Rejected
- `ARCHIVED` - Archived

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

