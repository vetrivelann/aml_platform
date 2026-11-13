from backend.notification_trigger import (
    create_aml_alert_notification
)


print("=" * 60)
print("AUTOMATIC AML NOTIFICATION TRIGGER TEST")
print("=" * 60)


# ============================================================
# TEST 1 — HIGH RISK ALERT
# ============================================================

print("\n1. Testing HIGH risk alert...")

high_alert = {
    "alert_id": "ALT_TEST_HIGH_001",
    "transaction_id": "TXN_TEST_HIGH_001",
    "alert_type": "LARGE_TRANSACTION",
    "severity": "HIGH",
    "risk_score": 80,
    "description": "Large transaction detected",
    "status": "OPEN"
}

notification = create_aml_alert_notification(
    high_alert
)

print("\nNotification result:")
print(notification)

if notification:

    print("\nPASS")

else:

    print("\nFAIL")


# ============================================================
# TEST 2 — LOW RISK ALERT
# ============================================================

print("\n2. Testing LOW risk alert...")

low_alert = {
    "alert_id": "ALT_TEST_LOW_001",
    "transaction_id": "TXN_TEST_LOW_001",
    "alert_type": "NORMAL_ACTIVITY",
    "severity": "LOW",
    "risk_score": 20,
    "description": "Normal transaction",
    "status": "OPEN"
}

low_notification = (
    create_aml_alert_notification(
        low_alert
    )
)

print("\nNotification result:")
print(low_notification)

if low_notification is None:

    print("\nPASS")

else:

    print("\nFAIL")


# ============================================================
# TEST 3 — CRITICAL ALERT
# ============================================================

print("\n3. Testing CRITICAL risk alert...")

critical_alert = {
    "alert_id": "ALT_TEST_CRITICAL_001",
    "transaction_id": "TXN_TEST_CRITICAL_001",
    "alert_type": "STRUCTURING",
    "severity": "CRITICAL",
    "risk_score": 95,
    "description": "Structuring pattern detected",
    "status": "OPEN"
}

critical_notification = (
    create_aml_alert_notification(
        critical_alert
    )
)

print("\nNotification result:")
print(critical_notification)

if critical_notification:

    print("\nPASS")

else:

    print("\nFAIL")


print("\n" + "=" * 60)
print("AUTOMATIC AML NOTIFICATION TRIGGER TEST COMPLETED")
print("=" * 60)