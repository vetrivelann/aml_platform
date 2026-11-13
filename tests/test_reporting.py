from backend.reporting import (
    generate_transaction_report,
    generate_alert_report,
    generate_customer_risk_report,
    generate_case_report,
    generate_investigation_report,
    export_to_csv
)


print("=" * 60)
print("REPORTING MODULE TEST")
print("=" * 60)


# ============================================================
# TEST 1 — TRANSACTION REPORT
# ============================================================

transactions = generate_transaction_report()

print("\n1. Transaction Report")
print("Transactions:", len(transactions))

assert isinstance(transactions, list)

print("PASS")


# ============================================================
# TEST 2 — ALERT REPORT
# ============================================================

alerts = generate_alert_report()

print("\n2. Alert Report")
print("Alerts:", len(alerts))

assert isinstance(alerts, list)

print("PASS")


# ============================================================
# TEST 3 — CUSTOMER RISK REPORT
# ============================================================

customer_risk = generate_customer_risk_report()

print("\n3. Customer Risk Report")
print("Customers:", len(customer_risk))

assert isinstance(customer_risk, list)

print("PASS")


# ============================================================
# TEST 4 — CASE REPORT
# ============================================================

cases = generate_case_report()

print("\n4. Case Report")
print("Cases:", len(cases))

assert isinstance(cases, list)

print("PASS")


# ============================================================
# TEST 5 — INVESTIGATION REPORT
# ============================================================

investigation = generate_investigation_report()

print("\n5. AML Investigation Report")

print(
    "Total transactions:",
    investigation["transaction_summary"]
    ["total_transactions"]
)

print(
    "Total alerts:",
    investigation["alert_summary"]
    ["total_alerts"]
)

print(
    "Total cases:",
    investigation["case_summary"]
    ["total_cases"]
)

assert "transaction_summary" in investigation
assert "alert_summary" in investigation
assert "case_summary" in investigation

print("PASS")


# ============================================================
# TEST 6 — CSV EXPORT
# ============================================================

csv_data = export_to_csv(alerts)

print("\n6. CSV Export")

print(
    "CSV generated:",
    len(csv_data) > 0
)

if alerts:
    assert "alert_id" in csv_data

print("PASS")


# ============================================================
# COMPLETION
# ============================================================

print("\n" + "=" * 60)
print("REPORTING MODULE TEST COMPLETED")
print("PASS")
print("=" * 60)