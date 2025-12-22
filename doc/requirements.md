# requirements.md

**Unified Journal Management Platform (UJMP)**

---

## 1. Purpose

The purpose of this document is to define **functional** and **non-functional requirements** for the Unified Journal Management Platform (UJMP).

UJMP is a **multi-journal, role-based academic publishing platform** that manages the full lifecycle of scientific articles:

> Submission → Review → Decision → Payment → Publication → Certification

This document is implementation-agnostic and applies to both:

* MVP frontend (Lovable.dev)
* Full system implementation (Cursor/Kiro)

---

## 2. User Roles

### 2.1 Author

A user who submits and manages their own articles.

**Core goals:**

* Submit articles to journals
* Track article progress
* Respond to revisions
* Pay APC fees
* Access publication links and certificates

---

### 2.2 Reviewer

*(Editor + Reviewer combined)*

A privileged user responsible for **editorial control and peer review**.

**Core goals:**

* Perform desk checks
* Review articles
* Request revisions
* Accept or reject submissions
* Publish accepted articles

---

### 2.3 Admin

A platform-level operator.

**Core goals:**

* Manage journals
* Manage users and roles
* Monitor payments
* Control certificates
* Audit system actions

---

## 3. Functional Requirements

### 3.1 Journal Management

**FR-01**
The system SHALL support multiple journals within a single platform.

**FR-02**
Each journal SHALL have:

* Name
* ISSN
* Scope/description
* APC configuration
* Logo
* Publication base URL (optional)

**FR-03**
Authors SHALL be able to browse journals publicly without authentication.

**FR-04**
Admins SHALL be able to create, update, enable, or disable journals.

---

### 3.2 Authentication & Authorization

**FR-05**
The system SHALL support user registration and login using email and password.

**FR-06**
The system SHALL use JWT-based authentication.

**FR-07**
Access to features SHALL be restricted by role (Author, Reviewer, Admin).

**FR-08**
Users SHALL only see dashboards and actions permitted by their role.

---

### 3.3 Article Submission (Author)

**FR-09**
Authors SHALL be able to create article drafts.

**FR-10**
The article submission form SHALL collect:

* Title
* Abstract
* Keywords
* Authors and affiliations
* Manuscript file
* Declarations (ethics, originality)

**FR-11**
Authors SHALL be able to submit an article to a selected journal.

**FR-12**
Upon submission, the system SHALL assign a unique submission identifier.

**FR-13**
Authors SHALL be able to view all their submissions in a dashboard.

---

### 3.4 Article Lifecycle & Status Tracking

**FR-14**
Each article SHALL follow a predefined workflow state machine.

**FR-15**
The system SHALL display the article lifecycle as a timeline/stepper.

**FR-16**
Authors SHALL see real-time status updates of their articles.

**FR-17**
Only allowed state transitions SHALL be permitted by the system.

---

### 3.5 Review & Editorial Control (Reviewer)

**FR-18**
Reviewers SHALL be able to view all articles assigned to their journals.

**FR-19**
Reviewers SHALL be able to perform desk checks:

* Proceed to review
* Request revision
* Desk reject

**FR-20**
Reviewers SHALL be able to submit reviews including:

* Recommendation (accept / revise / reject)
* Comments to author
* Confidential comments

**FR-21**
Reviewers SHALL be able to request minor or major revisions.

**FR-22**
Reviewers SHALL be able to accept or reject an article.

---

### 3.6 Revision Handling

**FR-23**
When revisions are requested, authors SHALL be able to upload revised versions.

**FR-24**
The system SHALL maintain a version history of all submissions.

**FR-25**
Revised submissions SHALL re-enter the editorial decision workflow.

---

### 3.7 Payments (APC)

**FR-26**
Only accepted articles SHALL generate an invoice.

**FR-27**
The system SHALL support APC payments via:

* Payme
* Click

**FR-28**
The system SHALL update payment status via secure webhooks.

**FR-29**
An article SHALL NOT be published unless payment status is `PAID`, unless overridden by Admin.

**FR-30**
Authors SHALL be able to view payment status and invoices.

---

### 3.8 Publication

**FR-31**
Reviewers SHALL be able to set a publication URL for accepted articles.

**FR-32**
The system SHALL mark articles as `PUBLISHED` after confirmation.

**FR-33**
Authors SHALL see the publication URL once published.

---

### 3.9 Certificate System

**FR-34**
The system SHALL automatically generate a certificate for published articles.

**FR-35**
Certificates SHALL be provided as downloadable PDF files.

**FR-36**
Each certificate SHALL include:

* Certificate ID
* Article metadata
* Journal metadata
* Publication date
* QR code for verification

**FR-37**
The system SHALL provide a public certificate verification page.

**FR-38**
Admins SHALL be able to revoke or regenerate certificates.

---

### 3.10 Admin & Audit

**FR-39**
Admins SHALL manage users and assign roles.

**FR-40**
Admins SHALL view all payments and invoice statuses.

**FR-41**
The system SHALL log critical actions for auditing:

* Status changes
* Payments
* Certificate issuance
* Overrides

---

## 4. Non-Functional Requirements

### 4.1 Security

**NFR-01**
Passwords SHALL be securely hashed.

**NFR-02**
Payment webhooks SHALL be verified and idempotent.

**NFR-03**
Role-based access SHALL be strictly enforced.

---

### 4.2 Performance

**NFR-04**
List views SHALL support pagination.

**NFR-05**
The system SHALL handle concurrent submissions without data corruption.

---

### 4.3 Reliability

**NFR-06**
Payment processing SHALL be retry-safe.

**NFR-07**
Critical operations SHALL be logged for recovery.

---

### 4.4 Maintainability

**NFR-08**
The system SHALL use modular architecture.

**NFR-09**
Workflow rules SHALL be configurable (not hard-coded).

---

### 4.5 Usability

**NFR-10**
The UI SHALL be responsive and accessible.

**NFR-11**
Users SHALL clearly understand article status at all times.

---

## 5. MVP Constraints

* No DOI integration in MVP
* No plagiarism detection in MVP
* No full OJS automation in MVP
* Email notifications only (no SMS/Telegram)

---

## 6. Success Criteria

The MVP SHALL be considered successful if:

1. An author can submit an article and track it end-to-end
2. A reviewer can review, decide, and publish articles
3. Payment is enforced before publication
4. Certificates are generated and publicly verifiable
5. Multiple journals are managed from a single platform
