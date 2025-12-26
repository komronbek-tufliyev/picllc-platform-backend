# Frontend Development Guide for UJMP

This guide provides instructions and prompts you can use with Cursor AI to build the frontend for the Unified Journal Management Platform.

---

## Initial Setup Prompt

Copy and paste this to Cursor to start the frontend project:

```
I need to build a frontend application for the Unified Journal Management Platform (UJMP). 

**Backend API:**
- Base URL: http://localhost:8000/api/
- Authentication: JWT Bearer tokens
- API Documentation: http://localhost:8000/api/docs/ (Swagger UI)
- Complete API contract: See api_contract.md in the backend repository

**Project Requirements:**
1. Create a modern React/Next.js frontend application
2. Implement JWT authentication with token refresh
3. Role-based access control (AUTHOR, REVIEWER, ADMIN)
4. Multi-journal support
5. Article submission and workflow management
6. Payment integration
7. Certificate viewing and download
8. Responsive design with modern UI/UX

**Key Features Needed:**
- User authentication (login, registration, profile)
- Journal browsing and selection
- Article submission flow (multi-step form)
- Author dashboard (my articles, status tracking)
- Reviewer dashboard (assigned articles, review interface)
- Admin dashboard (all articles, workflow management, journal management)
- Payment processing (invoice viewing, payment initiation)
- Certificate viewing and verification

**Technology Stack Preferences:**
- React 18+ with TypeScript
- Next.js 14+ (App Router) OR Vite + React
- Tailwind CSS for styling
- React Query/TanStack Query for API calls
- React Hook Form for forms
- Zustand or Redux Toolkit for state management
- Axios or fetch for HTTP requests

**Design Requirements:**
- Modern, clean interface
- Responsive (mobile, tablet, desktop)
- Accessible (WCAG 2.1 AA)
- Dark mode support (optional but preferred)

Please set up the project structure, install dependencies, and create the initial configuration files.
```

---

## Detailed Feature Prompts

### 1. Authentication System

```
Implement the authentication system for UJMP frontend:

**Requirements:**
- Login page with email/password
- Registration page with role selection (AUTHOR, REVIEWER, ADMIN)
- JWT token management (access + refresh tokens)
- Token refresh mechanism (automatic before expiry)
- Protected routes based on user role
- Logout functionality
- Profile page (view/edit user information)

**API Endpoints:**
- POST /api/auth/register/ - Registration
- POST /api/auth/login/ - Login (returns access + refresh tokens)
- POST /api/auth/token/refresh/ - Refresh access token
- GET /api/auth/profile/ - Get user profile
- PUT /api/auth/profile/ - Update user profile

**Implementation Details:**
- Store tokens securely (httpOnly cookies or secure localStorage)
- Implement axios interceptors for automatic token refresh
- Create auth context/provider for global auth state
- Add route guards for protected pages
- Show loading states during authentication
- Handle authentication errors gracefully

Please implement the complete authentication flow with all pages and components.
```

### 2. Journal Management

```
Implement journal browsing and management:

**Requirements:**
- Public journal list page (browse all active journals)
- Journal detail page (show journal info, scope, APC details)
- "Submit to this journal" button (redirects to article submission)
- Admin: Journal CRUD interface
- Admin: Assign reviewers to journals

**API Endpoints:**
- GET /api/journals/ - List all journals
- GET /api/journals/{id}/ - Journal details
- POST /api/journals/ - Create journal (Admin only)
- PUT /api/journals/{id}/ - Update journal (Admin only)
- DELETE /api/journals/{id}/ - Delete journal (Admin only)
- GET /api/journals/assignments/ - Get reviewer assignments
- POST /api/journals/assignments/ - Assign reviewer to journal (Admin only)

**UI Components Needed:**
- JournalCard component (for list view)
- JournalDetail component
- JournalForm component (Admin CRUD)
- ReviewerAssignment component (Admin)

Please implement all journal-related pages and components.
```

### 3. Article Submission Flow

```
Implement the article submission flow for authors:

**Requirements:**
- Multi-step submission form:
  1. Metadata step (title, abstract, keywords, journal selection)
  2. File upload step (manuscript file)
  3. Authors step (add co-authors)
  4. Declarations step (ethics, originality checkboxes)
  5. Review & submit step (summary, final submission)
- Draft auto-save functionality
- File upload with progress indicator
- Validation at each step
- Success page after submission

**API Endpoints:**
- POST /api/articles/ - Create article (DRAFT status)
- PUT /api/articles/{id}/ - Update article (DRAFT only)
- POST /api/articles/{id}/upload_manuscript/ - Upload initial manuscript
- POST /api/articles/{id}/workflow_action/ - Submit article (action: "submit")

**Implementation Details:**
- Use React Hook Form for form management
- Implement step-by-step wizard UI
- Show progress indicator
- Validate file types and sizes
- Handle upload errors
- Auto-save drafts to localStorage or backend

Please implement the complete article submission flow with all steps.
```

### 4. Author Dashboard

```
Implement the author dashboard:

**Requirements:**
- "My Articles" table/list view
- Filter by journal and status
- Search functionality
- Status badges with color coding
- Article detail page showing:
  - Article information
  - Current status and payment status
  - Workflow timeline
  - Versions history
  - Reviews (if available)
  - Actions available (upload revision, view invoice, etc.)
- Upload revision functionality (when status is REVISION_REQUIRED)
- View invoice and payment status
- Download certificate (if published)

**API Endpoints:**
- GET /api/articles/ - List articles (filtered by author)
- GET /api/articles/{id}/ - Article details
- POST /api/articles/{id}/upload_manuscript/ - Upload revision
- GET /api/payments/invoices/{id}/ - Get invoice
- POST /api/payments/invoices/{id}/initiate_payment/ - Initiate payment
- GET /api/certificates/ - List certificates
- GET /api/certificates/{id}/download/ - Download certificate PDF

**UI Components:**
- ArticleTable component (with filters and search)
- ArticleDetail component
- StatusBadge component
- WorkflowTimeline component
- FileUpload component
- InvoiceView component
- PaymentButton component

Please implement the complete author dashboard with all features.
```

### 5. Reviewer Dashboard

```
Implement the reviewer dashboard:

**Requirements:**
- "Assigned Articles" list (articles in UNDER_REVIEW status)
- Filter by journal
- Article review interface:
  - View article details and manuscript
  - Submit review recommendation (ACCEPT, REVISE, REJECT)
  - Add comments to author
  - Add confidential comments (reviewer/admin only)
  - Request revision (with revision type: MINOR/MAJOR)
- Review history (previously reviewed articles)

**API Endpoints:**
- GET /api/articles/ - List assigned articles (filtered by reviewer)
- GET /api/articles/{id}/ - Article details
- GET /api/articles/{id}/download_manuscript/ - Download manuscript
- POST /api/articles/{id}/workflow_action/ - Request revision (action: "request_revision")
- POST /api/articles/{id}/reviews/ - Submit review

**UI Components:**
- AssignedArticlesList component
- ReviewForm component
- ReviewSubmission component
- ManuscriptViewer component (PDF viewer)

Please implement the complete reviewer dashboard with review interface.
```

### 6. Admin Dashboard

```
Implement the admin dashboard:

**Requirements:**
- Overview dashboard with statistics:
  - Total articles by status
  - Pending reviews
  - Pending payments
  - Recent activity
- All articles management:
  - Table view with filters (status, journal, payment_status)
  - Search functionality
  - Bulk actions
  - Article detail with workflow actions
- Workflow actions (superadmin only):
  - Send to review (DESK_CHECK → UNDER_REVIEW)
  - Request revision
  - Accept article
  - Reject article
  - Desk reject
  - Move to production
  - Publish article
- Journal management (CRUD)
- Reviewer assignments
- Payment management
- Certificate management (view, revoke)

**API Endpoints:**
- GET /api/articles/ - List all articles (Admin sees all)
- POST /api/articles/{id}/workflow_action/ - All workflow actions
- GET /api/payments/invoices/ - List all invoices
- GET /api/certificates/ - List all certificates
- POST /api/certificates/{id}/revoke/ - Revoke certificate

**UI Components:**
- AdminDashboard component (statistics)
- ArticlesManagement component
- WorkflowActionButton component
- JournalManagement component
- PaymentManagement component
- CertificateManagement component

Please implement the complete admin dashboard with all management features.
```

### 7. Payment Integration

```
Implement payment processing:

**Requirements:**
- Invoice viewing page
- Payment initiation (redirects to payment provider)
- Payment status tracking
- Payment success/failure callbacks
- Payment history

**API Endpoints:**
- GET /api/payments/invoices/{id}/ - Get invoice details
- POST /api/payments/invoices/{id}/initiate_payment/ - Initiate payment
- GET /api/payments/invoices/{id}/payments/ - Get payment history

**Payment Providers:**
- Payme
- Click

**Implementation Details:**
- Show invoice details (amount, currency, status)
- Payment button that initiates payment
- Handle payment provider redirects
- Show payment status updates
- Display payment history

Please implement the payment processing interface.
```

### 8. Certificate System

```
Implement certificate viewing and verification:

**Requirements:**
- Certificate list (for authors)
- Certificate detail page
- PDF download functionality
- Public verification page (no auth required)
- QR code display (if available)

**API Endpoints:**
- GET /api/certificates/ - List certificates
- GET /api/certificates/{id}/ - Certificate details
- GET /api/certificates/{id}/download/ - Download PDF
- GET /verify/certificate/{certificate_id}/ - Public verification

**UI Components:**
- CertificateList component
- CertificateView component
- CertificateVerification component (public)
- PDFViewer component

Please implement the certificate viewing and verification system.
```

---

## State Management Prompt

```
Set up state management for the UJMP frontend:

**Requirements:**
- Global auth state (user, tokens, role)
- API client configuration (axios with interceptors)
- React Query setup for server state
- Local state management (Zustand or Redux Toolkit)
- Error handling and notifications (toast system)

**Implementation:**
- Create auth store (user info, tokens, login/logout)
- Set up React Query with proper caching
- Configure axios instance with base URL and interceptors
- Implement automatic token refresh
- Add error boundary
- Set up toast notification system (react-hot-toast or similar)

Please set up the complete state management infrastructure.
```

---

## Styling and UI Components Prompt

```
Create a design system and reusable UI components:

**Requirements:**
- Tailwind CSS configuration
- Design tokens (colors, typography, spacing)
- Reusable component library:
  - Button (variants: primary, secondary, danger, etc.)
  - Input (text, email, password, textarea, select)
  - Card
  - Table
  - Modal/Dialog
  - Badge/Status
  - Loading spinner
  - Toast notifications
  - Form components
  - Navigation components
- Responsive layout components
- Dark mode support (optional)

**Design Principles:**
- Modern, clean interface
- Consistent spacing and typography
- Accessible components (ARIA labels, keyboard navigation)
- Mobile-first responsive design

Please create the complete component library and design system.
```

---

## Routing and Navigation Prompt

```
Set up routing and navigation:

**Requirements:**
- Protected routes based on user role
- Public routes (login, register, journal list, certificate verification)
- Role-based navigation menus
- Breadcrumbs
- Route guards

**Routes Needed:**
- Public: /, /login, /register, /journals, /journals/:id, /verify/certificate/:id
- Author: /dashboard, /articles, /articles/:id, /articles/:id/submit
- Reviewer: /dashboard, /reviews, /reviews/:id
- Admin: /dashboard, /articles, /articles/:id, /journals/manage, /payments, /certificates

**Implementation:**
- Use React Router or Next.js App Router
- Create route guard components
- Implement role-based menu rendering
- Add loading states for route transitions

Please set up complete routing with role-based access control.
```

---

## Final Integration Prompt

```
Complete the frontend integration:

**Requirements:**
- Connect all pages to backend API
- Implement error handling throughout
- Add loading states
- Implement form validation
- Add success/error notifications
- Test all user flows:
  - Author: Register → Submit article → Track status → Upload revision → View invoice → Pay → Download certificate
  - Reviewer: Login → View assigned articles → Submit review → Request revision
  - Admin: Login → Manage articles → Perform workflow actions → Manage journals → View payments

**Quality Checks:**
- All API endpoints integrated
- Error handling on all API calls
- Form validation working
- Responsive design tested
- Accessibility checked
- Performance optimized (lazy loading, code splitting)

Please complete the integration and ensure all features work end-to-end.
```

---

## Quick Start Commands

Once Cursor sets up the project, you can use these commands:

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run tests
npm test

# Lint code
npm run lint
```

---

## Backend API Reference

**Base URL:** `http://localhost:8000/api/`

**Key Endpoints:**
- Authentication: `/api/auth/`
- Journals: `/api/journals/`
- Articles: `/api/articles/`
- Payments: `/api/payments/`
- Certificates: `/api/certificates/`
- Audit: `/api/audit/`

**API Documentation:**
- Swagger UI: `http://localhost:8000/api/docs/`
- ReDoc: `http://localhost:8000/api/redoc/`

**Health Checks:**
- `/health/` - Comprehensive health check
- `/health/live/` - Liveness probe
- `/health/ready/` - Readiness probe

---

## Tips for Working with Cursor

1. **Start Small**: Begin with authentication, then build feature by feature
2. **Reference Backend**: Keep `api_contract.md` open for API specifications
3. **Test Incrementally**: Test each feature as you build it
4. **Ask for Clarification**: If something is unclear, ask Cursor to explain
5. **Iterate**: Build MVP first, then enhance with additional features

---

## Project Structure Suggestion

```
frontend/
├── src/
│   ├── components/       # Reusable UI components
│   ├── pages/            # Page components
│   ├── features/         # Feature-based modules
│   │   ├── auth/
│   │   ├── articles/
│   │   ├── journals/
│   │   ├── payments/
│   │   └── certificates/
│   ├── hooks/            # Custom React hooks
│   ├── services/          # API services
│   ├── store/            # State management
│   ├── utils/            # Utility functions
│   ├── types/            # TypeScript types
│   └── styles/           # Global styles
├── public/
└── package.json
```

---

**Good luck with your frontend development!** 🚀

