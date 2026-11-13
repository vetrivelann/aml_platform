from fastapi import HTTPException

from backend.auth import create_access_token, decode_access_token
from backend.dependencies import require_roles


print("=" * 60)
print("RBAC SECURITY TEST")
print("=" * 60)


# ============================================================
# TEST USERS
# ============================================================

admin_user = {
    "user_id": "USR_SECURITY_ADMIN",
    "username": "security_admin",
    "role": "ADMIN",
    "is_active": True
}

manager_user = {
    "user_id": "USR_SECURITY_MANAGER",
    "username": "security_manager",
    "role": "MANAGER",
    "is_active": True
}

analyst_user = {
    "user_id": "USR_SECURITY_ANALYST",
    "username": "security_analyst",
    "role": "ANALYST",
    "is_active": True
}

viewer_user = {
    "user_id": "USR_SECURITY_VIEWER",
    "username": "security_viewer",
    "role": "VIEWER",
    "is_active": True
}


# ============================================================
# 1. TOKEN CREATION TEST
# ============================================================

print("\nADMIN token created:", end=" ")

admin_token = create_access_token(
    user_id=admin_user["user_id"],
    username=admin_user["username"],
    role=admin_user["role"]
)

print(bool(admin_token))

if admin_token:
    print("PASS")
else:
    print("FAIL")


print("\nMANAGER token created:", end=" ")

manager_token = create_access_token(
    user_id=manager_user["user_id"],
    username=manager_user["username"],
    role=manager_user["role"]
)

print(bool(manager_token))

if manager_token:
    print("PASS")
else:
    print("FAIL")


print("\nANALYST token created:", end=" ")

analyst_token = create_access_token(
    user_id=analyst_user["user_id"],
    username=analyst_user["username"],
    role=analyst_user["role"]
)

print(bool(analyst_token))

if analyst_token:
    print("PASS")
else:
    print("FAIL")


print("\nVIEWER token created:", end=" ")

viewer_token = create_access_token(
    user_id=viewer_user["user_id"],
    username=viewer_user["username"],
    role=viewer_user["role"]
)

print(bool(viewer_token))

if viewer_token:
    print("PASS")
else:
    print("FAIL")


# ============================================================
# 2. TOKEN DECODING TEST
# ============================================================

print("\n" + "-" * 60)
print("TOKEN DECODING TEST")
print("-" * 60)


admin_payload = decode_access_token(admin_token)

print("\nADMIN payload:")
print(admin_payload)

if (
    admin_payload
    and admin_payload.get("sub") == admin_user["user_id"]
    and admin_payload.get("username") == admin_user["username"]
    and admin_payload.get("role") == admin_user["role"]
):
    print("PASS")
else:
    print("FAIL")


manager_payload = decode_access_token(manager_token)

print("\nMANAGER payload:")
print(manager_payload)

if (
    manager_payload
    and manager_payload.get("sub") == manager_user["user_id"]
    and manager_payload.get("username") == manager_user["username"]
    and manager_payload.get("role") == manager_user["role"]
):
    print("PASS")
else:
    print("FAIL")


analyst_payload = decode_access_token(analyst_token)

print("\nANALYST payload:")
print(analyst_payload)

if (
    analyst_payload
    and analyst_payload.get("sub") == analyst_user["user_id"]
    and analyst_payload.get("username") == analyst_user["username"]
    and analyst_payload.get("role") == analyst_user["role"]
):
    print("PASS")
else:
    print("FAIL")


viewer_payload = decode_access_token(viewer_token)

print("\nVIEWER payload:")
print(viewer_payload)

if (
    viewer_payload
    and viewer_payload.get("sub") == viewer_user["user_id"]
    and viewer_payload.get("username") == viewer_user["username"]
    and viewer_payload.get("role") == viewer_user["role"]
):
    print("PASS")
else:
    print("FAIL")


# ============================================================
# 3. ROLE AUTHORIZATION MATRIX TEST
# ============================================================

print("\n" + "-" * 60)
print("ROLE AUTHORIZATION TEST")
print("-" * 60)


role_permissions = {
    "READ_DATA": [
        "ADMIN",
        "MANAGER",
        "ANALYST",
        "VIEWER"
    ],

    "CREATE_TRANSACTION": [
        "ADMIN",
        "MANAGER",
        "ANALYST"
    ],

    "UPDATE_ALERT": [
        "ADMIN",
        "MANAGER",
        "ANALYST"
    ],

    "CREATE_CASE": [
        "ADMIN",
        "MANAGER",
        "ANALYST"
    ],

    "UPDATE_CASE": [
        "ADMIN",
        "MANAGER",
        "ANALYST"
    ],

    "VIEW_CASE": [
        "ADMIN",
        "MANAGER",
        "ANALYST",
        "VIEWER"
    ]
}


all_users = [
    admin_user,
    manager_user,
    analyst_user,
    viewer_user
]


for permission, allowed_roles in role_permissions.items():

    print(f"\nPermission: {permission}")
    print(
        "Allowed roles: "
        + ", ".join(allowed_roles)
    )

    for user in all_users:

        if user["role"] in allowed_roles:
            result = "ALLOWED"
        else:
            result = "DENIED"

        print(
            f"  {user['role']:<8} -> {result}"
        )


# ============================================================
# 4. require_roles() FUNCTION TEST
# ============================================================

print("\n" + "-" * 60)
print("require_roles() FUNCTION TEST")
print("-" * 60)


# ------------------------------------------------------------
# ANALYST ACCESS TEST
# ------------------------------------------------------------

print("\nANALYST access to analyst endpoint:")

analyst_checker = require_roles("ANALYST")

try:

    result = analyst_checker(
        current_user=analyst_user
    )

    print(result)

    if (
        result["user_id"] == analyst_user["user_id"]
        and result["username"] == analyst_user["username"]
        and result["role"] == "ANALYST"
        and result["is_active"] is True
    ):
        print("PASS")
    else:
        print("FAIL")

except Exception as e:

    print("ANALYST access failed:")
    print(e)
    print("FAIL")


# ------------------------------------------------------------
# VIEWER DENIAL TEST
# ------------------------------------------------------------

print("\nVIEWER access to analyst endpoint:")

viewer_checker = require_roles("ANALYST")

try:

    viewer_checker(
        current_user=viewer_user
    )

    print(
        "FAIL - VIEWER was incorrectly allowed"
    )

except HTTPException as e:

    if e.status_code == 403:

        print("Access denied as expected")
        print("PASS")

    else:

        print(
            f"Unexpected HTTP status: {e.status_code}"
        )
        print("FAIL")


# ------------------------------------------------------------
# ADMIN ACCESS TEST
# ------------------------------------------------------------

print("\nADMIN access to admin endpoint:")

admin_checker = require_roles("ADMIN")

try:

    result = admin_checker(
        current_user=admin_user
    )

    print(result)

    if result["role"] == "ADMIN":
        print("PASS")
    else:
        print("FAIL")

except Exception as e:

    print("ADMIN access failed:")
    print(e)
    print("FAIL")


# ------------------------------------------------------------
# MANAGER ACCESS TEST
# ------------------------------------------------------------

print("\nMANAGER access to manager endpoint:")

manager_checker = require_roles("MANAGER")

try:

    result = manager_checker(
        current_user=manager_user
    )

    print(result)

    if result["role"] == "MANAGER":
        print("PASS")
    else:
        print("FAIL")

except Exception as e:

    print("MANAGER access failed:")
    print(e)
    print("FAIL")


# ------------------------------------------------------------
# VIEWER ACCESS TO VIEWER-ALLOWED ENDPOINT
# ------------------------------------------------------------

print("\nVIEWER access to viewer-allowed endpoint:")

viewer_allowed_checker = require_roles(
    "ADMIN",
    "MANAGER",
    "ANALYST",
    "VIEWER"
)

try:

    result = viewer_allowed_checker(
        current_user=viewer_user
    )

    print(result)

    if result["role"] == "VIEWER":
        print("PASS")
    else:
        print("FAIL")

except Exception as e:

    print("VIEWER access failed:")
    print(e)
    print("FAIL")


# ============================================================
# 5. CROSS-ROLE DENIAL TEST
# ============================================================

print("\n" + "-" * 60)
print("CROSS-ROLE DENIAL TEST")
print("-" * 60)


# Viewer trying to access ADMIN endpoint
print("\nVIEWER -> ADMIN endpoint:")

admin_checker = require_roles("ADMIN")

try:

    admin_checker(
        current_user=viewer_user
    )

    print("FAIL - VIEWER was allowed")

except HTTPException as e:

    if e.status_code == 403:
        print("Access denied as expected")
        print("PASS")
    else:
        print("FAIL")


# Analyst trying to access ADMIN endpoint
print("\nANALYST -> ADMIN endpoint:")

try:

    admin_checker(
        current_user=analyst_user
    )

    print("FAIL - ANALYST was allowed")

except HTTPException as e:

    if e.status_code == 403:
        print("Access denied as expected")
        print("PASS")
    else:
        print("FAIL")


# Viewer trying to update case
print("\nVIEWER -> UPDATE_CASE endpoint:")

update_case_checker = require_roles(
    "ADMIN",
    "MANAGER",
    "ANALYST"
)

try:

    update_case_checker(
        current_user=viewer_user
    )

    print("FAIL - VIEWER was allowed")

except HTTPException as e:

    if e.status_code == 403:
        print("Access denied as expected")
        print("PASS")
    else:
        print("FAIL")


# ============================================================
# 6. INVALID TOKEN TEST
# ============================================================

print("\n" + "-" * 60)
print("INVALID TOKEN TEST")
print("-" * 60)


invalid_token = "this_is_an_invalid_token"

invalid_result = decode_access_token(
    invalid_token
)

print("\nInvalid token result:")
print(invalid_result)

if invalid_result is None:
    print("PASS")
else:
    print("FAIL")


# ============================================================
# COMPLETED
# ============================================================

print("\n" + "=" * 60)
print("RBAC SECURITY TEST COMPLETED")
print("=" * 60)