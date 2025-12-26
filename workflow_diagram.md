# Article Workflow - Role Mapping Diagram

## State Diagram View

```mermaid
stateDiagram-v2
    [*] --> DRAFT
    
    DRAFT --> SUBMITTED: AUTHOR<br/>(Submit Article)
    
    SUBMITTED --> DESK_CHECK: SYSTEM<br/>(Auto-transition)
    SUBMITTED --> REJECTED: ADMIN<br/>(Desk Reject)
    
    DESK_CHECK --> UNDER_REVIEW: ADMIN<br/>(Send to Review)
    DESK_CHECK --> REJECTED: ADMIN<br/>(Desk Reject)
    
    UNDER_REVIEW --> REVISION_REQUIRED: REVIEWER, ADMIN<br/>(Request Revision)
    UNDER_REVIEW --> ACCEPTED: ADMIN<br/>(Accept Article)
    UNDER_REVIEW --> REJECTED: ADMIN<br/>(Reject Article)
    
    REVISION_REQUIRED --> UNDER_REVIEW: SYSTEM<br/>(Auto: After Revision Upload)
    
    ACCEPTED --> PAYMENT_PENDING: SYSTEM<br/>(Auto: APC Enabled)
    ACCEPTED --> PAID: SYSTEM<br/>(Auto: No APC)
    
    PAYMENT_PENDING --> PAID: SYSTEM, ADMIN<br/>(Payment Webhook / Admin Override)
    PAYMENT_PENDING --> REJECTED: ADMIN<br/>(Admin Reject)
    
    PAID --> PRODUCTION: REVIEWER<br/>(Move to Production)
    
    PRODUCTION --> SCHEDULED: REVIEWER<br/>(Schedule Publication)
    PRODUCTION --> PUBLISHED: REVIEWER<br/>(Publish Immediately)
    
    SCHEDULED --> PUBLISHED: REVIEWER, SYSTEM<br/>(Publish / Auto-publish)
    
    PUBLISHED --> CERTIFICATE_ISSUED: SYSTEM<br/>(Auto: Issue Certificate)
    
    REJECTED --> ARCHIVED: ADMIN<br/>(Archive)
    
    CERTIFICATE_ISSUED --> [*]
    ARCHIVED --> [*]
    
    note right of DRAFT
        Author creates article
        and uploads manuscript
    end note
    
    note right of DESK_CHECK
        Reviewer performs
        initial desk check
    end note
    
    note right of PAYMENT_PENDING
        Author pays APC
        via payment gateway
    end note
    
    note right of CERTIFICATE_ISSUED
        Terminal State
        (No further transitions)
    end note
    
    note right of ARCHIVED
        Terminal State
        (No further transitions)
    end note
```

## Flowchart View (Alternative)

```mermaid
flowchart TD
    Start([Article Created]) --> DRAFT[DRAFT]
    
    DRAFT -->|AUTHOR: Submit| SUBMITTED[SUBMITTED]
    SUBMITTED -->|SYSTEM: Auto| DESK_CHECK[DESK_CHECK]
    SUBMITTED -->|REVIEWER: Desk Reject| REJECTED[REJECTED]
    
    DESK_CHECK -->|ADMIN: Send to Review| UNDER_REVIEW[UNDER_REVIEW]
    DESK_CHECK -->|ADMIN: Desk Reject| REJECTED
    
    UNDER_REVIEW -->|REVIEWER/ADMIN: Request Revision| REVISION_REQUIRED[REVISION_REQUIRED]
    UNDER_REVIEW -->|ADMIN: Accept| ACCEPTED[ACCEPTED]
    UNDER_REVIEW -->|ADMIN: Reject| REJECTED
    
    REVISION_REQUIRED -.->|AUTHOR: Upload Revision<br/>SYSTEM: Auto| UNDER_REVIEW
    
    ACCEPTED -->|SYSTEM: APC Enabled| PAYMENT_PENDING[PAYMENT_PENDING]
    ACCEPTED -->|SYSTEM: No APC| PAID[PAID]
    
    PAYMENT_PENDING -->|SYSTEM/ADMIN: Payment| PAID
    PAYMENT_PENDING -->|ADMIN: Reject| REJECTED
    
    PAID -->|ADMIN: Move to Production| PRODUCTION[PRODUCTION]
    PRODUCTION -->|ADMIN: Schedule| SCHEDULED[SCHEDULED]
    PRODUCTION -->|ADMIN: Publish| PUBLISHED[PUBLISHED]
    SCHEDULED -->|ADMIN/SYSTEM: Publish| PUBLISHED
    
    PUBLISHED -->|SYSTEM: Auto| CERTIFICATE_ISSUED[CERTIFICATE_ISSUED]
    REJECTED -->|ADMIN: Archive| ARCHIVED[ARCHIVED]
    
    CERTIFICATE_ISSUED --> End1([Terminal])
    ARCHIVED --> End2([Terminal])
    
    style DRAFT fill:#e1f5ff
    style SUBMITTED fill:#fff4e1
    style DESK_CHECK fill:#fff4e1
    style UNDER_REVIEW fill:#fff4e1
    style REVISION_REQUIRED fill:#ffe1f5
    style ACCEPTED fill:#e1ffe1
    style PAYMENT_PENDING fill:#ffe1e1
    style PAID fill:#e1ffe1
    style PRODUCTION fill:#e1ffe1
    style SCHEDULED fill:#e1ffe1
    style PUBLISHED fill:#e1ffe1
    style CERTIFICATE_ISSUED fill:#d4edda
    style REJECTED fill:#f8d7da
    style ARCHIVED fill:#f8d7da
```

## Role Legend

- **AUTHOR**: Can create articles, submit, and upload revisions
- **REVIEWER**: Can request revisions from UNDER_REVIEW status and submit review recommendations
- **ADMIN**: Editorial authority - can send to review, accept/reject articles, manage production, and publish
- **SYSTEM**: Automatic transitions handled by backend logic

## Key Workflow Paths

### Main Publication Path
```
DRAFT → SUBMITTED → DESK_CHECK → UNDER_REVIEW → ACCEPTED → 
PAYMENT_PENDING → PAID → PRODUCTION → PUBLISHED → CERTIFICATE_ISSUED
```

### Revision Path
```
UNDER_REVIEW → REVISION_REQUIRED → (upload_revision) → UNDER_REVIEW (automatic)
```

### Rejection Path
```
Any State → REJECTED → ARCHIVED
```

## Auto-Transitions (SYSTEM)

1. **SUBMITTED → DESK_CHECK**: Automatically transitions when author submits
2. **REVISION_REQUIRED → UNDER_REVIEW**: Automatically transitions after author uploads revision
3. **ACCEPTED → PAYMENT_PENDING/PAID**: Automatically transitions based on journal APC settings
4. **PUBLISHED → CERTIFICATE_ISSUED**: Automatically issues certificate after publication

