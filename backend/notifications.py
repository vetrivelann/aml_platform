from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from backend.database import engine


# ============================================================
# CREATE NOTIFICATIONS TABLE
# ============================================================

def create_notifications_table():

    with engine.begin() as connection:

        connection.execute(
            text("""
                CREATE TABLE IF NOT EXISTS notifications (

                    notification_id VARCHAR(50)
                    PRIMARY KEY,

                    notification_type VARCHAR(50)
                    NOT NULL,

                    recipient VARCHAR(100)
                    NOT NULL,

                    subject VARCHAR(200)
                    NOT NULL,

                    message TEXT
                    NOT NULL,

                    priority VARCHAR(20)
                    NOT NULL DEFAULT 'MEDIUM',

                    status VARCHAR(20)
                    NOT NULL DEFAULT 'PENDING',

                    created_at TIMESTAMP WITH TIME ZONE
                    NOT NULL
                )
            """)
        )


# ============================================================
# CREATE NOTIFICATION
# ============================================================

def create_notification(
    notification_type: str,
    recipient: str,
    subject: str,
    message: str,
    priority: str = "MEDIUM"
):

    allowed_priorities = {
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    }

    priority = priority.upper()

    if priority not in allowed_priorities:

        raise ValueError(
            "Invalid priority. "
            f"Allowed values: {allowed_priorities}"
        )

    create_notifications_table()

    notification_id = (
        f"NOTIF_{uuid4().hex[:10].upper()}"
    )

    created_at = datetime.now(timezone.utc)

    with engine.begin() as connection:

        connection.execute(
            text("""
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
                    'PENDING',
                    :created_at
                )
            """),
            {
                "notification_id":
                    notification_id,

                "notification_type":
                    notification_type.upper(),

                "recipient":
                    recipient,

                "subject":
                    subject,

                "message":
                    message,

                "priority":
                    priority,

                "created_at":
                    created_at
            }
        )

    return {
        "notification_id":
            notification_id,

        "notification_type":
            notification_type.upper(),

        "recipient":
            recipient,

        "subject":
            subject,

        "message":
            message,

        "priority":
            priority,

        "status":
            "PENDING",

        "created_at":
            created_at.isoformat()
    }


# ============================================================
# GET ALL NOTIFICATIONS
# ============================================================

def get_notifications():

    create_notifications_table()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    notification_id,
                    notification_type,
                    recipient,
                    subject,
                    message,
                    priority,
                    status,
                    created_at

                FROM notifications

                ORDER BY created_at DESC
            """)
        ).mappings().all()

    notifications = []

    for row in result:

        notifications.append({

            "notification_id":
                row["notification_id"],

            "notification_type":
                row["notification_type"],

            "recipient":
                row["recipient"],

            "subject":
                row["subject"],

            "message":
                row["message"],

            "priority":
                row["priority"],

            "status":
                row["status"],

            "created_at":
                (
                    row["created_at"].isoformat()
                    if row["created_at"]
                    else None
                )
        })

    return notifications


# ============================================================
# GET NOTIFICATION BY ID
# ============================================================

def get_notification_by_id(
    notification_id: str
):

    create_notifications_table()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    notification_id,
                    notification_type,
                    recipient,
                    subject,
                    message,
                    priority,
                    status,
                    created_at

                FROM notifications

                WHERE notification_id =
                    :notification_id
            """),
            {
                "notification_id":
                    notification_id
            }
        ).mappings().first()

    if not result:
        return None

    return {

        "notification_id":
            result["notification_id"],

        "notification_type":
            result["notification_type"],

        "recipient":
            result["recipient"],

        "subject":
            result["subject"],

        "message":
            result["message"],

        "priority":
            result["priority"],

        "status":
            result["status"],

        "created_at":
            (
                result["created_at"].isoformat()
                if result["created_at"]
                else None
            )
    }


# ============================================================
# UPDATE NOTIFICATION STATUS
# ============================================================

def update_notification_status(
    notification_id: str,
    status: str
):

    allowed_statuses = {
        "PENDING",
        "SENT",
        "FAILED",
        "READ"
    }

    status = status.upper()

    if status not in allowed_statuses:

        raise ValueError(
            "Invalid notification status. "
            f"Allowed values: {allowed_statuses}"
        )

    create_notifications_table()

    with engine.begin() as connection:

        result = connection.execute(
            text("""
                UPDATE notifications

                SET status = :status

                WHERE notification_id =
                    :notification_id

                RETURNING
                    notification_id,
                    notification_type,
                    recipient,
                    subject,
                    message,
                    priority,
                    status,
                    created_at
            """),
            {
                "notification_id":
                    notification_id,

                "status":
                    status
            }
        ).mappings().first()

    if not result:
        return None

    return {

        "notification_id":
            result["notification_id"],

        "notification_type":
            result["notification_type"],

        "recipient":
            result["recipient"],

        "subject":
            result["subject"],

        "message":
            result["message"],

        "priority":
            result["priority"],

        "status":
            result["status"],

        "created_at":
            (
                result["created_at"].isoformat()
                if result["created_at"]
                else None
            )
    }