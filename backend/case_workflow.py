from datetime import datetime, timezone
from sqlalchemy import text

from backend.database import engine
from backend.audit import create_audit_log


# ============================================================
# CREATE CASE FROM ALERT
# ============================================================

def create_case_from_alert(
    alert_id: str,
    user_id: str | None = None,
    username: str | None = None,
    user_role: str | None = None
):

    with engine.begin() as connection:

        # ----------------------------------------------------
        # Check alert
        # ----------------------------------------------------

        alert = connection.execute(
            text("""
                SELECT
                    alert_id,
                    transaction_id,
                    alert_type,
                    severity,
                    risk_score,
                    status
                FROM alerts
                WHERE alert_id = :alert_id
            """),
            {
                "alert_id": alert_id
            }
        ).mappings().first()

        if not alert:
            return None

        # ----------------------------------------------------
        # Check whether case already exists
        # ----------------------------------------------------

        existing_case = connection.execute(
            text("""
                SELECT
                    case_id
                FROM cases
                WHERE alert_id = :alert_id
            """),
            {
                "alert_id": alert_id
            }
        ).mappings().first()

        if existing_case:

            return {
                "message": "Case already exists",
                "case_id": existing_case["case_id"]
            }

        # ----------------------------------------------------
        # Generate case ID
        # ----------------------------------------------------

        from uuid import uuid4

        case_id = (
            f"CASE_{uuid4().hex[:10].upper()}"
        )

        # ----------------------------------------------------
        # Determine priority
        # ----------------------------------------------------

        severity = str(
            alert["severity"]
        ).upper()

        if severity == "CRITICAL":
            priority = "CRITICAL"

        elif severity == "HIGH":
            priority = "HIGH"

        elif severity == "MEDIUM":
            priority = "MEDIUM"

        else:
            priority = "LOW"

        # ----------------------------------------------------
        # Insert case
        # ----------------------------------------------------

        connection.execute(
            text("""
                INSERT INTO cases (
                    case_id,
                    alert_id,
                    case_status,
                    priority,
                    assigned_to,
                    disposition,
                    notes,
                    created_at,
                    updated_at
                )
                VALUES (
                    :case_id,
                    :alert_id,
                    'OPEN',
                    :priority,
                    NULL,
                    NULL,
                    NULL,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                )
            """),
            {
                "case_id": case_id,
                "alert_id": alert_id,
                "priority": priority
            }
        )

    # --------------------------------------------------------
    # Audit case creation
    # --------------------------------------------------------

    try:

        create_audit_log(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action="CREATE_CASE",
            resource_type="CASE",
            resource_id=case_id,
            description=(
                f"Case created from AML alert "
                f"{alert_id}"
            ),
            ip_address=None
        )

    except Exception as e:

        print(
            f"WARNING: Case audit creation failed: {e}"
        )

    return {
        "case_id": case_id,
        "alert_id": alert_id,
        "case_status": "OPEN",
        "priority": priority,
        "assigned_to": None,
        "disposition": None,
        "notes": None
    }


# ============================================================
# ASSIGN CASE
# ============================================================

def assign_case(
    case_id: str,
    assigned_to: str,
    user_id: str | None = None,
    username: str | None = None,
    user_role: str | None = None
):

    with engine.begin() as connection:

        case = connection.execute(
            text("""
                SELECT case_id
                FROM cases
                WHERE case_id = :case_id
            """),
            {
                "case_id": case_id
            }
        ).mappings().first()

        if not case:
            return None

        connection.execute(
            text("""
                UPDATE cases
                SET
                    assigned_to = :assigned_to,
                    updated_at = CURRENT_TIMESTAMP
                WHERE case_id = :case_id
            """),
            {
                "case_id": case_id,
                "assigned_to": assigned_to
            }
        )

    # --------------------------------------------------------
    # Audit assignment
    # --------------------------------------------------------

    try:

        create_audit_log(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action="ASSIGN_CASE",
            resource_type="CASE",
            resource_id=case_id,
            description=(
                f"Case assigned to {assigned_to}"
            ),
            ip_address=None
        )

    except Exception as e:

        print(
            f"WARNING: Case assignment audit failed: {e}"
        )

    return {
        "case_id": case_id,
        "assigned_to": assigned_to
    }


# ============================================================
# UPDATE CASE DISPOSITION
# ============================================================

def update_case_disposition(
    case_id: str,
    disposition: str,
    notes: str | None = None,
    user_id: str | None = None,
    username: str | None = None,
    user_role: str | None = None
):

    allowed_dispositions = {
        "TRUE_POSITIVE",
        "FALSE_POSITIVE",
        "SUSPICIOUS",
        "NO_ACTION_REQUIRED",
        "ESCALATED"
    }

    disposition = disposition.upper()

    if disposition not in allowed_dispositions:

        raise ValueError(
            f"Invalid disposition. "
            f"Allowed values: {allowed_dispositions}"
        )

    with engine.begin() as connection:

        case = connection.execute(
            text("""
                SELECT case_id
                FROM cases
                WHERE case_id = :case_id
            """),
            {
                "case_id": case_id
            }
        ).mappings().first()

        if not case:
            return None

        connection.execute(
            text("""
                UPDATE cases
                SET
                    disposition = :disposition,
                    notes = :notes,
                    updated_at = CURRENT_TIMESTAMP
                WHERE case_id = :case_id
            """),
            {
                "case_id": case_id,
                "disposition": disposition,
                "notes": notes
            }
        )

    # --------------------------------------------------------
    # Audit disposition
    # --------------------------------------------------------

    try:

        create_audit_log(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action="UPDATE_CASE_DISPOSITION",
            resource_type="CASE",
            resource_id=case_id,
            description=(
                f"Case disposition updated to "
                f"{disposition}"
            ),
            ip_address=None
        )

    except Exception as e:

        print(
            f"WARNING: Case disposition audit failed: {e}"
        )

    return {
        "case_id": case_id,
        "disposition": disposition,
        "notes": notes
    }


# ============================================================
# CLOSE CASE
# ============================================================

def close_case(
    case_id: str,
    user_id: str | None = None,
    username: str | None = None,
    user_role: str | None = None
):

    with engine.begin() as connection:

        case = connection.execute(
            text("""
                SELECT
                    case_id,
                    disposition
                FROM cases
                WHERE case_id = :case_id
            """),
            {
                "case_id": case_id
            }
        ).mappings().first()

        if not case:
            return None

        if not case["disposition"]:

            raise ValueError(
                "Case cannot be closed without a disposition"
            )

        connection.execute(
            text("""
                UPDATE cases
                SET
                    case_status = 'CLOSED',
                    updated_at = CURRENT_TIMESTAMP
                WHERE case_id = :case_id
            """),
            {
                "case_id": case_id
            }
        )

    # --------------------------------------------------------
    # Audit closure
    # --------------------------------------------------------

    try:

        create_audit_log(
            user_id=user_id,
            username=username,
            user_role=user_role,
            action="CLOSE_CASE",
            resource_type="CASE",
            resource_id=case_id,
            description="AML case closed",
            ip_address=None
        )

    except Exception as e:

        print(
            f"WARNING: Case closure audit failed: {e}"
        )

    return {
        "case_id": case_id,
        "case_status": "CLOSED"
    }