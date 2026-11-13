from backend.dependencies import require_roles
from backend.auth import create_access_token, decode_access_token


print("=" * 50)
print("RBAC MODULE TEST")
print("=" * 50)


# ============================================================
# 1. CREATE ANALYST TOKEN
# ============================================================

print("\n1. Creating ANALYST token...")

analyst_token = create_access_token(
    user_id="USR_TEST_ANALYST",
    username="aml_test_user",
    role="ANALYST"
)

print("Token created:", bool(analyst_token))

assert analyst_token
print("PASS")


# ============================================================
# 2. DECODE ANALYST TOKEN
# ============================================================

print("\n2. Decoding ANALYST token...")

analyst_payload = decode_access_token(
    analyst_token
)

print("Payload:")
print(analyst_payload)

assert analyst_payload is not None
assert analyst_payload["role"] == "ANALYST"
assert analyst_payload["username"] == "aml_test_user"

print("PASS")


# ============================================================
# 3. CREATE ADMIN TOKEN
# ============================================================

print("\n3. Creating ADMIN token...")

admin_token = create_access_token(
    user_id="USR_TEST_ADMIN",
    username="aml_admin",
    role="ADMIN"
)

print("Token created:", bool(admin_token))

assert admin_token
print("PASS")


# ============================================================
# 4. DECODE ADMIN TOKEN
# ============================================================

print("\n4. Decoding ADMIN token...")

admin_payload = decode_access_token(
    admin_token
)

print("Payload:")
print(admin_payload)

assert admin_payload is not None
assert admin_payload["role"] == "ADMIN"
assert admin_payload["username"] == "aml_admin"

print("PASS")


# ============================================================
# 5. INVALID TOKEN
# ============================================================

print("\n5. Testing invalid token...")

invalid_payload = decode_access_token(
    "INVALID_TOKEN"
)

print("Result:", invalid_payload)

assert invalid_payload is None

print("PASS")


# ============================================================
# COMPLETED
# ============================================================

print("\n" + "=" * 50)
print("RBAC MODULE TEST COMPLETED")
print("PASS")
print("=" * 50)