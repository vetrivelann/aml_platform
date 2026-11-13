from sqlalchemy import text

from backend.database import engine
from backend.customer_risk import calculate_customer_risk


# ============================================================
# CUSTOMER INVESTIGATION
# ============================================================

def get_customer_investigation(customer_id: str):
    """
    Build a complete AML investigation profile for one customer.

    This module is intentionally independent from main.py so it can
    be tested before integration.

    It uses existing database tables:
        customers
        accounts
        transactions
        alerts

    Advanced AML alerts are already stored in the alerts table, so
    they are automatically included in the investigation results.
    """

    customer_sql = text("""
        SELECT customer_id
        FROM customers
        WHERE customer_id = :customer_id
    """)

    transaction_sql = text("""
        SELECT
            t.transaction_id,
            t.event_id,
            t.source_account_id,
            t.destination_account_id,
            t.amount,
            t.currency,
            t.channel,
            t.occurred_at,
            t.transaction_type
        FROM transactions t
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
        ORDER BY t.occurred_at DESC
    """)

    alert_sql = text("""
        SELECT
            al.alert_id,
            al.transaction_id,
            al.alert_type,
            al.severity,
            al.risk_score,
            al.description,
            al.status,
            al.created_at
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
        ORDER BY al.created_at DESC
    """)

    try:
        with engine.connect() as connection:

            # ------------------------------------------------
            # 1. Check customer
            # ------------------------------------------------
            customer = connection.execute(
                customer_sql,
                {"customer_id": customer_id}
            ).mappings().first()

            if not customer:
                return None

            # ------------------------------------------------
            # 2. Get transactions
            # ------------------------------------------------
            transaction_rows = connection.execute(
                transaction_sql,
                {"customer_id": customer_id}
            ).mappings().all()

            transactions = []

            for row in transaction_rows:
                transactions.append({
                    "transaction_id": row["transaction_id"],
                    "event_id": row["event_id"],
                    "source_account_id": row["source_account_id"],
                    "destination_account_id": row["destination_account_id"],
                    "amount": float(row["amount"]),
                    "currency": row["currency"],
                    "channel": row["channel"],
                    "occurred_at": (
                        row["occurred_at"].isoformat()
                        if row["occurred_at"]
                        else None
                    ),
                    "transaction_type": row["transaction_type"]
                })

            # ------------------------------------------------
            # 3. Get alerts
            # ------------------------------------------------
            alert_rows = connection.execute(
                alert_sql,
                {"customer_id": customer_id}
            ).mappings().all()

            alerts = []

            for row in alert_rows:
                alerts.append({
                    "alert_id": row["alert_id"],
                    "transaction_id": row["transaction_id"],
                    "alert_type": row["alert_type"],
                    "severity": row["severity"],
                    "risk_score": float(row["risk_score"]),
                    "description": row["description"],
                    "status": row["status"],
                    "created_at": (
                        row["created_at"].isoformat()
                        if row["created_at"]
                        else None
                    )
                })

            # ------------------------------------------------
            # 4. Count core AML rules
            # ------------------------------------------------
            large_transaction_count = sum(
                1
                for alert in alerts
                if alert["alert_type"] == "LARGE_TRANSACTION"
            )

            high_velocity_count = sum(
                1
                for alert in alerts
                if alert["alert_type"] == "HIGH_VELOCITY"
            )

            structuring_count = sum(
                1
                for alert in alerts
                if alert["alert_type"] == "STRUCTURING"
            )

            # ------------------------------------------------
            # 5. Customer risk
            # ------------------------------------------------
            risk_assessment = calculate_customer_risk(
                transaction_count=len(transactions),
                alert_count=len(alerts),
                large_transaction_count=large_transaction_count,
                high_velocity_count=high_velocity_count,
                structuring_count=structuring_count
            )

            # ------------------------------------------------
            # 6. Advanced AML rule violations
            #
            # Advanced rules are stored in the same alerts table.
            # Therefore we identify them by their alert_type.
            # ------------------------------------------------
            core_rules = {
                "LARGE_TRANSACTION",
                "HIGH_VELOCITY",
                "STRUCTURING"
            }

            advanced_rule_violations = [
                alert
                for alert in alerts
                if alert["alert_type"] not in core_rules
            ]

            # ------------------------------------------------
            # 7. Alert summary
            # ------------------------------------------------
            risk_levels = {
                "CRITICAL": 0,
                "HIGH": 0,
                "MEDIUM": 0,
                "LOW": 0
            }

            open_alert_count = 0

            for alert in alerts:

                level = alert["severity"]

                if level in risk_levels:
                    risk_levels[level] += 1

                if alert["status"] == "OPEN":
                    open_alert_count += 1

            # ------------------------------------------------
            # 8. Transaction summary
            # ------------------------------------------------
            total_transaction_amount = sum(
                transaction["amount"]
                for transaction in transactions
            )

            inbound_count = 0
            outbound_count = 0

            customer_accounts_sql = text("""
                SELECT account_id
                FROM accounts
                WHERE customer_id = :customer_id
            """)

            account_rows = connection.execute(
                customer_accounts_sql,
                {"customer_id": customer_id}
            ).mappings().all()

            customer_account_ids = {
                row["account_id"]
                for row in account_rows
            }

            for transaction in transactions:

                if transaction["source_account_id"] in customer_account_ids:
                    outbound_count += 1

                if transaction["destination_account_id"] in customer_account_ids:
                    inbound_count += 1

            # ------------------------------------------------
            # 9. Investigation decision
            # ------------------------------------------------
            requires_investigation = (
                len(alerts) > 0
                or risk_assessment["risk_level"] in {
                    "HIGH",
                    "CRITICAL"
                }
            )

            if risk_assessment["risk_level"] == "CRITICAL":
                investigation_priority = "CRITICAL"
            elif risk_assessment["risk_level"] == "HIGH":
                investigation_priority = "HIGH"
            elif len(alerts) > 0:
                investigation_priority = "MEDIUM"
            else:
                investigation_priority = "LOW"

            # ------------------------------------------------
            # 10. Final investigation response
            # ------------------------------------------------
            return {
                "customer": {
                    "customer_id": customer["customer_id"]
                },

                "transaction_summary": {
                    "transaction_count": len(transactions),
                    "total_transaction_amount": total_transaction_amount,
                    "inbound_transaction_count": inbound_count,
                    "outbound_transaction_count": outbound_count
                },

                "alert_summary": {
                    "total_alerts": len(alerts),
                    "open_alerts": open_alert_count,
                    "critical_alerts": risk_levels["CRITICAL"],
                    "high_alerts": risk_levels["HIGH"],
                    "medium_alerts": risk_levels["MEDIUM"],
                    "low_alerts": risk_levels["LOW"]
                },

                "aml_rule_violations": {
                    "core_rules": {
                        "large_transaction": large_transaction_count,
                        "high_velocity": high_velocity_count,
                        "structuring": structuring_count
                    },

                    "advanced_rules": advanced_rule_violations
                },

                "risk_assessment": {
                    "customer_risk_score":
                        risk_assessment["customer_risk_score"],
                    "risk_level":
                        risk_assessment["risk_level"]
                },

                "transactions": transactions,

                "alerts": alerts,

                "investigation_summary": {
                    "requires_investigation":
                        requires_investigation,
                    "investigation_priority":
                        investigation_priority,
                    "reason": (
                        "AML alerts detected for customer"
                        if len(alerts) > 0
                        else "No AML alerts detected"
                    )
                }
            }

    except Exception as e:
        raise RuntimeError(
            f"Customer investigation database error: {str(e)}"
        )
