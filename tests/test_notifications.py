from backend.notifications import (
    create_notification,
    get_notifications,
    get_notification_by_id,
    update_notification_status
)


print("=" * 60)
print("NOTIFICATION MODULE TEST")
print("=" * 60)


# ============================================================
# 1. CREATE NOTIFICATION
# ============================================================

print("\n1. Creating notification...")

notification = create_notification(
    notification_type="AML_ALERT",
    recipient="AML_ANALYST_01",
    subject="High Risk AML Alert",
    message=(
        "A high-risk transaction requires "
        "analyst review."
    ),
    priority="HIGH"
)

print(notification)

assert notification["notification_id"]
assert notification["status"] == "PENDING"

print("PASS")


# ============================================================
# 2. GET ALL NOTIFICATIONS
# ============================================================

print("\n2. Getting all notifications...")

notifications = get_notifications()

print(
    f"Notifications: {len(notifications)}"
)

assert len(notifications) >= 1

print("PASS")


# ============================================================
# 3. GET NOTIFICATION BY ID
# ============================================================

print("\n3. Getting notification by ID...")

notification_id = (
    notification["notification_id"]
)

result = get_notification_by_id(
    notification_id
)

print(result)

assert result is not None
assert (
    result["notification_id"]
    == notification_id
)

print("PASS")


# ============================================================
# 4. UPDATE STATUS
# ============================================================

print("\n4. Updating notification status...")

updated = update_notification_status(
    notification_id,
    "SENT"
)

print(updated)

assert updated is not None
assert updated["status"] == "SENT"

print("PASS")


# ============================================================
# FINAL
# ============================================================

print("\n" + "=" * 60)
print("NOTIFICATION MODULE TEST COMPLETED")
print("PASS")
print("=" * 60)