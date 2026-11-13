from uuid import uuid4

from sqlalchemy import text

from backend.database import engine


# ============================================================
# AUTOMATIC AML ALERT NOTIFICATION
# ============================================================

def create_aml_alert_notification(alert):
    """
    Automatically creates a notification for HIGH or CRITICAL AML alerts.

    This function is intentionally independent from the existing
    notification API so the current notification module is not affected.
    """

    # --------------------------------------------------------
    # Validate alert
    # --------------------------------------------------------

    if not alert:
        return None

    severity = str(
        alert.get("severity", "")
    ).upper()

    risk_score = float(
        alert.get("risk_score", 0)
    )

    # --------------------------------------------------------
    # Only notify for HIGH / CRITICAL alerts
    # --------------------------------------------------------

    if severity not in ["HIGH", "CRITICAL"] and risk_score < 70:
        return None

    # --------------------------------------------------------
    # Determine notification priority
    # --------------------------------------------------------

    if severity == "CRITICAL" or risk_score >= 90:
        priority = "CRITICAL"

    else:
        priority = "HIGH"

    # --------------------------------------------------------
    # Generate notification ID
    # --------------------------------------------------------

    notification_id = (
        f"NOTIF_{uuid4().hex[:10].upper()}"
    )

    # --------------------------------------------------------
    # Notification content
    # --------------------------------------------------------

    subject = (
        f"{severity} AML Alert Requires Review"
    )

    message = (
        f"AML alert {alert.get('alert_id')} "
        f"was generated for transaction "
        f"{alert.get('transaction_id')}. "
        f"Alert type: {alert.get('alert_type')}. "
        f"Risk score: {risk_score}. "
        f"Severity: {severity}. "
        f"Analyst review is required."
    )

    # --------------------------------------------------------
    # Insert notification
    # --------------------------------------------------------

    insert_sql = text("""
        INSERT INTO notifications (
            notification_id,
            notification_type,
            recipient,
            subject,
            message,
            priority,
            status,
            created_at
        )
        VALUES (
            :notification_id,
            :notification_type,
            :recipient,
            :subject,
            :message,
            :priority,
            :status,
            CURRENT_TIMESTAMP
        )
        RETURNING
            notification_id,
            notification_type,
            recipient,
            subject,
            message,
            priority,
            status,
            created_at
    """)

    try:

        with engine.begin() as connection:

            result = connection.execute(
                insert_sql,
                {
                    "notification_id":
                        notification_id,

                    "notification_type":
                        "AML_ALERT",

                    "recipient":
                        "AML_ANALYST_01",

                    "subject":
                        subject,

                    "message":
                        message,

                    "priority":
                        priority,

                    "status":
                        "PENDING"
                }
            ).mappings().first()

        if not result:
            return None

        return dict(result)

    except Exception as e:

        # Notification failure must NOT break
        # the AML transaction/alert processing.

        print(
            f"WARNING: AML notification creation failed: {e}"
        )

        return None