from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from backend.database import engine


# ============================================================
# AUDIT TABLE
# ============================================================

def create_audit_table():

    with engine.begin() as connection:

        connection.execute(
            text("""
                CREATE TABLE IF NOT EXISTS audit_logs (

                    audit_id VARCHAR(50) PRIMARY KEY,

                    user_id VARCHAR(50),

                    username VARCHAR(50),

                    user_role VARCHAR(20),

                    action VARCHAR(100) NOT NULL,

                    resource_type VARCHAR(50),

                    resource_id VARCHAR(100),

                    description TEXT,

                    ip_address VARCHAR(100),

                    created_at TIMESTAMP WITH TIME ZONE
                    NOT NULL
                )
            """)
        )


# ============================================================
# CREATE AUDIT LOG
# ============================================================

def create_audit_log(
    user_id: str | None,
    username: str | None,
    user_role: str | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    description: str | None = None,
    ip_address: str | None = None
):

    create_audit_table()

    audit_id = (
        f"AUD_{uuid4().hex[:10].upper()}"
    )

    created_at = datetime.now(timezone.utc)

    with engine.begin() as connection:

        connection.execute(
            text("""
                INSERT INTO audit_logs (
                    audit_id,
                    user_id,
                    username,
                    user_role,
                    action,
                    resource_type,
                    resource_id,
                    description,
                    ip_address,
                    created_at
                )

                VALUES (
                    :audit_id,
                    :user_id,
                    :username,
                    :user_role,
                    :action,
                    :resource_type,
                    :resource_id,
                    :description,
                    :ip_address,
                    :created_at
                )
            """),
            {
                "audit_id": audit_id,
                "user_id": user_id,
                "username": username,
                "user_role": user_role,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "description": description,
                "ip_address": ip_address,
                "created_at": created_at
            }
        )

    return {
        "audit_id": audit_id,
        "user_id": user_id,
        "username": username,
        "user_role": user_role,
        "action": action,
        "resource_type": resource_type,
        "resource_id": resource_id,
        "description": description,
        "ip_address": ip_address,
        "created_at": created_at
    }


# ============================================================
# GET AUDIT LOGS
# ============================================================

def get_audit_logs(
    limit: int = 100
):

    create_audit_table()

    limit = min(max(limit, 1), 500)

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    audit_id,
                    user_id,
                    username,
                    user_role,
                    action,
                    resource_type,
                    resource_id,
                    description,
                    ip_address,
                    created_at

                FROM audit_logs

                ORDER BY created_at DESC

                LIMIT :limit
            """),
            {
                "limit": limit
            }
        ).mappings().all()

    return [
        dict(row)
        for row in result
    ]


# ============================================================
# GET AUDIT LOG BY RESOURCE
# ============================================================

def get_audit_logs_by_resource(
    resource_type: str,
    resource_id: str
):

    create_audit_table()

    with engine.connect() as connection:

        result = connection.execute(
            text("""
                SELECT
                    audit_id,
                    user_id,
                    username,
                    user_role,
                    action,
                    resource_type,
                    resource_id,
                    description,
                    ip_address,
                    created_at

                FROM audit_logs

                WHERE resource_type = :resource_type

                AND resource_id = :resource_id

                ORDER BY created_at DESC
            """),
            {
                "resource_type": resource_type,
                "resource_id": resource_id
            }
        ).mappings().all()

    return [
        dict(row)
        for row in result
    ]