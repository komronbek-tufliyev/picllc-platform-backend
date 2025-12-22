Build a production-style MVP frontend for a web application called
“Unified Journal Management Platform (UJMP)”.

Purpose:
A multi-journal academic publishing platform that manages article
submission, review, payment, publication, and certification.

Tech assumptions:
- React-style SPA
- REST API backend exists (mock responses allowed)
- JWT authentication
- Role-based routing

User roles:
- Author
- Reviewer (editorial + peer review combined)
- Admin

GLOBAL UI STYLE:
- Clean academic design
- White background, blue primary color
- Card-based layouts
- Status badges
- Timeline/stepper components
- Responsive dashboard layout

PAGES TO BUILD:

PUBLIC
- Landing page (platform overview)
- Journals list page
- Journal detail page
- Login & Register pages
- Public certificate verification page

AUTHOR DASHBOARD
- My Articles table (status badges, filters)
- Submit Article wizard (multi-step form)
- Article detail page with:
  - Lifecycle timeline
  - Messages from reviewer
  - File versions
  - Revision upload (conditional)
  - Payment panel (conditional)
  - Publication link + certificate download (conditional)

REVIEWER DASHBOARD
- Incoming submissions
- In review
- Revisions submitted
- Accepted / Rejected
- Article review page:
  - Review form (recommendation, comments)
  - Decision actions (accept, reject, request revision)
  - Publication URL input
  - Publish action

ADMIN PANEL
- Journals management (CRUD UI)
- Users & roles
- Payments overview
- Certificates list

UX REQUIREMENTS:
- Role-based navigation
- Status-based conditional UI
- Confirmation modals for critical actions
- Empty states and loading states

NOT REQUIRED:
- Backend logic
- Real payment integration
- Real PDF generation

Focus on:
- Correct workflows
- Clean UI
- API-ready components
- Realistic academic product design
