# Changelog

All notable changes to the UJMP Backend project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2025-12-26

### 🎉 Initial Release - Production Ready

### Added

#### Core Features
- **Dual Lifecycle Architecture**: Separated scientific workflow (`Article.status`) from business workflow (`Article.payment_status`)
- **Payment Status Field**: New `payment_status` field on Article model (NONE, PENDING, PAID, NOT_REQUIRED)
- **Payment Gates**: Enforced payment status checks before production and publishing
- **Auto-transitions**: Automatic workflow transitions (submission → desk check, revision → review)

#### Admin Panel
- **Modern UI**: Integrated django-jazzmin for modern admin interface
- **Workflow Actions**: Superadmin-only workflow actions in admin panel
  - Send to review
  - Request revision
  - Accept/Reject articles
  - Move to production
  - Publish articles
- **Payment Status Display**: Separate display for scientific vs business workflow
- **Inline Admins**: Versions, reviews, and payments displayed inline

#### API Documentation
- **OpenAPI/Swagger**: Complete auto-generated API documentation
- **Enum Naming**: Fixed enum naming collisions in OpenAPI schema
- **Type Hints**: Added type hints to all serializer methods
- **Webhook Schemas**: Added serializers for webhook endpoints
- **Certificate Schema**: Fixed certificate verification endpoint schema

#### Security
- **Superadmin Restrictions**: Workflow actions restricted to superadmins only
- **Rate Limiting**: Comprehensive rate limiting for all endpoints
- **Webhook Security**: IP whitelisting and signature verification
- **Security Headers**: XSS, CSRF, HSTS protection

### Changed

#### Workflow Refactoring
- **Payment Separation**: Payment operations no longer modify `Article.status`
- **Invoice Creation**: Invoice created only when article is ACCEPTED
- **Payment Gates**: `move_to_production` and `publish` require `payment_status = PAID` or `NOT_REQUIRED`
- **Revision Flow**: Auto-transition from REVISION_REQUIRED to UNDER_REVIEW after revision upload

#### Role Permissions
- **ADMIN**: All workflow actions, final accept/reject, publishing
- **REVIEWER**: Request revisions (from UNDER_REVIEW only), submit recommendations
- **AUTHOR**: Submit articles, upload manuscripts/revisions

#### Technology Stack
- **Django**: Upgraded to 5.x (from 4.x)
- **Python**: Updated to 3.14 (from 3.12)

### Fixed

- **Enum Naming Collisions**: Resolved OpenAPI enum naming warnings
- **Serializer Type Hints**: Added type hints to all serializer methods
- **Webhook Serializers**: Added missing serializers for webhook views
- **Certificate Schema**: Fixed certificate verification endpoint schema
- **Admin Actions**: Restricted workflow actions to superadmins only

### Documentation

- **README.md**: Updated with dual lifecycle architecture, admin panel features, and latest technology stack
- **PROJECT_COMPLETION.md**: Comprehensive project completion summary
- **CHANGELOG.md**: This file
- **API Contract**: Already frozen in `api_contract.md`

---

## Migration Notes

### Database Migration Required

After pulling this version, run:

```bash
python manage.py migrate articles
```

This applies the migration that adds the `payment_status` field to the `Article` model.

### Admin Panel Changes

- Workflow actions are now only visible to superadmins
- Payment status is displayed separately from article status
- Inline admins show related data (versions, reviews, payments)

### API Changes

- `Article` responses now include `payment_status` field
- Payment operations (`initiate_payment`, `mark_as_paid`) no longer modify `Article.status`
- `move_to_production` and `publish` actions now enforce payment gates

---

## Breaking Changes

None. All changes are backward compatible.

---

## Deprecated

- `PAYMENT_PENDING` and `PAID` as `Article.status` values (legacy, not used in active workflow)
- These values remain in the enum for backward compatibility but are not used in transitions

---

## Security

- Workflow actions in admin panel restricted to superadmins
- All security measures from previous versions remain in place
- Enhanced webhook security with IP whitelisting

---

**For detailed API changes, see `api_contract.md` (frozen contract).**

