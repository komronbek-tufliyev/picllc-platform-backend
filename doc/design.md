# design.md

**Unified Journal Management Platform (UJMP)**

---

## 1. Design Goals

The design must satisfy the following principles:

1. **Clarity over complexity**
   Users must immediately understand:

   * where their article is
   * what action is required
   * what happens next

2. **Role-first UX**
   Each role (Author, Reviewer, Admin) sees:

   * only relevant actions
   * no irrelevant controls

3. **Workflow transparency**
   Article lifecycle must be:

   * visible
   * predictable
   * auditable

4. **MVP-first, extensible later**
   Design must allow:

   * fast MVP via Lovable.dev
   * later extension without redesign

---

## 2. Global Layout System

### 2.1 Application Shell

```
┌──────────────────────────────────────┐
│ Topbar                               │
│ - Logo                               │
│ - Active journal (if applicable)     │
│ - User menu (profile, logout)        │
└──────────────────────────────────────┘
┌──────────────┬───────────────────────┐
│ Sidebar      │ Main Content Area      │
│              │                       │
│ - Dashboard  │ - Tables               │
│ - Articles   │ - Forms                │
│ - Journals   │ - Timelines             │
│ - Payments   │ - Modals                │
│ - Admin      │                       │
└──────────────┴───────────────────────┘
```

### 2.2 Sidebar (Role-based)

**Author**

* Dashboard
* My Articles
* Submit Article
* Certificates

**Reviewer**

* Dashboard
* Incoming Submissions
* In Review
* Revisions
* Accepted / Rejected

**Admin**

* Journals
* Users & Roles
* Payments
* Certificates
* Audit Logs

---

## 3. Design System

### 3.1 Colors

* Primary: Academic Blue (`#1E4FD8`)
* Success: Green (`#2ECC71`)
* Warning: Orange (`#F39C12`)
* Error: Red (`#E74C3C`)
* Neutral: Gray scale (`#F5F6FA → #2C2C2C`)

### 3.2 Status Badge Mapping

| Status            | Color     | Meaning                |
| ----------------- | --------- | ---------------------- |
| DRAFT             | Gray      | Not submitted          |
| SUBMITTED         | Blue      | Waiting for desk check |
| UNDER_REVIEW      | Orange    | Review in progress     |
| REVISION_REQUIRED | Red       | Author action required |
| ACCEPTED          | Green     | Accepted               |
| PAYMENT_PENDING   | Orange    | Payment required       |
| PAID              | Blue      | Payment confirmed      |
| PUBLISHED         | Green     | Publicly available     |
| REJECTED          | Dark Gray | Closed                 |

---

## 4. Core UI Components

### 4.1 Article Timeline (Critical Component)

Horizontal or vertical stepper:

```
Submitted → Review → Decision → Payment → Published → Certificate
```

Each step:

* status icon (done / active / blocked)
* timestamp
* tooltip with explanation

This component is reused in:

* Author article detail
* Reviewer article detail
* Admin audit view

---

### 4.2 Article Table

Reusable table component with:

* Column sorting
* Status badge
* Row actions dropdown
* Pagination

Used in:

* My Articles
* Incoming Submissions
* Payments
* Certificates

---

### 4.3 Action Modals

All critical actions use confirmation modals:

* Submit article
* Request revision
* Accept / Reject
* Publish article
* Issue certificate
* Mark payment paid (admin)

Modal always shows:

* Article title
* Journal
* Irreversible warning if applicable

---

## 5. Page-Level Design

---

## 5.1 Public Pages

### Landing Page

Sections:

* Platform description
* How it works (4 steps)
* Journals showcase
* Call to action (Submit article)

### Journals List

* Card layout
* ISSN, scope snippet, APC price
* “Submit to this journal” button

### Certificate Verification

Public page:

* Certificate ID input or QR scan
* Validation result:

  * valid / revoked
* Article + journal metadata
* Publication link

---

## 5.2 Author Pages

### Author Dashboard

Widgets:

* Total submissions
* Under review
* Revision required
* Published

### My Articles

Table:

* Article ID
* Journal
* Title
* Status
* Last updated
* Action: View

### Submit Article (Wizard)

Step 1: Metadata
Step 2: File upload
Step 3: Declarations
Step 4: Review & submit

Draft autosave enabled.

### Article Detail (Author)

Sections:

1. Timeline
2. Editorial messages
3. File versions
4. Revision upload (conditional)
5. Payment panel (conditional)
6. Publication & certificate (conditional)

---

## 5.3 Reviewer Pages

### Reviewer Dashboard

KPIs:

* Pending desk checks
* In review
* Revisions awaiting decision

### Incoming Submissions

Table with quick actions:

* Desk reject
* Send to review

### Article Review Page

Tabs:

* Article info
* Files
* Reviews
* Decision

Decision panel:

* Request minor revision
* Request major revision
* Accept
* Reject

### Review Form

Fields:

* Recommendation (radio)
* Comments to author
* Confidential comments

---

## 5.4 Admin Pages

### Journals Management

* Create/Edit journal
* APC configuration
* Enable/disable payments
* Logo upload

### Users & Roles

* User list
* Role assignment
* Journal assignment for reviewers

### Payments Overview

* Invoice list
* Status filters
* Provider filter
* Manual override action

### Certificates

* Issued certificates list
* Revoke / regenerate

### Audit Logs

* Timeline view
* Filter by entity / user / action

---

## 6. Navigation & Routing Rules

* Role-based route guards
* Unauthorized access → 403 page
* Session expired → login redirect
* Direct deep-link support:

  * `/articles/{id}`
  * `/verify/cert/{uuid}`

---

## 7. MVP UI Constraints (Lovable.dev)

For Lovable MVP:

* Mock API responses allowed
* Payment buttons are placeholders
* Publication URL manually entered
* Certificate PDF mocked or static

For Cursor completion:

* Replace mocks with real API
* Enable file uploads
* Enable webhook callbacks
* Enable PDF generation

---

## 8. Error & Empty States

* No articles → guidance message
* No journals → admin warning
* Payment failed → retry CTA
* Forbidden action → explanation + contact admin

---

## 9. Accessibility & UX Notes

* All status colors paired with icons/text
* Forms with inline validation
* Clear next-step messaging
* No hidden workflow transitions

---

## 10. Design Acceptance Criteria

The design is accepted if:

1. Each role has a clearly distinct dashboard
2. Article status is always visible and understandable
3. Payment is visually enforced before publication
4. Certificate verification is public and simple
5. MVP UI can be generated directly by Lovable.dev
