from datetime import datetime
from decimal import Decimal
import csv
import io

from sqlalchemy import text

from backend.database import engine


# ============================================================
# TRANSACTION REPORT
# ============================================================

def generate_transaction_report():

    with engine.connect() as connection:

        rows = connection.execute(
            text("""
                SELECT
                    transaction_id,
                    source_account_id,
                    destination_account_id,
                    amount,
                    currency,
                    channel,
                    occurred_at,
                    transaction_type
                FROM transactions
                ORDER BY occurred_at DESC
            """)
        ).mappings().all()

    return [dict(row) for row in rows]


# ============================================================
# ALERT REPORT
# ============================================================

def generate_alert_report():

    with engine.connect() as connection:

        rows = connection.execute(
            text("""
                SELECT
                    alert_id,
                    transaction_id,
                    alert_type,
                    severity,
                    risk_score,
                    description,
                    status,
                    created_at
                FROM alerts
                ORDER BY created_at DESC
            """)
        ).mappings().all()

    return [dict(row) for row in rows]


# ============================================================
# CUSTOMER RISK REPORT
# ============================================================

def generate_customer_risk_report():

    with engine.connect() as connection:

        customers = connection.execute(
            text("""
                SELECT customer_id
                FROM customers
                ORDER BY customer_id
            """)
        ).mappings().all()

    report = []

    for customer in customers:

        customer_id = customer["customer_id"]

        with engine.connect() as connection:

            transaction_data = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS transaction_count,
                        COALESCE(SUM(amount), 0) AS total_amount
                    FROM transactions t
                    JOIN accounts a
                        ON t.source_account_id = a.account_id
                    WHERE a.customer_id = :customer_id
                """),
                {
                    "customer_id": customer_id
                }
            ).mappings().first()

            alert_data = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS alert_count
                    FROM alerts al
                    JOIN transactions t
                        ON al.transaction_id = t.transaction_id
                    JOIN accounts a
                        ON t.source_account_id = a.account_id
                    WHERE a.customer_id = :customer_id
                """),
                {
                    "customer_id": customer_id
                }
            ).mappings().first()

        transaction_count = (
            transaction_data["transaction_count"] or 0
        )

        total_amount = (
            transaction_data["total_amount"] or 0
        )

        alert_count = (
            alert_data["alert_count"] or 0
        )

        # Simple report-level risk classification
        if alert_count >= 5:
            risk_score = 90
            risk_level = "CRITICAL"

        elif alert_count >= 3:
            risk_score = 70
            risk_level = "HIGH"

        elif alert_count >= 1:
            risk_score = 40
            risk_level = "MEDIUM"

        else:
            risk_score = 10
            risk_level = "LOW"

        report.append(
            {
                "customer_id": customer_id,
                "transaction_count": transaction_count,
                "total_transaction_amount": float(
                    total_amount
                ),
                "alert_count": alert_count,
                "risk_score": risk_score,
                "risk_level": risk_level
            }
        )

    return report


# ============================================================
# CASE REPORT
# ============================================================

def generate_case_report():

    with engine.connect() as connection:

        rows = connection.execute(
            text("""
                SELECT
                    case_id,
                    alert_id,
                    priority,
                    case_status,
                    assigned_to,
                    disposition,
                    notes,
                    created_at,
                    updated_at
                FROM cases
                ORDER BY created_at DESC
            """)
        ).mappings().all()

    return [dict(row) for row in rows]


# ============================================================
# AML INVESTIGATION REPORT
# ============================================================

def generate_investigation_report():

    transactions = generate_transaction_report()
    alerts = generate_alert_report()
    cases = generate_case_report()

    total_transaction_amount = sum(
        Decimal(str(transaction["amount"]))
        for transaction in transactions
    )

    open_alerts = sum(
        1
        for alert in alerts
        if str(alert.get("status", "")).upper() == "OPEN"
    )

    high_risk_alerts = sum(
        1
        for alert in alerts
        if str(alert.get("severity", "")).upper()
        == "HIGH"
    )

    critical_alerts = sum(
        1
        for alert in alerts
        if str(alert.get("severity", "")).upper()
        == "CRITICAL"
    )

    open_cases = sum(
        1
        for case in cases
        if str(case.get("case_status", "")).upper()
        not in {"CLOSED", "RESOLVED"}
    )

    return {
        "generated_at": datetime.now().isoformat(),

        "transaction_summary": {
            "total_transactions": len(transactions),
            "total_transaction_amount":
                float(total_transaction_amount)
        },

        "alert_summary": {
            "total_alerts": len(alerts),
            "open_alerts": open_alerts,
            "high_risk_alerts": high_risk_alerts,
            "critical_alerts": critical_alerts
        },

        "case_summary": {
            "total_cases": len(cases),
            "open_cases": open_cases
        }
    }


# ============================================================
# CSV EXPORT
# ============================================================

def export_to_csv(data):

    if not data:
        return ""

    output = io.StringIO()

    fieldnames = list(data[0].keys())

    writer = csv.DictWriter(
        output,
        fieldnames=fieldnames
    )

    writer.writeheader()

    for row in data:

        writer.writerow(
            {
                key: str(value)
                for key, value in row.items()
            }
        )

    return output.getvalue()