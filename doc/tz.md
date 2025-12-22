# tz.md

**Unified Journal Management Platform (UJMP)**
**Technical Specification (Cursor-Optimized)**

---

## 1. Project Overview

**Project Name:** Unified Journal Management Platform (UJMP)

**Purpose:**
UJMP is a multi-journal academic publishing platform that manages the **complete lifecycle of scientific articles** from submission to publication and certification, enforcing editorial workflow, payments, and verification.

The system MUST support multiple journals within a single platform and enforce **strict business rules**.

---

## 2. Scope

### In Scope (MVP + Production)

* Multi-journal support
* Article submission and tracking
* Editorial review and decision making
* Revision handling
* APC payment (Payme / Click)
* Publication enforcement
* Certificate generation and verification
* Role-based access control
* Audit logging

### Out of Scope (MVP)

* DOI / Crossref integration
* Plagiarism detection
* Automatic OJS publishing
* SMS / Telegram notifications
* Advanced production workflows (copyediting, galley proofs)

---

## 3. User Roles

### 3.1 Author

* Submits and manages own articles
* Uploads revisions
* Pays APC fees
* Views publication links
* Downloads certificates

### 3.2 Reviewer

*(Editorial + Peer Review combined)*

* Performs desk checks
* Reviews articles
* Requests revisions
* Accepts or rejects submissions
* Publishes articles after payment

### 3.3 Admin

* Manages journals
* Manages users and roles
* Oversees payments
* Manages certificates
* Performs administrative overrides
* Views audit logs

---

## 4. Core Business Rules (NON-NEGOTIABLE)

1. **Payment before publication is mandatory**

   * An article MUST NOT be published unless payment status is `PAID`
   * Exception: Admin override (logged)

2. **Certificates are issued only after publication**

   * No certificate for unpublished articles

3. **Strict workflow enforcement**

   * Only allowed status transitions are permitted
   * All status changes are logged

4. **Role isolation**

   * Authors cannot edit decisions
   * Reviewers cannot modify payment status
   * Admin actions are fully audited

5. **Public verification**

   * Certificate verification endpoint is public and read-only

---

## 5. Article Workflow (State Machine)

Allowed article states:

```
DRAFT
SUBMITTED
DESK_CHECK
REVIEWERS_INVITED
UNDER_REVIEW
REVISION_REQUIRED
REVISED_SUBMITTED
EDITOR_DECISION
ACCEPTED
PAYMENT_PENDING
PAID
PRODUCTION
SCHEDULED
PUBLISHED
CERTIFICATE_ISSUED
REJECTED
ARCHIVED
```

### Workflow Rules

* Only Authors can move `DRAFT → SUBMITTED`
* Only Reviewers can perform editorial decisions
* Only system/webhooks can move `PAYMENT_PENDING → PAID`
* Only Reviewers can publish articles
* Only Admins can override workflow states

---

## 6. Journal Management

Each Journal MUST have:

* Name
* ISSN
* Scope / description
* APC enabled (boolean)
* APC amount
* Currency
* Logo
* Publication base URL (optional)

Admins manage all journal configurations.

---

## 7. Authentication & Authorization

* JWT-based authentication
* Access token + refresh token
* Role-based route protection
* Journal-scoped permissions for Reviewers

---

## 8. Article Submission Requirements

Authors submit articles with:

* Title
* Abstract
* Keywords
* Author list and affiliations
* Manuscript file (PDF/DOCX)
* Declarations (ethics, originality)

Each submission receives a **unique submission identifier**.

---

## 9. Review & Editorial Process

* Desk check performed by Reviewer
* Review includes:

  * Recommendation (accept / revise / reject)
  * Comments to author
  * Confidential comments
* Revision types:

  * Minor
  * Major
* Multiple revision cycles allowed (MVP: unlimited)

---

## 10. Payments (APC)

### Supported Providers

* Payme
* Click

### Payment Rules

* Invoice generated only after `ACCEPTED`
* Webhook-based confirmation
* Idempotent processing required
* Failed payments do not advance workflow

---

## 11. Publication

* Reviewer sets publication URL
* System enforces:

  * payment status == `PAID`
* Publication date is stored
* Status becomes `PUBLISHED`

---

## 12. Certificate System

### Certificate Requirements

* PDF format
* Unique certificate ID
* Article metadata
* Journal metadata
* Publication date
* Publication URL
* QR code for verification

### Verification

* Public endpoint:

  ```
  /verify/certificate/{uuid}
  ```
* Shows:

  * Valid / revoked status
  * Article and journal info
  * Publication link

---

## 13. Audit Logging

The system MUST log:

* Status changes
* Review decisions
* Payment confirmations
* Certificate issuance/revocation
* Admin overrides

Logs MUST include:

* Actor
* Timestamp
* Entity type
* Action
* Metadata

---

## 14. Non-Functional Requirements

### Security

* Password hashing
* Webhook signature verification
* Strict RBAC enforcement

### Reliability

* Retry-safe payment processing
* No duplicate invoices
* No duplicate certificates

### Maintainability

* Modular architecture
* Configurable workflow rules
* Clear separation of concerns

---

## 15. Technology Assumptions (Recommended)

* Backend: Django REST Framework **or** NestJS
* Database: PostgreSQL
* Storage: S3 / MinIO
* Background jobs: Celery / BullMQ
* PDF: ReportLab or equivalent
* Frontend: Already provided (Lovable.dev MVP)

---

## 16. Acceptance Criteria (System Level)

The system is accepted when:

1. Authors can submit and track articles end-to-end
2. Reviewers can review, decide, and publish articles
3. Payment is enforced before publication
4. Certificates are issued and publicly verifiable
5. Multiple journals operate independently within one platform

---

## 17. Cursor Execution Rule

Cursor MUST:

* Follow this TZ strictly
* Not invent workflows or UI
* Enforce all business rules
* Ask clarification ONLY if something is undefined
