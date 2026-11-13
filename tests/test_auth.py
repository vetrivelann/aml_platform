from backend.user_auth import (
    create_user,
    authenticate_user,
    get_user_by_id
)


print("=" * 50)
print("AUTHENTICATION MODULE TEST")
print("=" * 50)


# ------------------------------------------------------------
# CREATE TEST USER
# ------------------------------------------------------------

username = "aml_test_user"

try:

    user = create_user(
        username=username,
        password="Test12345",
        role="ANALYST"
    )

    print("\nUser created:")
    print(user)

except ValueError as e:

    print("\nUser already exists or creation failed:")
    print(e)


# ------------------------------------------------------------
# AUTHENTICATE
# ------------------------------------------------------------

authenticated_user = authenticate_user(
    username=username,
    password="Test12345"
)

print("\nAuthentication result:")
print(authenticated_user)


# ------------------------------------------------------------
# GET USER
# ------------------------------------------------------------

if authenticated_user:

    user_details = get_user_by_id(
        authenticated_user["user_id"]
    )

    print("\nUser details:")
    print(user_details)


print("\n" + "=" * 50)
print("AUTHENTICATION MODULE TEST COMPLETED")
print("=" * 50)