from sqlalchemy import text

from backend.database import engine


# ============================================================
# AML ALERT INVESTIGATION MODULE
# ============================================================

def get_alert_investigation(alert_id: str):
    """
    Collect complete investigation information for an AML alert.

    This module is intentionally independent from main.py.
    It does not modify transactions, alerts, cases, or
    existing investigation functionality.
    """

    # ========================================================
    # 1. GET ALERT
    # ========================================================

    with engine.connect() as connection:

        alert = connection.execute(
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
                WHERE alert_id = :alert_id
            """),
            {
                "alert_id": alert_id
            }
        ).mappings().first()

        if not alert:
            return None

        alert = dict(alert)

        # ====================================================
        # 2. GET TRANSACTION
        # ====================================================

        transaction = connection.execute(
            text("""
                SELECT
                    transaction_id,
                    event_id,
                    source_account_id,
                    destination_account_id,
                    amount,
                    currency,
                    channel,
                    occurred_at,
                    transaction_type
                FROM transactions
                WHERE transaction_id = :transaction_id
            """),
            {
                "transaction_id": alert["transaction_id"]
            }
        ).mappings().first()

        transaction = (
            dict(transaction)
            if transaction
            else None
        )

        # ====================================================
        # 3. GET CUSTOMER
        # ====================================================

        customer = None

        if transaction:

            customer = connection.execute(
                text("""
                     SELECT
                c.customer_id
            FROM customers c
            JOIN accounts a
                ON c.customer_id = a.customer_id
            WHERE a.account_id = :account_id
                """),
                {
                    "account_id":
                        transaction["source_account_id"]
                }
            ).mappings().first()

            customer = (
                dict(customer)
                if customer
                else None
            )

        # ====================================================
        # 4. GET RELATED TRANSACTIONS
        # ====================================================

        related_transactions = []

        if transaction:

            related_transactions = connection.execute(
                text("""
                    SELECT
                        transaction_id,
                        event_id,
                        source_account_id,
                        destination_account_id,
                        amount,
                        currency,
                        channel,
                        occurred_at,
                        transaction_type
                    FROM transactions
                    WHERE source_account_id = :account_id
                      AND transaction_id != :transaction_id
                    ORDER BY occurred_at DESC
                    LIMIT 20
                """),
                {
                    "account_id":
                        transaction["source_account_id"],

                    "transaction_id":
                        transaction["transaction_id"]
                }
            ).mappings().all()

            related_transactions = [
                dict(row)
                for row in related_transactions
            ]

        # ====================================================
        # 5. GET RELATED ALERTS
        # ====================================================

        related_alerts = []

        if transaction:

            related_alerts = connection.execute(
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
                    WHERE transaction_id = :transaction_id
                    ORDER BY created_at DESC
                """),
                {
                    "transaction_id":
                        transaction["transaction_id"]
                }
            ).mappings().all()

            related_alerts = [
                dict(row)
                for row in related_alerts
            ]

        # ====================================================
        # 6. TRANSACTION SUMMARY
        # ====================================================

        transaction_summary = {
            "transaction_count": 0,
            "total_transaction_amount": 0,
            "average_transaction_amount": 0
        }

        if transaction:

            summary = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS transaction_count,
                        COALESCE(
                            SUM(amount),
                            0
                        ) AS total_transaction_amount,
                        COALESCE(
                            AVG(amount),
                            0
                        ) AS average_transaction_amount
                    FROM transactions
                    WHERE source_account_id = :account_id
                """),
                {
                    "account_id":
                        transaction["source_account_id"]
                }
            ).mappings().first()

            if summary:

                transaction_summary = dict(summary)

        # ====================================================
        # 7. ALERT SUMMARY
        # ====================================================

        alert_summary = {
            "alert_count": 0,
            "high_alert_count": 0,
            "critical_alert_count": 0
        }

        if transaction:

            alert_summary_result = connection.execute(
                text("""
                    SELECT
                        COUNT(*) AS alert_count,

                        COUNT(
                            CASE
                                WHEN severity = 'HIGH'
                                THEN 1
                            END
                        ) AS high_alert_count,

                        COUNT(
                            CASE
                                WHEN severity = 'CRITICAL'
                                THEN 1
                            END
                        ) AS critical_alert_count

                    FROM alerts

                    WHERE transaction_id = :transaction_id
                """),
                {
                    "transaction_id":
                        transaction["transaction_id"]
                }
            ).mappings().first()

            if alert_summary_result:

                alert_summary = dict(
                    alert_summary_result
                )

        # ====================================================
        # 8. RISK ASSESSMENT
        # ====================================================

        risk_score = float(
            alert.get("risk_score") or 0
        )

        severity = str(
            alert.get("severity") or "LOW"
        ).upper()

        if severity == "CRITICAL" or risk_score >= 90:
            risk_level = "CRITICAL"

        elif severity == "HIGH" or risk_score >= 70:
            risk_level = "HIGH"

        elif risk_score >= 40:
            risk_level = "MEDIUM"

        else:
            risk_level = "LOW"

        risk_assessment = {
            "risk_score": risk_score,
            "risk_level": risk_level,
            "alert_severity": severity,
            "alert_status": alert.get("status")
        }

        # ====================================================
        # 9. INVESTIGATION SUMMARY
        # ====================================================

        if risk_level == "CRITICAL":

            recommended_action = (
                "Immediate analyst investigation required"
            )

        elif risk_level == "HIGH":

            recommended_action = (
                "Analyst review required"
            )

        elif risk_level == "MEDIUM":

            recommended_action = (
                "Monitor and review transaction activity"
            )

        else:

            recommended_action = (
                "No immediate escalation required"
            )

        investigation_summary = {
            "alert_id": alert["alert_id"],
            "transaction_id": alert["transaction_id"],
            "risk_level": risk_level,
            "risk_score": risk_score,
            "related_transaction_count":
                len(related_transactions),
            "related_alert_count":
                len(related_alerts),
            "recommended_action":
                recommended_action
        }

    # ========================================================
    # 10. RETURN COMPLETE INVESTIGATION
    # ========================================================

    return {
        "alert": alert,

        "transaction": transaction,

        "customer": customer,

        "related_transactions":
            related_transactions,

        "related_alerts":
            related_alerts,

        "transaction_summary":
            transaction_summary,

        "alert_summary":
            alert_summary,

        "risk_assessment":
            risk_assessment,

        "investigation_summary":
            investigation_summary
    }