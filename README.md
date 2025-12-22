# Unified Journal Management Platform (UJMP) - Backend

Django REST Framework backend for the Unified Journal Management Platform.

## Features

- **Multi-journal support**: Manage multiple journals in a single platform
- **Role-based access control**: Author, Reviewer, Admin roles
- **Strict workflow state machine**: Enforced article lifecycle transitions
- **Payment integration**: Payme and Click payment providers
- **Certificate system**: PDF certificate generation with QR codes
- **Audit logging**: Complete audit trail of all critical actions

## Technology Stack

- Python 3.12
- Django 4.x
- Django REST Framework
- PostgreSQL
- Celery + Redis (background jobs)
- ReportLab (PDF generation)
- MinIO/S3 (file storage)

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
- Strict workflow state machine
- Status transitions enforced by role
- Business rules:
  - Payment required before publication
  - Certificate only after publication

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

Article workflow states (from `tz.md`):

- `DRAFT` → `SUBMITTED` → `DESK_CHECK` → `UNDER_REVIEW`
- `REVISION_REQUIRED` → `REVISED_SUBMITTED` → `UNDER_REVIEW`
- `ACCEPTED` → `PAYMENT_PENDING` → `PAID` → `PRODUCTION` → `PUBLISHED`
- `PUBLISHED` → `CERTIFICATE_ISSUED`
- `REJECTED` → `ARCHIVED`

## Business Rules

1. **Payment before publication**: Articles cannot be published unless payment status is `PAID`
2. **Certificate after publication**: Certificates can only be issued for published articles
3. **Strict state transitions**: Only allowed transitions are permitted based on user role
4. **Audit logging**: All critical actions are logged

## API Endpoints

API endpoints will be implemented in subsequent phases. Base URLs:

- `/api/auth/` - Authentication
- `/api/journals/` - Journal management
- `/api/articles/` - Article management
- `/api/payments/` - Payment processing
- `/api/certificates/` - Certificate management
- `/api/audit/` - Audit logs
- `/verify/certificate/` - Public certificate verification

## Development

### Running Celery

```bash
celery -A ujmp worker -l info
celery -A ujmp beat -l info  # For scheduled tasks
```

### Running Tests

```bash
python manage.py test
```

## Documentation

See `doc/` directory for:
- `requirements.md` - Functional requirements
- `design.md` - UI/UX design specifications
- `tasks.md` - Development roadmap
- `tz.md` - Technical specification

## License

[To be determined]

