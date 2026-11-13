from decimal import Decimal
from datetime import datetime

from backend.aml_rules import (
    check_large_transaction,
    check_high_velocity,
    check_structuring
)


# ============================================================
# LARGE TRANSACTION TESTS
# ============================================================

print("\n========================================")
print("LARGE TRANSACTION TESTS")
print("========================================")


# ------------------------------------------------------------
# Test 1: Transaction above threshold
# ------------------------------------------------------------

large_result = check_large_transaction(
    Decimal("750000")
)

print("\nTest 1: ₹750,000")

print(large_result)

assert large_result["triggered"] is True
assert large_result["alert_type"] == "LARGE_TRANSACTION"
assert large_result["severity"] == "HIGH"
assert large_result["risk_score"] == 80

print("PASS")


# ------------------------------------------------------------
# Test 2: Transaction below threshold
# ------------------------------------------------------------

small_result = check_large_transaction(
    Decimal("100000")
)

print("\nTest 2: ₹100,000")

print(small_result)

assert small_result["triggered"] is False

print("PASS")


# ------------------------------------------------------------
# Test 3: Exactly ₹500,000
# ------------------------------------------------------------

threshold_result = check_large_transaction(
    Decimal("500000")
)

print("\nTest 3: Exactly ₹500,000")

print(threshold_result)

assert threshold_result["triggered"] is False

print("PASS")


# ============================================================
# HIGH VELOCITY TESTS
# ============================================================

print("\n========================================")
print("HIGH VELOCITY TESTS")
print("========================================")


# ------------------------------------------------------------
# Test 4: 5 transactions within 10 minutes
# ------------------------------------------------------------

current_time = datetime.fromisoformat(
    "2026-11-05T10:10:00+05:30"
)

previous_transactions = [

    {
        "occurred_at":
            "2026-11-05T10:02:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:04:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:06:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:08:00+05:30"
    }
]


velocity_result = check_high_velocity(
    current_time,
    previous_transactions
)

print("\nTest 4: 5 transactions within 10 minutes")

print(velocity_result)

assert velocity_result["triggered"] is True
assert velocity_result["alert_type"] == "HIGH_VELOCITY"
assert velocity_result["severity"] == "HIGH"
assert velocity_result["risk_score"] == 85

print("PASS")


# ------------------------------------------------------------
# Test 5: Only 4 transactions
# ------------------------------------------------------------

current_time = datetime.fromisoformat(
    "2026-11-05T10:10:00+05:30"
)

previous_transactions = [

    {
        "occurred_at":
            "2026-11-05T10:02:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:04:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:06:00+05:30"
    }
]


velocity_result = check_high_velocity(
    current_time,
    previous_transactions
)

print("\nTest 5: Only 4 transactions")

print(velocity_result)

assert velocity_result["triggered"] is False

print("PASS")


# ------------------------------------------------------------
# Test 6: Previous transactions outside 10-minute window
# ------------------------------------------------------------

current_time = datetime.fromisoformat(
    "2026-11-05T10:30:00+05:30"
)

previous_transactions = [

    {
        "occurred_at":
            "2026-11-05T10:02:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:04:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:06:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:08:00+05:30"
    }
]


velocity_result = check_high_velocity(
    current_time,
    previous_transactions
)

print(
    "\nTest 6: Previous transactions "
    "outside 10-minute window"
)

print(velocity_result)

assert velocity_result["triggered"] is False

print("PASS")


# ------------------------------------------------------------
# Test 7: Transaction exactly 10 minutes old
# ------------------------------------------------------------

current_time = datetime.fromisoformat(
    "2026-11-05T10:10:00+05:30"
)

previous_transactions = [

    {
        "occurred_at":
            "2026-11-05T10:00:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:02:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:04:00+05:30"
    },

    {
        "occurred_at":
            "2026-11-05T10:06:00+05:30"
    }
]


velocity_result = check_high_velocity(
    current_time,
    previous_transactions
)

print(
    "\nTest 7: Transaction exactly "
    "10 minutes old"
)

print(velocity_result)

assert velocity_result["triggered"] is True

print("PASS")


# ============================================================
# STRUCTURING / SMURFING TESTS
# ============================================================

print("\n========================================")
print("STRUCTURING / SMURFING TESTS")
print("========================================")


# ------------------------------------------------------------
# Test 8: 3 transactions totaling above ₹500,000
# ------------------------------------------------------------

current_amount = Decimal("200000")

previous_transactions = [

    {
        "amount": Decimal("180000"),

        "occurred_at":
            "2026-11-05T09:00:00+05:30"
    },

    {
        "amount": Decimal("170000"),

        "occurred_at":
            "2026-11-05T10:00:00+05:30"
    }
]


structuring_result = check_structuring(
    current_amount,
    previous_transactions
)

print(
    "\nTest 8: 3 transactions "
    "totaling ₹550,000"
)

print(structuring_result)

assert structuring_result["triggered"] is True
assert structuring_result["alert_type"] == "STRUCTURING"
assert structuring_result["severity"] == "HIGH"
assert structuring_result["risk_score"] == 90

print("PASS")


# ------------------------------------------------------------
# Test 9: Total amount below threshold
# ------------------------------------------------------------

current_amount = Decimal("100000")

previous_transactions = [

    {
        "amount": Decimal("150000"),

        "occurred_at":
            "2026-11-05T09:00:00+05:30"
    },

    {
        "amount": Decimal("100000"),

        "occurred_at":
            "2026-11-05T10:00:00+05:30"
    }
]


structuring_result = check_structuring(
    current_amount,
    previous_transactions
)

print(
    "\nTest 9: Total amount ₹350,000"
)

print(structuring_result)

assert structuring_result["triggered"] is False

print("PASS")


# ------------------------------------------------------------
# Test 10: Only 2 transactions
# ------------------------------------------------------------

current_amount = Decimal("200000")

previous_transactions = [

    {
        "amount": Decimal("180000"),

        "occurred_at":
            "2026-11-05T09:00:00+05:30"
    }
]


structuring_result = check_structuring(
    current_amount,
    previous_transactions
)

print(
    "\nTest 10: Only 2 transactions"
)

print(structuring_result)

assert structuring_result["triggered"] is False

print("PASS")


# ------------------------------------------------------------
# Test 11: Transaction outside 24-hour window
# ------------------------------------------------------------

current_amount = Decimal("200000")

previous_transactions = [

    {
        "amount": Decimal("180000"),

        "occurred_at":
            "2026-11-03T09:00:00+05:30"
    },

    {
        "amount": Decimal("170000"),

        "occurred_at":
            "2026-11-05T10:00:00+05:30"
    }
]


structuring_result = check_structuring(
    current_amount,
    previous_transactions
)

print(
    "\nTest 11: Old transaction "
    "outside 24-hour window"
)

print(structuring_result)

assert structuring_result["triggered"] is False

print("PASS")


# ------------------------------------------------------------
# Test 12: One transaction is above ₹500,000
# ------------------------------------------------------------

current_amount = Decimal("200000")

previous_transactions = [

    {
        "amount": Decimal("600000"),

        "occurred_at":
            "2026-11-05T09:00:00+05:30"
    },

    {
        "amount": Decimal("180000"),

        "occurred_at":
            "2026-11-05T10:00:00+05:30"
    }
]


structuring_result = check_structuring(
    current_amount,
    previous_transactions
)

print(
    "\nTest 12: Previous transaction "
    "above ₹500,000"
)

print(structuring_result)

assert structuring_result["triggered"] is False

print("PASS")


# ============================================================
# FINAL RESULT
# ============================================================

print("\n========================================")
print("ALL AML RULE TESTS PASSED")
print("========================================")

print("\nRules tested:")
print("1. LARGE_TRANSACTION")
print("2. HIGH_VELOCITY")
print("3. STRUCTURING")