from datetime import datetime, timedelta
from decimal import Decimal

from backend.advanced_aml_rules import (
    detect_rapid_fund_movement,
    detect_unusual_transaction_amount,
    detect_unusual_transaction_frequency,
    detect_round_number_transactions,
    detect_multiple_counterparties,
    run_advanced_aml_rules
)


print("=" * 60)
print("ADVANCED AML RULES MODULE TEST")
print("=" * 60)


# ============================================================
# TEST DATA
# ============================================================

base_time = datetime.now()

transactions = [

    # --------------------------------------------------------
    # NORMAL HISTORICAL TRANSACTIONS
    # --------------------------------------------------------

    {
        "transaction_id": "TXN_001",
        "customer_id": "CUS_001",
        "source_account_id": "ACC_001",
        "destination_account_id": "ACC_010",
        "amount": Decimal("10000"),
        "occurred_at": base_time - timedelta(days=10),
        "direction": "OUT"
    },

    {
        "transaction_id": "TXN_002",
        "customer_id": "CUS_001",
        "source_account_id": "ACC_001",
        "destination_account_id": "ACC_011",
        "amount": Decimal("12000"),
        "occurred_at": base_time - timedelta(days=9),
        "direction": "OUT"
    },

    {
        "transaction_id": "TXN_003",
        "customer_id": "CUS_001",
        "source_account_id": "ACC_001",
        "destination_account_id": "ACC_012",
        "amount": Decimal("15000"),
        "occurred_at": base_time - timedelta(days=8),
        "direction": "OUT"
    },

    # --------------------------------------------------------
    # RAPID FUND MOVEMENT
    # --------------------------------------------------------

    {
        "transaction_id": "TXN_004",
        "customer_id": "CUS_002",
        "source_account_id": "BANK",
        "destination_account_id": "ACC_002",
        "amount": Decimal("500000"),
        "occurred_at": base_time,
        "direction": "IN"
    },

    {
        "transaction_id": "TXN_005",
        "customer_id": "CUS_002",
        "source_account_id": "ACC_002",
        "destination_account_id": "ACC_020",
        "amount": Decimal("450000"),
        "occurred_at":
            base_time + timedelta(minutes=20),
        "direction": "OUT"
    },

    # --------------------------------------------------------
    # UNUSUAL AMOUNT
    # --------------------------------------------------------

    {
        "transaction_id": "TXN_006",
        "customer_id": "CUS_001",
        "source_account_id": "ACC_001",
        "destination_account_id": "ACC_013",
        "amount": Decimal("100000"),
        "occurred_at":
            base_time + timedelta(hours=1),
        "direction": "OUT"
    },

    # --------------------------------------------------------
    # ROUND NUMBER
    # --------------------------------------------------------

    {
        "transaction_id": "TXN_007",
        "customer_id": "CUS_003",
        "source_account_id": "ACC_003",
        "destination_account_id": "ACC_030",
        "amount": Decimal("200000"),
        "occurred_at":
            base_time + timedelta(hours=2),
        "direction": "OUT"
    },

    # --------------------------------------------------------
    # MULTIPLE COUNTERPARTIES
    # --------------------------------------------------------

    {
        "transaction_id": "TXN_008",
        "customer_id": "CUS_004",
        "source_account_id": "ACC_004",
        "destination_account_id": "ACC_041",
        "amount": Decimal("20000"),
        "occurred_at":
            base_time + timedelta(hours=3),
        "direction": "OUT"
    },

    {
        "transaction_id": "TXN_009",
        "customer_id": "CUS_004",
        "source_account_id": "ACC_004",
        "destination_account_id": "ACC_042",
        "amount": Decimal("20000"),
        "occurred_at":
            base_time + timedelta(hours=3, minutes=5),
        "direction": "OUT"
    },

    {
        "transaction_id": "TXN_010",
        "customer_id": "CUS_004",
        "source_account_id": "ACC_004",
        "destination_account_id": "ACC_043",
        "amount": Decimal("20000"),
        "occurred_at":
            base_time + timedelta(hours=3, minutes=10),
        "direction": "OUT"
    },

    {
        "transaction_id": "TXN_011",
        "customer_id": "CUS_004",
        "source_account_id": "ACC_004",
        "destination_account_id": "ACC_044",
        "amount": Decimal("20000"),
        "occurred_at":
            base_time + timedelta(hours=3, minutes=15),
        "direction": "OUT"
    },

    {
        "transaction_id": "TXN_012",
        "customer_id": "CUS_004",
        "source_account_id": "ACC_004",
        "destination_account_id": "ACC_045",
        "amount": Decimal("20000"),
        "occurred_at":
            base_time + timedelta(hours=3, minutes=20),
        "direction": "OUT"
    }
]


# ============================================================
# TEST 1 — RAPID FUND MOVEMENT
# ============================================================

rapid_alerts = detect_rapid_fund_movement(
    transactions
)

print("\n1. Rapid Fund Movement")
print("Triggered alerts:", len(rapid_alerts))

assert len(rapid_alerts) >= 1

print("PASS")


# ============================================================
# TEST 2 — UNUSUAL AMOUNT
# ============================================================

amount_alerts = detect_unusual_transaction_amount(
    transactions
)

print("\n2. Unusual Transaction Amount")
print("Triggered alerts:", len(amount_alerts))

assert len(amount_alerts) >= 1

print("PASS")


# ============================================================
# TEST 3 — ROUND NUMBER
# ============================================================

round_alerts = detect_round_number_transactions(
    transactions
)

print("\n3. Round Number Transaction")
print("Triggered alerts:", len(round_alerts))

assert len(round_alerts) >= 1

print("PASS")


# ============================================================
# TEST 4 — MULTIPLE COUNTERPARTIES
# ============================================================

counterparty_alerts = detect_multiple_counterparties(
    transactions
)

print("\n4. Multiple Counterparties")
print(
    "Triggered alerts:",
    len(counterparty_alerts)
)

assert len(counterparty_alerts) >= 1

print("PASS")


# ============================================================
# TEST 5 — ALL ADVANCED RULES
# ============================================================

all_alerts = run_advanced_aml_rules(
    transactions
)

print("\n5. All Advanced AML Rules")

print(
    "Total triggered alerts:",
    len(all_alerts)
)

assert len(all_alerts) >= 4

for alert in all_alerts:

    print(
        f"- {alert['rule_type']} | "
        f"Risk: {alert['risk_score']} | "
        f"Level: {alert['risk_level']}"
    )

print("\nPASS")


# ============================================================
# COMPLETION
# ============================================================

print("\n" + "=" * 60)
print("ADVANCED AML RULES MODULE TEST COMPLETED")
print("=" * 60)