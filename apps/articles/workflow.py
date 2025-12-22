"""
Article workflow state machine.

Enforces strict state transitions according to tz.md.
"""
from enum import Enum
from typing import Set, Dict, List


class ArticleStatus(Enum):
    """Article workflow states."""
    DRAFT = 'DRAFT'
    SUBMITTED = 'SUBMITTED'
    DESK_CHECK = 'DESK_CHECK'
    REVIEWERS_INVITED = 'REVIEWERS_INVITED'
    UNDER_REVIEW = 'UNDER_REVIEW'
    REVISION_REQUIRED = 'REVISION_REQUIRED'
    REVISED_SUBMITTED = 'REVISED_SUBMITTED'
    EDITOR_DECISION = 'EDITOR_DECISION'
    ACCEPTED = 'ACCEPTED'
    PAYMENT_PENDING = 'PAYMENT_PENDING'
    PAID = 'PAID'
    PRODUCTION = 'PRODUCTION'
    SCHEDULED = 'SCHEDULED'
    PUBLISHED = 'PUBLISHED'
    CERTIFICATE_ISSUED = 'CERTIFICATE_ISSUED'
    REJECTED = 'REJECTED'
    ARCHIVED = 'ARCHIVED'


# Allowed state transitions
# Format: {from_state: {to_state: [allowed_roles]}}
ALLOWED_TRANSITIONS: Dict[ArticleStatus, Dict[ArticleStatus, List[str]]] = {
    ArticleStatus.DRAFT: {
        ArticleStatus.SUBMITTED: ['AUTHOR'],
    },
    ArticleStatus.SUBMITTED: {
        ArticleStatus.DESK_CHECK: ['SYSTEM'],  # Auto-transition
        ArticleStatus.REJECTED: ['REVIEWER'],  # Desk reject
    },
    ArticleStatus.DESK_CHECK: {
        ArticleStatus.UNDER_REVIEW: ['REVIEWER'],
        ArticleStatus.REVISION_REQUIRED: ['REVIEWER'],
        ArticleStatus.REJECTED: ['REVIEWER'],  # Desk reject
    },
    ArticleStatus.UNDER_REVIEW: {
        ArticleStatus.REVISION_REQUIRED: ['REVIEWER'],
        ArticleStatus.ACCEPTED: ['REVIEWER'],
        ArticleStatus.REJECTED: ['REVIEWER'],
    },
    ArticleStatus.REVISION_REQUIRED: {
        ArticleStatus.REVISED_SUBMITTED: ['AUTHOR'],
    },
    ArticleStatus.REVISED_SUBMITTED: {
        ArticleStatus.UNDER_REVIEW: ['REVIEWER'],
        ArticleStatus.REJECTED: ['REVIEWER'],
    },
    ArticleStatus.ACCEPTED: {
        ArticleStatus.PAYMENT_PENDING: ['SYSTEM'],  # Auto-transition if APC enabled
        ArticleStatus.PAID: ['SYSTEM'],  # If no APC or admin override
    },
    ArticleStatus.PAYMENT_PENDING: {
        ArticleStatus.PAID: ['SYSTEM', 'ADMIN'],  # Webhook or admin override
        ArticleStatus.REJECTED: ['ADMIN'],  # Admin can reject even after acceptance
    },
    ArticleStatus.PAID: {
        ArticleStatus.PRODUCTION: ['REVIEWER'],
    },
    ArticleStatus.PRODUCTION: {
        ArticleStatus.SCHEDULED: ['REVIEWER'],
        ArticleStatus.PUBLISHED: ['REVIEWER'],
    },
    ArticleStatus.SCHEDULED: {
        ArticleStatus.PUBLISHED: ['REVIEWER', 'SYSTEM'],
    },
    ArticleStatus.PUBLISHED: {
        ArticleStatus.CERTIFICATE_ISSUED: ['SYSTEM'],  # Auto-transition
    },
    ArticleStatus.CERTIFICATE_ISSUED: {
        # Terminal state - no further transitions
    },
    ArticleStatus.REJECTED: {
        ArticleStatus.ARCHIVED: ['ADMIN'],
    },
    ArticleStatus.ARCHIVED: {
        # Terminal state
    },
}


def can_transition(
    from_status: ArticleStatus,
    to_status: ArticleStatus,
    user_role: str
) -> bool:
    """
    Check if a state transition is allowed for the given role.
    
    Args:
        from_status: Current article status
        to_status: Desired article status
        user_role: User role (AUTHOR, REVIEWER, ADMIN)
    
    Returns:
        True if transition is allowed, False otherwise
    """
    if from_status not in ALLOWED_TRANSITIONS:
        return False
    
    transitions = ALLOWED_TRANSITIONS[from_status]
    if to_status not in transitions:
        return False
    
    allowed_roles = transitions[to_status]
    
    # SYSTEM transitions are automatic (handled by backend logic)
    if 'SYSTEM' in allowed_roles:
        return True
    
    # Check user role
    return user_role in allowed_roles


def get_allowed_transitions(
    current_status: ArticleStatus,
    user_role: str
) -> List[ArticleStatus]:
    """
    Get list of allowed next states for the current status and user role.
    
    Args:
        current_status: Current article status
        user_role: User role
    
    Returns:
        List of allowed next statuses
    """
    if current_status not in ALLOWED_TRANSITIONS:
        return []
    
    allowed = []
    for next_status, roles in ALLOWED_TRANSITIONS[current_status].items():
        if 'SYSTEM' in roles or user_role in roles:
            allowed.append(next_status)
    
    return allowed


def is_terminal_state(status: ArticleStatus) -> bool:
    """Check if a status is terminal (no further transitions)."""
    return status in [
        ArticleStatus.CERTIFICATE_ISSUED,
        ArticleStatus.ARCHIVED
    ]


def requires_payment(status: ArticleStatus) -> bool:
    """Check if a status requires payment before proceeding."""
    return status == ArticleStatus.PAYMENT_PENDING


def can_publish(status: ArticleStatus, payment_status: str = None) -> bool:
    """
    Check if article can be published.
    
    Business rule: Payment must be PAID before publication.
    """
    if status != ArticleStatus.PAID and status != ArticleStatus.PRODUCTION:
        return False
    
    # Additional check: payment_status should be PAID
    if payment_status and payment_status != 'PAID':
        return False
    
    return True


def can_issue_certificate(status: ArticleStatus) -> bool:
    """
    Check if certificate can be issued.
    
    Business rule: Certificate only after publication.
    """
    return status == ArticleStatus.PUBLISHED

