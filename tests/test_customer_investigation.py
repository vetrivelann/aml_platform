from backend.customer_investigation import (
    get_customer_investigation
)
from backend.database import engine
from sqlalchemy import text


print("=" * 60)
print("CUSTOMER INVESTIGATION MODULE TEST")
print("=" * 60)


# ============================================================
# FIND A CUSTOMER WITH TRANSACTIONS
# ============================================================

with engine.connect() as connection:

    row = connection.execute(
        text("""
            SELECT a.customer_id
            FROM accounts a
            INNER JOIN transactions t
                ON t.source_account_id = a.account_id
            GROUP BY a.customer_id
            ORDER BY COUNT(t.transaction_id) DESC
            LIMIT 1
        """)
    ).first()


if not row:
    print("\nNo customer with transactions found.")
    print("FAIL")
    raise SystemExit(1)


customer_id = row[0]

print("\nTesting customer:")
print(customer_id)


# ============================================================
# RUN INVESTIGATION
# ============================================================

result = get_customer_investigation(customer_id)


assert result is not None
assert result["customer"]["customer_id"] == customer_id

assert "transaction_summary" in result
assert "alert_summary" in result
assert "aml_rule_violations" in result
assert "risk_assessment" in result
assert "investigation_summary" in result
assert "transactions" in result
assert "alerts" in result


# ============================================================
# DISPLAY RESULTS
# ============================================================

print("\nCustomer:")
print(result["customer"])

print("\nTransaction Summary:")
print(result["transaction_summary"])

print("\nAlert Summary:")
print(result["alert_summary"])

print("\nRisk Assessment:")
print(result["risk_assessment"])

print("\nInvestigation Summary:")
print(result["investigation_summary"])

print("\nAdvanced AML Violations:")
print(
    len(
        result["aml_rule_violations"]["advanced_rules"]
    )
)

print("\nTotal Transactions Returned:")
print(len(result["transactions"]))

print("\nTotal Alerts Returned:")
print(len(result["alerts"]))


print("\n" + "=" * 60)
print("CUSTOMER INVESTIGATION MODULE TEST COMPLETED")
print("PASS")
print("=" * 60)
