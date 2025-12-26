# Unified Journal Management Platform (UJMP) - Backend

Django REST Framework backend for the Unified Journal Management Platform.

## Features

- **Multi-journal support**: Manage multiple journals in a single platform
- **Role-based access control**: Author, Reviewer, Admin roles with strict permissions
- **Dual lifecycle architecture**: Scientific workflow (Article.status) separate from business workflow (Article.payment_status)
- **Strict workflow state machine**: Enforced article lifecycle transitions with role-based permissions
- **Payment integration**: Payme and Click payment providers with webhook support
- **Certificate system**: PDF certificate generation with QR codes and public verification
- **Modern admin panel**: Jazzmin-based admin UI with workflow actions (superadmin-only)
- **API documentation**: Auto-generated OpenAPI/Swagger documentation
- **Audit logging**: Complete audit trail of all critical actions
- **Docker support**: Full Docker Compose setup for development and production

## Technology Stack

- Python 3.14
- Django 5.x
- Django REST Framework
- PostgreSQL
- Celery + Redis (background jobs)
- ReportLab (PDF generation)
- MinIO/S3 (file storage)
- django-jazzmin (Modern admin UI)
- drf-spectacular (OpenAPI/Swagger documentation)

## Project Structure

```
cursor-backend/
├── apps/
│   ├── accounts/          # User model and authentication
│   ├── journals/          # Journal management
│   ├── articles/          # Article models and workflow
│   ├── payments/          # Invoice and payment processing
│   ├── certificates/      # Certificate generation
│   └── audit/             # Audit logging
├── ujmp/                  # Django project settings
├── manage.py
├── requirements.txt
└── README.md
```

## Setup Instructions

### Prerequisites

- Python 3.12
- PostgreSQL
- Redis (for Celery)
- MinIO (optional, for S3-compatible storage)

### Installation

1. **Clone the repository** (if applicable)

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. **Run migrations**:
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Run development server**:
   ```bash
   python manage.py runserver
   ```

### Environment Variables

Key environment variables (see `.env.example`):

- `SECRET_KEY`: Django secret key
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`: PostgreSQL configuration
- `CELERY_BROKER_URL`: Redis connection string
- `USE_S3`: Enable S3-compatible storage
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`: MinIO/S3 credentials
- `PAYME_MERCHANT_ID`, `PAYME_SECRET_KEY`: Payme credentials
- `CLICK_MERCHANT_ID`, `CLICK_SECRET_KEY`: Click credentials

## Core Models

### User
- Custom user model with role support (AUTHOR, REVIEWER, ADMIN)
- JWT authentication

### Journal
- Multi-journal support
- APC (Article Processing Charge) configuration
- Logo and publication settings

### Article
- **Dual lifecycle architecture**:
  - `status`: Scientific/editorial workflow (DRAFT → SUBMITTED → DESK_CHECK → UNDER_REVIEW → ACCEPTED → PRODUCTION → PUBLISHED)
  - `payment_status`: Business workflow (NONE → PENDING → PAID or NOT_REQUIRED)
- Strict workflow state machine with role-based transitions
- Business rules:
  - Invoice created only when article is ACCEPTED
  - Payment gate: Articles must have `payment_status = PAID` or `NOT_REQUIRED` before moving to PRODUCTION or PUBLISHING
  - Certificate only after publication
  - Payment operations never modify `Article.status` (scientific workflow)

### ArticleVersion
- Version history for revisions
- File uploads for manuscripts

### Review
- Reviewer comments and recommendations
- Public and confidential comments

### Invoice
- Generated after article acceptance
- Payment provider integration
- Status tracking

### Certificate
- PDF certificate generation
- QR code for verification
- Revocation support (Admin only)

### AuditLog
- Complete audit trail
- Tracks all critical actions

## Workflow States

### Scientific Workflow (Article.status)
Article scientific/editorial lifecycle:

- `DRAFT` → `SUBMITTED` → `DESK_CHECK` → `UNDER_REVIEW`
- `REVISION_REQUIRED` → `UNDER_REVIEW` (auto-transition after revision upload)
- `UNDER_REVIEW` → `ACCEPTED` (Admin only) or `REJECTED` (Admin only)
- `ACCEPTED` → `PRODUCTION` → `PUBLISHED` (payment gate enforced)
- `PUBLISHED` → `CERTIFICATE_ISSUED` (auto-transition)
- `REJECTED` → `ARCHIVED`

### Business Workflow (Article.payment_status)
Payment lifecycle (separate from scientific workflow):

- `NONE`: No invoice yet (pre-acceptance)
- `PENDING`: Invoice created, payment not completed
- `PAID`: Payment completed
- `NOT_REQUIRED`: APC not required for this article

**Key Principle**: Payment operations (`initiate_payment`, `mark_as_paid`) never modify `Article.status`. They only update `Article.payment_status`.

## Business Rules

1. **Dual lifecycle separation**: `Article.status` (scientific) and `Article.payment_status` (business) are tracked separately
2. **Invoice creation**: Invoice created only when article status becomes `ACCEPTED`
3. **Payment gate**: Articles must have `payment_status = PAID` or `NOT_REQUIRED` before moving to PRODUCTION or PUBLISHING
4. **Payment operations**: `initiate_payment` and `mark_as_paid` never modify `Article.status`
5. **Certificate after publication**: Certificates can only be issued for published articles
6. **Strict state transitions**: Only allowed transitions are permitted based on user role
7. **Role-based permissions**:
   - **ADMIN**: All workflow actions, final accept/reject, publishing
   - **REVIEWER**: Request revisions (from UNDER_REVIEW only), submit recommendations
   - **AUTHOR**: Submit articles, upload manuscripts/revisions
8. **Audit logging**: All critical actions are logged

## API Endpoints

Complete API documentation available at `/api/docs/` (Swagger UI) and `/api/redoc/` (ReDoc).

Base URLs:
- `/api/auth/` - Authentication (JWT tokens, registration, profile)
- `/api/journals/` - Journal management (CRUD, assignments)
- `/api/articles/` - Article management (CRUD, workflow actions, manuscript uploads)
- `/api/payments/` - Payment processing (invoices, payment initiation, webhooks)
- `/api/certificates/` - Certificate management (list, download, revoke)
- `/api/audit/` - Audit logs (read-only)
- `/verify/certificate/<certificate_id>/` - Public certificate verification

**Health Check Endpoints:**
- `/health/` - Comprehensive health check (database, Redis, Celery, storage, disk)
- `/health/live/` - Liveness probe (application running)
- `/health/ready/` - Readiness probe (ready to serve traffic)

See `api_contract.md` for complete API specification (frozen contract).  
See `HEALTH_CHECK.md` for health check endpoint documentation.

## Development

### Docker Development (Recommended)

```bash
# Start all services
docker compose up -d

# View logs
docker compose logs -f web

# Run migrations
docker compose exec web python manage.py migrate

# Create superuser
docker compose exec web python manage.py createsuperuser

# Access admin panel
# http://localhost:8000/admin/
```

See `DOCKER.md` for complete Docker setup guide.

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver

# Run Celery worker
celery -A ujmp worker -l info

# Run Celery beat (scheduled tasks)
celery -A ujmp beat -l info
```

### Running Tests

```bash
python manage.py test --settings=ujmp.test_settings
```

### Admin Panel

- **URL**: `http://localhost:8000/admin/`
- **Modern UI**: Jazzmin-based admin interface
- **Workflow Actions**: Available to superadmins only
  - Send to review
  - Request revision
  - Accept/Reject articles
  - Move to production
  - Publish articles
- **Payment Status**: Separate display for scientific vs business workflow

## Documentation

### Core Documentation
- `README.md` - This file (project overview)
- `PROJECT_COMPLETION.md` - Comprehensive project completion summary
- `CHANGELOG.md` - Version history and changes
- `api_contract.md` - Frozen API contract (immutable)

### Deployment & Operations
- `DEPLOYMENT.md` - Production deployment guide
- `DOCKER.md` - Docker setup and configuration
- `SECURITY.md` - Security hardening guide
- `OPERATIONS.md` - Operational procedures

### Technical Documentation
- `workflow_diagram.md` - Workflow state machine visualization
- `doc/requirements.md` - Functional requirements
- `doc/design.md` - UI/UX design specifications
- `doc/tasks.md` - Development roadmap
- `doc/tz.md` - Technical specification

## Quick Start

### Docker (Recommended)

```bash
# Clone repository
git clone <repository-url>
cd picllc-platform-backend

# Start services
docker compose up -d

# Create superuser
docker compose exec web python manage.py createsuperuser

# Access admin panel
# http://localhost:8000/admin/
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run server
python manage.py runserver
```

## Project Status

✅ **PRODUCTION READY**

All features implemented, tested, and documented. See `PROJECT_COMPLETION.md` for details.

## License

[To be determined]

