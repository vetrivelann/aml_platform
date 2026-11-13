from fastapi.testclient import TestClient
from unittest.mock import patch

from backend.main import app
from backend.auth import create_access_token


print("=" * 60)
print("FASTAPI ENDPOINT SECURITY TEST")
print("=" * 60)


# ============================================================
# TEST CLIENT
# ============================================================

client = TestClient(app)


# ============================================================
# TEST USERS
# ============================================================

USERS = {
    "ADMIN": {
        "user_id": "USR_ENDPOINT_ADMIN",
        "username": "endpoint_admin",
        "role": "ADMIN",
        "is_active": True
    },

    "MANAGER": {
        "user_id": "USR_ENDPOINT_MANAGER",
        "username": "endpoint_manager",
        "role": "MANAGER",
        "is_active": True
    },

    "ANALYST": {
        "user_id": "USR_ENDPOINT_ANALYST",
        "username": "endpoint_analyst",
        "role": "ANALYST",
        "is_active": True
    },

    "VIEWER": {
        "user_id": "USR_ENDPOINT_VIEWER",
        "username": "endpoint_viewer",
        "role": "VIEWER",
        "is_active": True
    }
}


# ============================================================
# CREATE JWT TOKENS
# ============================================================

TOKENS = {}

for role, user in USERS.items():

    TOKENS[role] = create_access_token(
        user_id=user["user_id"],
        username=user["username"],
        role=user["role"]
    )


# ============================================================
# MOCK USER LOOKUP
# ============================================================
#
# The real get_current_user() function checks the database
# using get_user_by_id().
#
# For endpoint security testing, we provide test users here
# so that the test does not require creating permanent users
# in PostgreSQL.
#
# ============================================================

def mock_get_user_by_id(user_id):

    for user in USERS.values():

        if user["user_id"] == user_id:
            return user

    return None


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def auth_headers(role):

    return {
        "Authorization": f"Bearer {TOKENS[role]}"
    }


def print_result(
    role,
    endpoint,
    response,
    expected
):

    print(
        f"{role:<8} -> "
        f"{endpoint:<45} "
        f"HTTP {response.status_code}"
    )

    if response.status_code == expected:
        print("           PASS")
        return True

    print(
        f"           FAIL "
        f"(Expected HTTP {expected})"
    )

    return False


def print_allowed_result(
    role,
    endpoint,
    response
):

    print(
        f"{role:<8} -> "
        f"{endpoint:<45} "
        f"HTTP {response.status_code}"
    )

    # For an authorized user, we only need to confirm
    # that authentication/authorization did not reject
    # the request.
    #
    # The endpoint may return:
    # 200 -> successful operation
    # 404 -> resource not found
    # 422 -> validation error
    # 400 -> business validation error
    #
    # All of these prove that RBAC allowed the request
    # to reach the endpoint.

    if response.status_code not in [401, 403]:

        print("           PASS")
        return True

    print("           FAIL - REQUEST WAS BLOCKED")
    return False


# ============================================================
# 1. NO TOKEN TEST
# ============================================================

print("\n" + "-" * 60)
print("1. NO TOKEN TEST")
print("-" * 60)

response = client.get(
    "/api/v1/alerts"
)

if response.status_code == 401:
    print("GET /api/v1/alerts without token")
    print("HTTP 401")
    print("PASS")
else:
    print(
        "FAIL - Expected HTTP 401, "
        f"got {response.status_code}"
    )


# ============================================================
# 2. INVALID TOKEN TEST
# ============================================================

print("\n" + "-" * 60)
print("2. INVALID TOKEN TEST")
print("-" * 60)

response = client.get(
    "/api/v1/alerts",
    headers={
        "Authorization": "Bearer invalid_token_123"
    }
)

if response.status_code == 401:
    print("GET /api/v1/alerts with invalid token")
    print("HTTP 401")
    print("PASS")
else:
    print(
        "FAIL - Expected HTTP 401, "
        f"got {response.status_code}"
    )


# ============================================================
# 3. READ DATA ENDPOINT
# ============================================================

print("\n" + "-" * 60)
print("3. READ DATA ENDPOINT")
print("-" * 60)

print("\nEndpoint:")
print("GET /api/v1/alerts")

with patch(
    "backend.dependencies.get_user_by_id",
    side_effect=mock_get_user_by_id
):

    for role in [
        "ADMIN",
        "MANAGER",
        "ANALYST",
        "VIEWER"
    ]:

        response = client.get(
            "/api/v1/alerts",
            headers=auth_headers(role)
        )

        print_allowed_result(
            role,
            "GET /api/v1/alerts",
            response
        )


# ============================================================
# 4. CREATE TRANSACTION ENDPOINT
# ============================================================

print("\n" + "-" * 60)
print("4. CREATE TRANSACTION ENDPOINT")
print("-" * 60)

print("\nEndpoint:")
print("POST /api/v1/transactions")

print("\nExpected:")
print("ADMIN    -> ALLOWED")
print("MANAGER  -> ALLOWED")
print("ANALYST  -> ALLOWED")
print("VIEWER   -> DENIED")


with patch(
    "backend.dependencies.get_user_by_id",
    side_effect=mock_get_user_by_id
):

    # ADMIN
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers("ADMIN"),
        json={}
    )

    print_allowed_result(
        "ADMIN",
        "POST /api/v1/transactions",
        response
    )

    # MANAGER
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers("MANAGER"),
        json={}
    )

    print_allowed_result(
        "MANAGER",
        "POST /api/v1/transactions",
        response
    )

    # ANALYST
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers("ANALYST"),
        json={}
    )

    print_allowed_result(
        "ANALYST",
        "POST /api/v1/transactions",
        response
    )

    # VIEWER
    response = client.post(
        "/api/v1/transactions",
        headers=auth_headers("VIEWER"),
        json={}
    )

    print_result(
        "VIEWER",
        "POST /api/v1/transactions",
        response,
        403
    )


# ============================================================
# 5. UPDATE ALERT ENDPOINT
# ============================================================

print("\n" + "-" * 60)
print("5. UPDATE ALERT ENDPOINT")
print("-" * 60)

print("\nEndpoint:")
print("PATCH /api/v1/alerts/TEST_ALERT/status")

print("\nExpected:")
print("ADMIN    -> ALLOWED")
print("MANAGER  -> ALLOWED")
print("ANALYST  -> DENIED")
print("VIEWER   -> DENIED")


alert_payload = {
    "status": "UNDER_REVIEW"
}


with patch(
    "backend.dependencies.get_user_by_id",
    side_effect=mock_get_user_by_id
):

    for role in [
        "ADMIN",
        "MANAGER"
    ]:

        response = client.patch(
            "/api/v1/alerts/TEST_ALERT/status",
            headers=auth_headers(role),
            json=alert_payload
        )

        print_allowed_result(
            role,
            "PATCH /api/v1/alerts/{id}/status",
            response
        )

    # ANALYST
    response = client.patch(
        "/api/v1/alerts/TEST_ALERT/status",
        headers=auth_headers("ANALYST"),
        json=alert_payload
    )

    print_result(
        "ANALYST",
        "PATCH /api/v1/alerts/{id}/status",
        response,
        403
    )

    # VIEWER
    response = client.patch(
        "/api/v1/alerts/TEST_ALERT/status",
        headers=auth_headers("VIEWER"),
        json=alert_payload
    )

    print_result(
        "VIEWER",
        "PATCH /api/v1/alerts/{id}/status",
        response,
        403
    )


# ============================================================
# 6. CREATE CASE ENDPOINT
# ============================================================

print("\n" + "-" * 60)
print("6. CREATE CASE ENDPOINT")
print("-" * 60)

print("\nEndpoint:")
print("POST /api/v1/cases")

print("\nExpected:")
print("ADMIN    -> ALLOWED")
print("MANAGER  -> ALLOWED")
print("ANALYST  -> ALLOWED")
print("VIEWER   -> DENIED")


case_payload = {
    "alert_id": "TEST_ALERT",
    "priority": "HIGH"
}


with patch(
    "backend.dependencies.get_user_by_id",
    side_effect=mock_get_user_by_id
):

    for role in [
        "ADMIN",
        "MANAGER",
        "ANALYST"
    ]:

        response = client.post(
            "/api/v1/cases",
            headers=auth_headers(role),
            json=case_payload
        )

        print_allowed_result(
            role,
            "POST /api/v1/cases",
            response
        )

    # VIEWER
    response = client.post(
        "/api/v1/cases",
        headers=auth_headers("VIEWER"),
        json=case_payload
    )

    print_result(
        "VIEWER",
        "POST /api/v1/cases",
        response,
        403
    )


# ============================================================
# 7. CASE VIEW ENDPOINT
# ============================================================

print("\n" + "-" * 60)
print("7. CASE VIEW ENDPOINT")
print("-" * 60)

print("\nEndpoint:")
print("GET /api/v1/cases/TEST_CASE")

print("\nExpected:")
print("ADMIN    -> ALLOWED")
print("MANAGER  -> ALLOWED")
print("ANALYST  -> ALLOWED")
print("VIEWER   -> ALLOWED")


with patch(
    "backend.dependencies.get_user_by_id",
    side_effect=mock_get_user_by_id
):

    for role in [
        "ADMIN",
        "MANAGER",
        "ANALYST",
        "VIEWER"
    ]:

        response = client.get(
            "/api/v1/cases/TEST_CASE",
            headers=auth_headers(role)
        )

        print_allowed_result(
            role,
            "GET /api/v1/cases/{id}",
            response
        )


# ============================================================
# 8. UPDATE CASE ENDPOINT
# ============================================================

print("\n" + "-" * 60)
print("8. UPDATE CASE ENDPOINT")
print("-" * 60)

print("\nEndpoint:")
print("PATCH /api/v1/cases/TEST_CASE")

print("\nExpected:")
print("ADMIN    -> ALLOWED")
print("MANAGER  -> ALLOWED")
print("ANALYST  -> DENIED")
print("VIEWER   -> DENIED")


case_update_payload = {
    "notes": "Endpoint security test"
}


with patch(
    "backend.dependencies.get_user_by_id",
    side_effect=mock_get_user_by_id
):

    for role in [
        "ADMIN",
        "MANAGER"
    ]:

        response = client.patch(
            "/api/v1/cases/TEST_CASE",
            headers=auth_headers(role),
            json=case_update_payload
        )

        print_allowed_result(
            role,
            "PATCH /api/v1/cases/{id}",
            response
        )

    # ANALYST
    response = client.patch(
        "/api/v1/cases/TEST_CASE",
        headers=auth_headers("ANALYST"),
        json=case_update_payload
    )

    print_result(
        "ANALYST",
        "PATCH /api/v1/cases/{id}",
        response,
        403
    )

    # VIEWER
    response = client.patch(
        "/api/v1/cases/TEST_CASE",
        headers=auth_headers("VIEWER"),
        json=case_update_payload
    )

    print_result(
        "VIEWER",
        "PATCH /api/v1/cases/{id}",
        response,
        403
    )


# ============================================================
# 9. CUSTOMER RISK ENDPOINT
# ============================================================

print("\n" + "-" * 60)
print("9. CUSTOMER RISK ENDPOINT")
print("-" * 60)

print("\nEndpoint:")
print("GET /api/v1/customers/CUST_0001/risk")

print("\nExpected:")
print("ADMIN    -> ALLOWED")
print("MANAGER  -> ALLOWED")
print("ANALYST  -> ALLOWED")
print("VIEWER   -> ALLOWED")


with patch(
    "backend.dependencies.get_user_by_id",
    side_effect=mock_get_user_by_id
):

    for role in [
        "ADMIN",
        "MANAGER",
        "ANALYST",
        "VIEWER"
    ]:

        response = client.get(
            "/api/v1/customers/CUST_0001/risk",
            headers=auth_headers(role)
        )

        print_allowed_result(
            role,
            "GET /api/v1/customers/{id}/risk",
            response
        )


# ============================================================
# 10. FINAL RESULT
# ============================================================

print("\n" + "=" * 60)
print("FASTAPI ENDPOINT SECURITY TEST COMPLETED")
print("=" * 60)