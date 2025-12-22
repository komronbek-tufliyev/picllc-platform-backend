**Unified Journal Management Platform (UJMP)**
*MVP → Production roadmap*

---

## 0. Roles (Updated)

* **Author**
* **Reviewer** *(Editor + Reviewer combined into one role)*
* **Admin**

---

## 1. EPIC: Project Setup & Foundation

### 1.1 Repository & Tooling

* [ ] Create project repository structure (frontend + backend)
* [ ] Define environment configurations (dev / stage / prod)
* [ ] Configure code style, formatting, and linting
* [ ] Setup basic CI pipeline (build + lint)

> **Lovable.dev**: frontend structure only
> **Cursor/Kiro**: backend and integrations added later

---

## 2. EPIC: Authentication & RBAC

### 2.1 Authentication (Frontend – MVP)

* [ ] Login page UI
* [ ] Registration page UI
* [ ] JWT token storage (localStorage or memory)
* [ ] Protected routes based on role

### 2.2 Authentication (Backend – Cursor)

* [ ] User model
* [ ] Secure password hashing
* [ ] JWT access & refresh tokens
* [ ] Role-based access middleware

**Acceptance Criteria**

* Author, Reviewer, and Admin see separate dashboards
* Unauthorized routes are blocked

---

## 3. EPIC: Journals (Multi-Journal Core)

### 3.1 Public Journals (Lovable MVP)

* [ ] Journals list page
* [ ] Journal detail page
* [ ] “Submit to this journal” call-to-action

### 3.2 Journals Management (Backend – Cursor)

* [ ] Journal CRUD (Admin)
* [ ] APC pricing configuration
* [ ] Enable / disable payment per journal

**Acceptance Criteria**

* Multiple journals are visible and selectable on one platform

---

## 4. EPIC: Article Submission (Author)

### 4.1 Submission Flow (Lovable MVP)

* [ ] Multi-step submission form

  * [ ] Metadata step
  * [ ] File upload step
  * [ ] Declarations step
  * [ ] Review & submit step
* [ ] Draft auto-save

### 4.2 Author Dashboard

* [ ] “My Articles” table
* [ ] Status badges
* [ ] Filters (journal, status)
* [ ] Article detail page
* [ ] Article lifecycle timeline / stepper

### 4.3 Revision Handling

* [ ] Revision-required state UI
* [ ] Revised file upload
* [ ] Version history list

**Acceptance Criteria**

* Author can submit, revise, and track articles end-to-end

---

## 5. EPIC: Review & Editorial (Reviewer Role)

> Reviewer role handles **editorial control + peer review**

### 5.1 Reviewer Dashboard (Lovable MVP)

* [ ] Incoming submissions
* [ ] Under review
* [ ] Revisions submitted
* [ ] Accepted / Rejected

### 5.2 Editorial Decisions

* [ ] Desk reject
* [ ] Send to review
* [ ] Request minor / major revision
* [ ] Accept article
* [ ] Reject article

### 5.3 Review Form

* [ ] Recommendation (accept / revise / reject)
* [ ] Comments to author
* [ ] Confidential comments to reviewer/admin

### 5.4 Backend Enforcement (Cursor)

* [ ] Allowed status transitions only
* [ ] Editorial audit logs

**Acceptance Criteria**

* Reviewer fully controls review and decision workflow

---

## 6. EPIC: Payments (APC)

### 6.1 Payment UI (Lovable MVP)

* [ ] Invoice panel on article page
* [ ] Payme button (placeholder)
* [ ] Click button (placeholder)
* [ ] Payment success and failure pages

### 6.2 Payment Backend (Cursor)

* [ ] Invoice model
* [ ] Payme integration
* [ ] Click integration
* [ ] Webhook endpoints
* [ ] Idempotent payment processing
* [ ] Manual “mark as paid” (Admin)

**Acceptance Criteria**

* Accepted article → invoice → payment → PAID status

---

## 7. EPIC: Publication

### 7.1 Publish Flow (Lovable MVP)

* [ ] Publication URL input (Reviewer)
* [ ] Publish confirmation modal
* [ ] Published status badge + link (Author)

### 7.2 Backend Rules (Cursor)

* [ ] Enforce payment-before-publication
* [ ] Store publication date
* [ ] Update article status to PUBLISHED

**Acceptance Criteria**

* Only paid articles can be published

---

## 8. EPIC: Certificate System

### 8.1 Certificate UI (Lovable MVP)

* [ ] Certificate download button
* [ ] Certificate preview page
* [ ] Public verification page

### 8.2 Certificate Backend (Cursor)

* [ ] PDF certificate generator
* [ ] QR code embedding
* [ ] Public verification endpoint
* [ ] Revoke / regenerate certificate (Admin)

**Acceptance Criteria**

* Published article receives a verifiable certificate

---

## 9. EPIC: Admin Panel

### 9.1 Admin UI (Lovable MVP)

* [ ] Journals management
* [ ] Users & role assignment
* [ ] Payments overview
* [ ] Certificates list

### 9.2 Backend (Cursor)

* [ ] Role enforcement
* [ ] Overrides (mark paid, revoke cert)
* [ ] Audit log viewer

---

## 10. EPIC: Notifications (MVP – Minimal)

* [ ] Email notifications for:

  * Submission
  * Decision
  * Revision request
  * Payment confirmation
  * Publication
* [ ] Template-based emails

---

## 11. EPIC: MVP Hardening

* [ ] Error states
* [ ] Empty states
* [ ] Loading skeletons
* [ ] Pagination
* [ ] File size/type validation

---

## 12. FINAL MVP CHECKLIST

* [ ] Multi-journal support
* [ ] Author → submit → track → pay → publish → certificate
* [ ] Reviewer → review → decide → publish
* [ ] Admin → manage journals, payments, certificates
* [ ] Public certificate verification

---
