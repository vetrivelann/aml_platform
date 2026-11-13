from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import text

from backend.database import engine
from backend.auth import hash_password, verify_password


# ============================================================
# CREATE USERS TABLE
# ============================================================

def create_users_table():

    with engine.begin() as connection:

        connection.execute(
            text("""
                CREATE TABLE IF NOT EXISTS users (

                    user_id VARCHAR(50) PRIMARY KEY,

                    username VARCHAR(50)
                    UNIQUE NOT NULL,

                    password_hash TEXT NOT NULL,

                    role VARCHAR(20)
                    NOT NULL DEFAULT 'ANALYST',

                    is_active BOOLEAN
                    NOT NULL DEFAULT TRUE,

                    created_at TIMESTAMP WITH TIME ZONE
                    NOT NULL
                )
            """)
        )


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    username: str,
    password: str,
    role: str = "ANALYST"
):

    allowed_roles = {
        "ADMIN",
        "MANAGER",
        "ANALYST",
        "VIEWER",
        "USER"
    }

    role = role.upper()

    if role not in allowed_roles:
        raise ValueError(
            f"Invalid role. Allowed roles: {allowed_roles}"
        )

    create_users_table()

    user_id = (
        f"USR_{uuid4().hex[:10].upper()}"
    )

    password_hash = hash_password(password)

    created_at = datetime.now(timezone.utc)

    with engine.begin() as connection:

        existing_user = connection.execute(
            text("""
                SELECT user_id
                FROM users
                WHERE username = :username
            """),
            {
                "username": username
            }
        ).first()

        if existing_user:

            raise ValueError(
                "Username already exists"
            )

        connection.execute(
            text("""
                INSERT INTO users (
                    user_id,
                    username,
                    password_hash,
                    role,
                    is_active,
                    created_at
                )
                VALUES (
                    :user_id,
                    :username,
                    :password_hash,
                    :role,
                    :is_active,
                    :created_at
                )
            """),
            {
                "user_id": user_id,
                "username": username,
                "password_hash": password_hash,
                "role": role,
                "is_active": True,
                "created_at": created_at
            }
        )

    return {
        "user_id": user_id,
        "username": username,
        "role": role,
        "is_active": True
    }


# ============================================================
# AUTHENTICATE USER
# ============================================================

def authenticate_user(
    username: str,
    password: str
):

    create_users_table()

    with engine.connect() as connection:

        user = connection.execute(
            text("""
                SELECT
                    user_id,
                    username,
                    password_hash,
                    role,
                    is_active

                FROM users

                WHERE username = :username
            """),
            {
                "username": username
            }
        ).mappings().first()

    if not user:

        return None

    if not user["is_active"]:

        return None

    if not verify_password(
        password,
        user["password_hash"]
    ):

        return None

    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "is_active": user["is_active"]
    }


# ============================================================
# GET USER
# ============================================================

def get_user_by_id(user_id: str):

    create_users_table()

    with engine.connect() as connection:

        user = connection.execute(
            text("""
                SELECT
                    user_id,
                    username,
                    role,
                    is_active,
                    created_at

                FROM users

                WHERE user_id = :user_id
            """),
            {
                "user_id": user_id
            }
        ).mappings().first()

    if not user:
        return None

    return dict(user)