from fastapi import FastAPI, HTTPException, Depends
from backend.dependencies import require_roles
from sqlalchemy import text
from datetime import timezone, timedelta
from decimal import Decimal
from uuid import uuid4
from backend.auth_routes import router as auth_router
from backend.models import (
    TransactionCreate,
    AlertStatusUpdate,
    CaseCreate,
    CaseUpdate
)
from backend.case_workflow_routes import (
    router as case_workflow_router
)
from backend.investigation_routes import (
    router as investigation_router
)
from backend.notification_routes import router as notification_router
from fastapi.responses import Response
from backend.reporting import (
    generate_transaction_report,
    generate_alert_report,
    generate_customer_risk_report,
    generate_case_report,
    generate_investigation_report,
    export_to_csv
)
from backend.notification_trigger import create_aml_alert_notification
from backend.advanced_aml_rules import (
    run_advanced_aml_rules
)
from backend.rbac_routes import router as rbac_router
from backend.database import engine
from backend.audit import create_audit_log
from backend.audit_routes import router as audit_router
from backend.risk_engine import calculate_overall_risk
from backend.customer_investigation import get_customer_investigation
from backend.customer_risk import calculate_customer_risk
from backend.dependencies import require_roles
# ============================================================
# AUDIT TRAIL INTEGRATION
# ============================================================
# Audit logging is intentionally isolated from AML processing.
# Audit failures are caught so existing API operations continue.
# Authentication and RBAC remain handled by existing modules.
# Existing AML rules and risk calculations are unchanged.
# Existing transaction, alert, case, and dashboard APIs remain.
# ============================================================
from backend.aml_rules import (
    check_large_transaction,
    check_high_velocity,
    check_structuring,
    HIGH_VELOCITY_WINDOW_MINUTES,
    STRUCTURING_WINDOW_HOURS
)

from backend.risk_engine import calculate_overall_risk

from backend.customer_risk import calculate_customer_risk


# ============================================================
# FASTAPI APPLICATION
# ============================================================

app = FastAPI(
    title="AML Transaction Monitoring Platform",
    description="Real-Time AML Transaction Monitoring & Investigation Platform",
    version="1.0.0"
)

app.include_router(auth_router)
app.include_router(rbac_router)
app.include_router(audit_router)
app.include_router(notification_router)
app.include_router(investigation_router)
app.include_router(case_workflow_router)
# ============================================================
# CONFIGURATION
# ============================================================

LARGE_TRANSACTION_THRESHOLD = Decimal("500000")


# ============================================================
# ROOT ENDPOINT
# ============================================================

@app.get("/")
def root():

    return {
        "message":
            "AML Transaction Monitoring Platform is running"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():

    return {
        "status": "healthy"
    }


# ============================================================
# CREATE TRANSACTION
# ============================================================

@app.post("/api/v1/transactions")
def create_transaction(
    transaction: TransactionCreate,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "USER"
        )
    )
):

    # --------------------------------------------------------
    # 1. Validate source and destination accounts
    # --------------------------------------------------------

    if (
        transaction.source_account_id
        == transaction.destination_account_id
    ):

        raise HTTPException(
            status_code=400,
            detail=(
                "Source and destination accounts "
                "cannot be the same"
            )
        )

    # --------------------------------------------------------
    # 2. Generate transaction IDs
    # --------------------------------------------------------

    # Transaction ID is built from the source and destination accounts
    # plus a short unique suffix so every transaction remains unique.
    transaction_id = (
        f"TXN_{transaction.source_account_id}_"
        f"{transaction.destination_account_id}_"
        f"{uuid4().hex[:6].upper()}"
    )

    event_id = (
        f"EVT_{uuid4().hex[:12].upper()}"
    )

    # --------------------------------------------------------
    # 3. Handle transaction timestamp
    # --------------------------------------------------------

    occurred_at = transaction.occurred_at

    if occurred_at.tzinfo is None:

        occurred_at = occurred_at.replace(
            tzinfo=timezone.utc
        )

    else:

        occurred_at = occurred_at.astimezone(
            timezone.utc
        )

    # --------------------------------------------------------
    # 4. SQL INSERT
    # --------------------------------------------------------

    insert_transaction_sql = text("""
        INSERT INTO transactions (
            transaction_id,
            event_id,
            source_account_id,
            destination_account_id,
            amount,
            currency,
            channel,
            occurred_at,
            transaction_type
        )
        VALUES (
            :transaction_id,
            :event_id,
            :source_account_id,
            :destination_account_id,
            :amount,
            :currency,
            :channel,
            :occurred_at,
            :transaction_type
        )
    """)

    try:

        # ====================================================
        # DATABASE TRANSACTION
        # ====================================================

        with engine.begin() as connection:

            # ------------------------------------------------
            # 5. Check source account
            # ------------------------------------------------

            source_exists = connection.execute(
                text("""
                    SELECT account_id
                    FROM accounts
                    WHERE account_id = :account_id
                """),
                {
                    "account_id":
                        transaction.source_account_id
                }
            ).fetchone()

            if not source_exists:

                raise HTTPException(
                    status_code=404,
                    detail="Source account not found"
                )

            # ------------------------------------------------
            # 6. Check destination account
            # ------------------------------------------------

            destination_exists = connection.execute(
                text("""
                    SELECT account_id
                    FROM accounts
                    WHERE account_id = :account_id
                """),
                {
                    "account_id":
                        transaction.destination_account_id
                }
            ).fetchone()

            if not destination_exists:

                raise HTTPException(
                    status_code=404,
                    detail="Destination account not found"
                )

            # ------------------------------------------------
            # 7. Insert transaction
            # ------------------------------------------------

            connection.execute(
                insert_transaction_sql,
                {
                    "transaction_id":
                        transaction_id,

                    "event_id":
                        event_id,

                    "source_account_id":
                        transaction.source_account_id,

                    "destination_account_id":
                        transaction.destination_account_id,

                    "amount":
                        transaction.amount,

                    "currency":
                        transaction.currency,

                    "channel":
                        transaction.channel,

                    "occurred_at":
                        occurred_at,

                    "transaction_type":
                        transaction.transaction_type
                }
            )

            # =================================================
            # AML ENGINE
            # =================================================

            aml_results = []

            # =================================================
            # RULE 1: LARGE TRANSACTION
            # =================================================

            large_transaction_result = (
                check_large_transaction(
                    transaction.amount
                )
            )

            if large_transaction_result["triggered"]:

                aml_results.append(
                    large_transaction_result
                )

            # =================================================
            # RULE 2: HIGH VELOCITY
            # =================================================

            velocity_start_time = (
                occurred_at
                - timedelta(
                    minutes=
                    HIGH_VELOCITY_WINDOW_MINUTES
                )
            )

            velocity_end_time = occurred_at

            velocity_query = text("""
                SELECT occurred_at
                FROM transactions
                WHERE source_account_id =
                      :source_account_id

                  AND transaction_id !=
                      :transaction_id

                  AND occurred_at >=
                      :start_time

                  AND occurred_at <=
                      :end_time

                ORDER BY occurred_at ASC
            """)

            velocity_rows = connection.execute(
                velocity_query,
                {
                    "source_account_id":
                        transaction.source_account_id,

                    "transaction_id":
                        transaction_id,

                    "start_time":
                        velocity_start_time,

                    "end_time":
                        velocity_end_time
                }
            ).fetchall()

            previous_velocity_transactions = []

            for row in velocity_rows:

                previous_velocity_transactions.append(
                    {
                        "occurred_at":
                            row.occurred_at
                    }
                )

            high_velocity_result = (
                check_high_velocity(
                    occurred_at,
                    previous_velocity_transactions
                )
            )

            if high_velocity_result["triggered"]:

                aml_results.append(
                    high_velocity_result
                )

            # =================================================
            # RULE 3: STRUCTURING / SMURFING
            # =================================================

            structuring_start_time = (
                occurred_at
                - timedelta(
                    hours=
                    STRUCTURING_WINDOW_HOURS
                )
            )

            structuring_end_time = occurred_at

            structuring_query = text("""
                SELECT
                    transaction_id,
                    amount,
                    occurred_at
                FROM transactions
                WHERE source_account_id =
                      :source_account_id

                  AND transaction_id !=
                      :transaction_id

                  AND occurred_at >=
                      :start_time

                  AND occurred_at <=
                      :end_time

                ORDER BY occurred_at ASC
            """)

            structuring_rows = connection.execute(
                structuring_query,
                {
                    "source_account_id":
                        transaction.source_account_id,

                    "transaction_id":
                        transaction_id,

                    "start_time":
                        structuring_start_time,

                    "end_time":
                        structuring_end_time
                }
            ).fetchall()

            previous_structuring_transactions = []

            for row in structuring_rows:

                previous_structuring_transactions.append(
                    {
                        "amount":
                            row.amount,

                        "occurred_at":
                            row.occurred_at
                    }
                )

            structuring_result = (
                check_structuring(
                    transaction.amount,
                    previous_structuring_transactions
                )
            )

            if structuring_result["triggered"]:

                aml_results.append(
                    structuring_result
                )

            # =================================================
            # ADVANCED AML RULE ENGINE
            # =================================================
            # Existing AML rules above are intentionally preserved.
            # The advanced rules are added after the existing rules
            # so the original transaction-monitoring behaviour remains.
            # =================================================

            advanced_aml_results = []

            try:

                # ------------------------------------------------
                # Find the customer associated with the source account
                # ------------------------------------------------

                customer_row = connection.execute(
                    text("""
                        SELECT customer_id
                        FROM accounts
                        WHERE account_id = :account_id
                    """),
                    {
                        "account_id":
                            transaction.source_account_id
                    }
                ).mappings().first()

                if customer_row:

                    customer_id = customer_row["customer_id"]

                    # --------------------------------------------
                    # Get all accounts belonging to this customer
                    # --------------------------------------------

                    customer_accounts = connection.execute(
                        text("""
                            SELECT account_id
                            FROM accounts
                            WHERE customer_id = :customer_id
                        """),
                        {
                            "customer_id": customer_id
                        }
                    ).scalars().all()

                    # --------------------------------------------
                    # Get transaction history involving the customer
                    # --------------------------------------------

                    if customer_accounts:

                        # Fetch transaction history and filter it to the
                        # customer's accounts in Python. This avoids changing
                        # the existing SQLAlchemy/PostgreSQL configuration.
                        all_transaction_rows = connection.execute(
                            text("""
                                SELECT
                                    transaction_id,
                                    source_account_id,
                                    destination_account_id,
                                    amount,
                                    occurred_at
                                FROM transactions
                                ORDER BY occurred_at ASC
                            """)
                        ).mappings().all()

                        advanced_transactions = []

                        customer_account_set = set(
                            customer_accounts
                        )

                        for row in all_transaction_rows:

                            if (
                                row["source_account_id"]
                                not in customer_account_set
                                and row["destination_account_id"]
                                not in customer_account_set
                            ):
                                continue

                            if row["source_account_id"] in customer_account_set:
                                direction = "OUT"
                            else:
                                direction = "IN"

                            advanced_transactions.append({
                                "transaction_id":
                                    row["transaction_id"],

                                "customer_id":
                                    customer_id,

                                "source_account_id":
                                    row["source_account_id"],

                                "destination_account_id":
                                    row["destination_account_id"],

                                "amount":
                                    row["amount"],

                                "occurred_at":
                                    row["occurred_at"],

                                "direction":
                                    direction
                            })

                        # The current transaction is already inserted above,
                        # therefore it is already included in the history.

                        advanced_aml_results = run_advanced_aml_rules(
                            advanced_transactions
                        )

                        # Only attach advanced rules that triggered for the
                        # transaction being created. Historical violations must
                        # not be copied onto the new transaction.
                        advanced_aml_results = [
                            result
                            for result in advanced_aml_results
                            if str(
                                result.get(
                                    "trigger_transaction_id",
                                    result.get("transaction_id", "")
                                )
                            ) == str(transaction_id)
                        ]

                        for advanced_result in advanced_aml_results:

                            # ------------------------------------------------
                            # Normalize advanced AML result to the existing AML format
                            # ------------------------------------------------
                            #
                            # Advanced AML rules return:
                            #   rule_type
                            #   risk_score
                            #   risk_level
                            #   description
                            #
                            # Existing AML alert processing expects:
                            #   alert_type
                            #   risk_score
                            #   severity
                            #   description
                            #
                            # This conversion allows advanced rules to use the
                            # existing alert database and alert API without changing
                            # any existing AML rule behaviour.
                            # ------------------------------------------------

                            normalized_advanced_result = {
                                "alert_type": advanced_result.get(
                                    "alert_type",
                                    advanced_result.get(
                                        "rule_type",
                                        "ADVANCED_AML_RULE"
                                    )
                                ),
                                "risk_score": advanced_result.get(
                                    "risk_score",
                                    0
                                ),
                                "severity": advanced_result.get(
                                    "severity",
                                    advanced_result.get(
                                        "risk_level",
                                        "MEDIUM"
                                    )
                                ),
                                "description": advanced_result.get(
                                    "description",
                                    "Advanced AML rule triggered"
                                )
                            }

                            # Add the normalized result to the existing
                            # alert-processing pipeline.
                            aml_results.append(
                                normalized_advanced_result
                            )

            except Exception:

                # Advanced-rule failure must not break the existing
                # transaction and basic AML processing.
                advanced_aml_results = []

            # =================================================
            # RISK SCORING ENGINE
            # =================================================

            risk_assessment = calculate_overall_risk(
                aml_results
            )

            # =================================================
            # CREATE ALERTS
            # =================================================

            alerts_created = []

            insert_alert_sql = text("""
                INSERT INTO alerts (
                    alert_id,
                    transaction_id,
                    alert_type,
                    severity,
                    risk_score,
                    description,
                    status,
                    created_at
                )
                VALUES (
                    :alert_id,
                    :transaction_id,
                    :alert_type,
                    :severity,
                    :risk_score,
                    :description,
                    :status,
                    CURRENT_TIMESTAMP
                )
            """)

            for aml_result in aml_results:

                alert_id = (
                    f"ALT_{uuid4().hex[:12].upper()}"
                )

                connection.execute(
                    insert_alert_sql,
                    {
                        "alert_id":
                            alert_id,

                        "transaction_id":
                            transaction_id,

                        "alert_type":
                            aml_result["alert_type"],

                        "severity":
                            aml_result["severity"],

                        "risk_score":
                            aml_result["risk_score"],

                        "description":
                            aml_result["description"],

                        "status":
                            "OPEN"
                    }
                )

                # ============================================================
                # AUTOMATIC CASE CREATION
                # ============================================================
                # Every AML alert gets one OPEN case so the investigator can
                # verify the alert and later resolve/close the case.
                # ============================================================

                case_id = f"CASE_{uuid4().hex[:10].upper()}"

                case_priority = str(
                    aml_result.get("severity", "MEDIUM")
                ).upper()

                if case_priority not in [
                    "LOW",
                    "MEDIUM",
                    "HIGH",
                    "CRITICAL"
                ]:
                    case_priority = "MEDIUM"

                case_customer = connection.execute(
                    text("""
                        SELECT customer_id
                        FROM accounts
                        WHERE account_id = :account_id
                    """),
                    {
                        "account_id":
                            transaction.source_account_id
                    }
                ).mappings().first()

                case_customer_id = (
                    case_customer["customer_id"]
                    if case_customer
                    else None
                )

                connection.execute(
                    text("""
                        INSERT INTO cases (
                            case_id,
                            alert_id,
                            customer_id,
                            case_status,
                            priority,
                            assigned_to,
                            notes
                        )
                        VALUES (
                            :case_id,
                            :alert_id,
                            :customer_id,
                            'OPEN',
                            :priority,
                            NULL,
                            :notes
                        )
                    """),
                    {
                        "case_id": case_id,
                        "alert_id": alert_id,
                        "customer_id": case_customer_id,
                        "priority": case_priority,
                        "notes": (
                            f"Automatically created for AML alert {alert_id} "
                            f"({aml_result['alert_type']}) on transaction "
                            f"{transaction_id}."
                        )
                    }
                )

                alerts_created.append(
                    {
                        "alert_id": alert_id,
                        "alert_type": aml_result["alert_type"],
                        "severity": aml_result["severity"],
                        "risk_score": aml_result["risk_score"],
                        "description": aml_result["description"],
                        "status": "OPEN",
                        "case_id": case_id,
                        "case_status": "OPEN"
                    }
                )

                # ============================================================
                # AUTOMATIC AML ALERT NOTIFICATION
                # ============================================================

                notification_alert = {
                    "alert_id": alert_id,
                    "transaction_id": transaction_id,
                    "alert_type": aml_result["alert_type"],
                    "severity": aml_result["severity"],
                    "risk_score": aml_result["risk_score"]
                }

                try:

                    create_aml_alert_notification(
                        notification_alert
                    )

                except Exception:

                    # Notification failure must not roll back the AML alert
                    # or its case.
                    pass

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

    # ========================================================
    # AUDIT TRAIL
    # ========================================================

    try:

        create_audit_log(
            user_id=current_user["user_id"],
            username=current_user["username"],
            user_role=current_user["role"],
            action="CREATE_TRANSACTION",
            resource_type="TRANSACTION",
            resource_id=transaction_id,
            description=(
                f"Transaction created successfully "
                f"with amount {transaction.amount} "
                f"{transaction.currency}"
            )
        )

    except Exception:

        # Audit failure must not break transaction processing.
        pass

    # ========================================================
    # API RESPONSE
    # ========================================================

    # --------------------------------------------------------
    # AML outcome for the transaction creator
    # --------------------------------------------------------

    triggered_rules = [
        alert["alert_type"]
        for alert in alerts_created
    ]

    aml_status = (
        "SAFE"
        if not alerts_created
        else "AML_REVIEW_REQUIRED"
    )

    response = {

        "message":
            "Transaction created successfully",

        "transaction_id":
            transaction_id,

        "event_id":
            event_id,

        "status":
            "accepted",

        "transaction_status":
            aml_status,

        "source_account_id":
            transaction.source_account_id,

        "destination_account_id":
            transaction.destination_account_id,

        "amount":
            float(transaction.amount),

        "aml_check": {

            "checked":
                True,

            "alert_created":
                len(alerts_created) > 0,

            "triggered_rules":
                triggered_rules,

            "rules_checked": [
                "LARGE_TRANSACTION",
                "HIGH_VELOCITY",
                "STRUCTURING",
                "RAPID_FUND_MOVEMENT",
                "UNUSUAL_TRANSACTION_AMOUNT",
                "UNUSUAL_TRANSACTION_FREQUENCY",
                "ROUND_NUMBER_TRANSACTION",
                "MULTIPLE_COUNTERPARTIES"
            ]
        },

        "risk_assessment": {

            "overall_risk_score":
                risk_assessment[
                    "overall_risk_score"
                ],

            "risk_level":
                risk_assessment[
                    "risk_level"
                ],

            "triggered_rule_count":
                risk_assessment[
                    "triggered_rule_count"
                ]
        },

        "notification": {

            "created":
                len(alerts_created) > 0,

            "message": (
                "AML alert notification created"
                if alerts_created
                else "No notification required for a safe transaction"
            )
        }
    }

    # --------------------------------------------------------
    # Add alerts to response
    # --------------------------------------------------------

    if alerts_created:

        response["alerts"] = alerts_created

        response["alert"] = alerts_created[0]

    return response

# ============================================================
# GET TRANSACTION INVESTIGATION DETAILS
# ============================================================

@app.get("/api/v1/transactions/{transaction_id}")
# ============================================================
# GET ALL TRANSACTIONS
# ============================================================

@app.get("/api/v1/transactions")
def get_all_transactions(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    try:

        with engine.connect() as connection:

            transactions = connection.execute(
                text("""
                    SELECT
                        t.transaction_id,
                        t.event_id,
                        t.source_account_id,
                        t.destination_account_id,
                        t.amount,
                        t.currency,
                        t.channel,
                        t.occurred_at,
                        t.transaction_type,
                        t.created_at

                    FROM transactions t

                    ORDER BY t.created_at DESC

                    LIMIT 100
                """)
            ).mappings().all()

            transaction_list = []

            for transaction in transactions:

                # ------------------------------------------------
                # Get alerts for this transaction
                # ------------------------------------------------

                alerts = connection.execute(
                    text("""
                        SELECT
                            alert_id,
                            alert_type,
                            severity,
                            risk_score,
                            status,
                            description,
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

                # ------------------------------------------------
                # Calculate transaction risk
                # ------------------------------------------------

                triggered_alerts = []

                for alert in alerts:

                    triggered_alerts.append(
                        {
                            "risk_score":
                                float(alert["risk_score"])
                        }
                    )

                risk_assessment = calculate_overall_risk(
                    triggered_alerts
                )

                # ------------------------------------------------
                # Transaction status
                # ------------------------------------------------

                if alerts:

                    transaction_status = (
                        "AML_REVIEW_REQUIRED"
                    )

                else:

                    transaction_status = "SAFE"

                # ------------------------------------------------
                # Convert alerts
                # ------------------------------------------------

                alert_list = []

                for alert in alerts:

                    alert_list.append(
                        {
                            "alert_id":
                                alert["alert_id"],

                            "alert_type":
                                alert["alert_type"],

                            "severity":
                                alert["severity"],

                            "risk_score":
                                float(
                                    alert["risk_score"]
                                ),

                            "status":
                                alert["status"],

                            "description":
                                alert["description"],

                            "created_at":
                                (
                                    alert["created_at"].isoformat()
                                    if alert["created_at"]
                                    else None
                                )
                        }
                    )

                # ------------------------------------------------
                # Add transaction
                # ------------------------------------------------

                transaction_list.append(
                    {
                        "transaction_id":
                            transaction["transaction_id"],

                        "event_id":
                            transaction["event_id"],

                        "source_account_id":
                            transaction["source_account_id"],

                        "destination_account_id":
                            transaction["destination_account_id"],

                        "amount":
                            float(transaction["amount"]),

                        "currency":
                            transaction["currency"],

                        "channel":
                            transaction["channel"],

                        "occurred_at":
                            (
                                transaction["occurred_at"].isoformat()
                                if transaction["occurred_at"]
                                else None
                            ),

                        "transaction_type":
                            transaction["transaction_type"],

                        "created_at":
                            (
                                transaction["created_at"].isoformat()
                                if transaction["created_at"]
                                else None
                            ),

                        "transaction_status":
                            transaction_status,

                        "risk_score":
                            risk_assessment[
                                "overall_risk_score"
                            ],

                        "risk_level":
                            risk_assessment[
                                "risk_level"
                            ],

                        "triggered_rule_count":
                            risk_assessment[
                                "triggered_rule_count"
                            ],

                        "alert_count":
                            len(alert_list),

                        "alerts":
                            alert_list
                    }
                )

            return {
                "count": len(transaction_list),
                "transactions": transaction_list
            }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Error loading transactions: {str(e)}"
        )
def get_transaction_details(transaction_id: str):

    try:

        with engine.connect() as connection:

            # ------------------------------------------------
            # 1. Get transaction + customer information
            # ------------------------------------------------

            transaction = connection.execute(
                text("""
                    SELECT
                        t.transaction_id,
                        t.event_id,
                        t.source_account_id,
                        t.destination_account_id,
                        t.amount,
                        t.currency,
                        t.channel,
                        t.occurred_at,
                        t.transaction_type,
                        t.created_at,

                        a.customer_id

                    FROM transactions t

                    LEFT JOIN accounts a
                        ON a.account_id = t.source_account_id

                    WHERE t.transaction_id = :transaction_id
                """),
                {
                    "transaction_id": transaction_id
                }
            ).mappings().first()

            if not transaction:

                raise HTTPException(
                    status_code=404,
                    detail="Transaction not found"
                )

            # ------------------------------------------------
            # 2. Get alerts related to transaction
            # ------------------------------------------------

            alerts = connection.execute(
                text("""
                    SELECT
                        alert_id,
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
                    "transaction_id": transaction_id
                }
            ).mappings().all()

            alert_list = []

            for alert in alerts:

                alert_list.append({
                    "alert_id":
                        alert["alert_id"],

                    "alert_type":
                        alert["alert_type"],

                    "severity":
                        alert["severity"],

                    "risk_score":
                        float(alert["risk_score"]),

                    "description":
                        alert["description"],

                    "status":
                        alert["status"],

                    "created_at":
                        (
                            alert["created_at"].isoformat()
                            if alert["created_at"]
                            else None
                        )
                })

            # ------------------------------------------------
            # 3. Get previous transactions
            # ------------------------------------------------

            previous_transactions = connection.execute(
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

                    WHERE source_account_id =
                          :source_account_id

                      AND transaction_id !=
                          :transaction_id

                      AND occurred_at <=
                          :occurred_at

                    ORDER BY occurred_at DESC

                    LIMIT 10
                """),
                {
                    "source_account_id":
                        transaction["source_account_id"],

                    "transaction_id":
                        transaction_id,

                    "occurred_at":
                        transaction["occurred_at"]
                }
            ).mappings().all()

            previous_transaction_list = []

            for row in previous_transactions:

                previous_transaction_list.append({
                    "transaction_id":
                        row["transaction_id"],

                    "event_id":
                        row["event_id"],

                    "source_account_id":
                        row["source_account_id"],

                    "destination_account_id":
                        row["destination_account_id"],

                    "amount":
                        float(row["amount"]),

                    "currency":
                        row["currency"],

                    "channel":
                        row["channel"],

                    "occurred_at":
                        (
                            row["occurred_at"].isoformat()
                            if row["occurred_at"]
                            else None
                        ),

                    "transaction_type":
                        row["transaction_type"]
                })

            # ------------------------------------------------
            # 4. Calculate transaction risk
            # ------------------------------------------------

            triggered_alerts = []

            for alert in alerts:

                triggered_alerts.append({
                    "risk_score":
                        float(alert["risk_score"])
                })

            risk_assessment = calculate_overall_risk(
                triggered_alerts
            )

            # ------------------------------------------------
            # 5. Return investigation information
            # ------------------------------------------------

            return {

                "transaction": {

                    "transaction_id":
                        transaction["transaction_id"],

                    "event_id":
                        transaction["event_id"],

                    "source_account_id":
                        transaction["source_account_id"],

                    "destination_account_id":
                        transaction["destination_account_id"],

                    "customer_id":
                        transaction["customer_id"],

                    "amount":
                        float(transaction["amount"]),

                    "currency":
                        transaction["currency"],

                    "channel":
                        transaction["channel"],

                    "occurred_at":
                        (
                            transaction["occurred_at"].isoformat()
                            if transaction["occurred_at"]
                            else None
                        ),

                    "transaction_type":
                        transaction["transaction_type"],

                    "created_at":
                        (
                            transaction["created_at"].isoformat()
                            if transaction["created_at"]
                            else None
                        )
                },

                "risk_assessment": {

                    "overall_risk_score":
                        risk_assessment[
                            "overall_risk_score"
                        ],

                    "risk_level":
                        risk_assessment[
                            "risk_level"
                        ],

                    "triggered_rule_count":
                        risk_assessment[
                            "triggered_rule_count"
                        ]
                },

                "alerts": alert_list,

                "previous_transactions":
                    previous_transaction_list,

                "investigation_summary": {

                    "alert_count":
                        len(alert_list),

                    "previous_transaction_count":
                        len(previous_transaction_list),

                    "requires_investigation":
                        len(alert_list) > 0
                }
            }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )

# ============================================================
# CUSTOMER INVESTIGATION
# ============================================================

@app.get("/api/v1/customers/{customer_id}/investigation")
def get_customer_investigation_details(customer_id: str):

    """
    Get complete AML investigation information
    for a customer.

    Includes:

    - Customer information
    - Transaction summary
    - Alert summary
    - Core AML rule violations
    - Advanced AML rule violations
    - Customer risk assessment
    - Complete transaction history
    - Complete alert history
    - Investigation priority
    """

    try:

        investigation = get_customer_investigation(
            customer_id
        )

        # ----------------------------------------------------
        # Customer not found
        # ----------------------------------------------------

        if investigation is None:

            raise HTTPException(
                status_code=404,
                detail="Customer not found"
            )

        return investigation

    except HTTPException:
        raise

    except RuntimeError as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Customer investigation error: {str(e)}"
        )
    
# ============================================================
# CUSTOMER RISK PROFILING
# ============================================================

@app.get("/api/v1/customers/{customer_id}/risk")
def get_customer_risk(
    customer_id: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    """
    Calculate customer-level AML risk.

    The customer's risk is calculated from:

    - Number of transactions
    - Number of AML alerts
    - Large transaction alerts
    - High velocity alerts
    - Structuring alerts
    """

    # --------------------------------------------------------
    # SQL: CUSTOMER + TRANSACTION + ALERT INFORMATION
    # --------------------------------------------------------

    customer_sql = text("""
        SELECT
            c.customer_id
        FROM customers c
        WHERE c.customer_id = :customer_id
    """)

    transaction_count_sql = text("""
        SELECT COUNT(*)
        FROM transactions t
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
    """)

    alert_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
    """)

    large_transaction_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
          AND al.alert_type = 'LARGE_TRANSACTION'
    """)

    high_velocity_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
          AND al.alert_type = 'HIGH_VELOCITY'
    """)

    structuring_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
          AND al.alert_type = 'STRUCTURING'
    """)

    try:

        with engine.connect() as connection:

            # ------------------------------------------------
            # 1. Check customer
            # ------------------------------------------------

            customer = connection.execute(
                customer_sql,
                {
                    "customer_id":
                        customer_id
                }
            ).fetchone()

            if not customer:

                raise HTTPException(
                    status_code=404,
                    detail="Customer not found"
                )

            # ------------------------------------------------
            # 2. Count transactions
            # ------------------------------------------------

            transaction_count = connection.execute(
                transaction_count_sql,
                {
                    "customer_id":
                        customer_id
                }
            ).scalar()

            # ------------------------------------------------
            # 3. Count all AML alerts
            # ------------------------------------------------

            alert_count = connection.execute(
                alert_count_sql,
                {
                    "customer_id":
                        customer_id
                }
            ).scalar()

            # ------------------------------------------------
            # 4. Count large transaction alerts
            # ------------------------------------------------

            large_transaction_count = connection.execute(
                large_transaction_count_sql,
                {
                    "customer_id":
                        customer_id
                }
            ).scalar()

            # ------------------------------------------------
            # 5. Count high velocity alerts
            # ------------------------------------------------

            high_velocity_count = connection.execute(
                high_velocity_count_sql,
                {
                    "customer_id":
                        customer_id
                }
            ).scalar()

            # ------------------------------------------------
            # 6. Count structuring alerts
            # ------------------------------------------------

            structuring_count = connection.execute(
                structuring_count_sql,
                {
                    "customer_id":
                        customer_id
                }
            ).scalar()

            # ------------------------------------------------
            # 7. Calculate customer risk
            # ------------------------------------------------

            risk_assessment = calculate_customer_risk(
                transaction_count=transaction_count,
                alert_count=alert_count,
                large_transaction_count=
                    large_transaction_count,
                high_velocity_count=
                    high_velocity_count,
                structuring_count=
                    structuring_count
            )

            # ------------------------------------------------
            # 8. Return customer risk profile
            # ------------------------------------------------

            return {

                "customer_id":
                    customer_id,

                "transaction_count":
                    transaction_count,

                "alert_count":
                    alert_count,

                "large_transaction_count":
                    large_transaction_count,

                "high_velocity_count":
                    high_velocity_count,

                "structuring_count":
                    structuring_count,

                "customer_risk_score":
                    risk_assessment[
                        "customer_risk_score"
                    ],

                "risk_level":
                    risk_assessment[
                        "risk_level"
                    ]
            }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# GET ALL ALERTS
# ============================================================

@app.get("/api/v1/alerts")
def get_alerts(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    sql = text("""
        SELECT
            a.alert_id,
            a.transaction_id,
            a.alert_type,
            a.severity,
            a.risk_score,
            a.description,
            a.status,
            a.created_at,

            c.case_id,
            c.case_status,

            t.amount,
            t.source_account_id,
            t.destination_account_id,

            acc.customer_id

        FROM alerts a

        LEFT JOIN transactions t
            ON t.transaction_id = a.transaction_id

        LEFT JOIN cases c
            ON c.alert_id = a.alert_id

        LEFT JOIN accounts acc
            ON acc.account_id = t.source_account_id

        ORDER BY a.created_at DESC
    """)

    try:

        with engine.connect() as connection:

            result = connection.execute(sql)

            alerts = []

            for row in result:

                # --------------------------------------------
                # Calculate risk level
                # --------------------------------------------

                risk_score = float(row.risk_score)

                if risk_score >= 90:
                    risk_level = "CRITICAL"

                elif risk_score >= 70:
                    risk_level = "HIGH"

                elif risk_score >= 40:
                    risk_level = "MEDIUM"

                else:
                    risk_level = "LOW"

                # --------------------------------------------
                # Build alert response
                # --------------------------------------------

                alerts.append(
                    {

                        "alert_id":
                            row.alert_id,

                        "transaction_id":
                            row.transaction_id,

                        "alert_type":
                            row.alert_type,

                        "severity":
                            row.severity,

                        "risk_score":
                            risk_score,

                        "risk_level":
                            risk_level,

                        "status":
                            row.status,

                        "case_id":
                            row.case_id,

                        "case_status":
                            row.case_status,

                        "description":
                            row.description,

                        "customer_id":
                            row.customer_id,

                        "amount":
                            float(row.amount)
                            if row.amount is not None
                            else None,

                        "source_account_id":
                            row.source_account_id,

                        "destination_account_id":
                            row.destination_account_id,

                        "created_at":
                            (
                                row.created_at.isoformat()
                                if row.created_at
                                else None
                            )
                    }
                )

            return {
                "count":
                    len(alerts),

                "alerts":
                    alerts
            }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
# ============================================================
# UPDATE ALERT STATUS
# ============================================================

@app.patch("/api/v1/alerts/{alert_id}/status")
def update_alert_status(
    alert_id: str,
    status_update: AlertStatusUpdate,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER"
        )
    )
):

    allowed_statuses = [
        "OPEN",
        "UNDER_REVIEW",
        "ESCALATED",
        "RESOLVED",
        "FALSE_POSITIVE"
    ]

    new_status = status_update.status.upper()

    if new_status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid status. "
                f"Allowed values: {allowed_statuses}"
            )
        )

    sql = text("""
        UPDATE alerts
        SET status = :status
        WHERE alert_id = :alert_id
        RETURNING
            alert_id,
            transaction_id,
            alert_type,
            severity,
            risk_score,
            description,
            status,
            created_at
    """)

    try:

        with engine.begin() as connection:

            result = connection.execute(
                sql,
                {
                    "alert_id":
                        alert_id,

                    "status":
                        new_status
                }
            ).fetchone()

            if not result:

                raise HTTPException(
                    status_code=404,
                    detail="Alert not found"
                )

            # Keep the linked case synchronized with the alert workflow.
            case_status_map = {
                "OPEN": "OPEN",
                "UNDER_REVIEW": "UNDER_REVIEW",
                "ESCALATED": "ESCALATED",
                "RESOLVED": "RESOLVED",
                "FALSE_POSITIVE": "CLOSED"
            }

            mapped_case_status = case_status_map.get(new_status)

            if mapped_case_status:

                connection.execute(
                    text("""
                        UPDATE cases
                        SET case_status = :case_status,
                            disposition = CASE
                                WHEN :new_status = 'FALSE_POSITIVE'
                                    THEN 'FALSE_POSITIVE'
                                ELSE disposition
                            END,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE alert_id = :alert_id
                    """),
                    {
                        "case_status": mapped_case_status,
                        "new_status": new_status,
                        "alert_id": alert_id
                    }
                )

            response = {

                "message":
                    "Alert status updated successfully",

                "alert": {

                    "alert_id":
                        result.alert_id,

                    "transaction_id":
                        result.transaction_id,

                    "alert_type":
                        result.alert_type,

                    "severity":
                        result.severity,

                    "risk_score":
                        float(result.risk_score),

                    "description":
                        result.description,

                    "status":
                        result.status,

                    "created_at":
                        (
                            result.created_at.isoformat()
                            if result.created_at
                            else None
                        )
                }
            }

            try:

                create_audit_log(
                    user_id=current_user["user_id"],
                    username=current_user["username"],
                    user_role=current_user["role"],
                    action="UPDATE_ALERT_STATUS",
                    resource_type="ALERT",
                    resource_id=alert_id,
                    description=f"Alert status changed to {new_status}"
                )

            except Exception:

                # Audit failure must not break the existing operation.
                pass

            return response

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# GET ALERT INVESTIGATION DETAILS
# ============================================================

@app.get("/api/v1/alerts/{alert_id}")
def get_alert_details(
    alert_id: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    # --------------------------------------------------------
    # 1. Get alert
    # --------------------------------------------------------

    alert_sql = text("""
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
    """)

    # --------------------------------------------------------
    # 2. Get related transaction
    # --------------------------------------------------------

    transaction_sql = text("""
        SELECT
            transaction_id,
            event_id,
            source_account_id,
            destination_account_id,
            amount,
            currency,
            channel,
            occurred_at,
            transaction_type,
            created_at
        FROM transactions
        WHERE transaction_id = :transaction_id
    """)

    # --------------------------------------------------------
    # 3. Get previous transactions
    # --------------------------------------------------------

    previous_transactions_sql = text("""
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
        WHERE source_account_id = :source_account_id

          AND transaction_id != :transaction_id

          AND occurred_at <= :occurred_at

        ORDER BY occurred_at DESC

        LIMIT 10
    """)

    try:

        with engine.connect() as connection:

            # ----------------------------------------------
            # Find alert
            # ----------------------------------------------

            alert = connection.execute(
                alert_sql,
                {
                    "alert_id":
                        alert_id
                }
            ).fetchone()

            if not alert:

                raise HTTPException(
                    status_code=404,
                    detail="Alert not found"
                )

            # ----------------------------------------------
            # Find related transaction
            # ----------------------------------------------

            transaction = connection.execute(
                transaction_sql,
                {
                    "transaction_id":
                        alert.transaction_id
                }
            ).fetchone()

            if not transaction:

                raise HTTPException(
                    status_code=404,
                    detail=(
                        "Transaction associated with "
                        "alert not found"
                    )
                )

            # ----------------------------------------------
            # Find previous transactions
            # ----------------------------------------------

            previous_transactions = connection.execute(
                previous_transactions_sql,
                {
                    "source_account_id":
                        transaction.source_account_id,

                    "transaction_id":
                        transaction.transaction_id,

                    "occurred_at":
                        transaction.occurred_at
                }
            ).fetchall()

            # ----------------------------------------------
            # Convert previous transactions
            # ----------------------------------------------

            previous_transaction_list = []

            for row in previous_transactions:

                previous_transaction_list.append(
                    {
                        "transaction_id":
                            row.transaction_id,

                        "source_account_id":
                            row.source_account_id,

                        "destination_account_id":
                            row.destination_account_id,

                        "amount":
                            float(row.amount),

                        "currency":
                            row.currency,

                        "channel":
                            row.channel,

                        "occurred_at":
                            (
                                row.occurred_at.isoformat()
                                if row.occurred_at
                                else None
                            ),

                        "transaction_type":
                            row.transaction_type
                    }
                )

            # ----------------------------------------------
            # Return investigation details
            # ----------------------------------------------

            return {

                "alert": {

                    "alert_id":
                        alert.alert_id,

                    "transaction_id":
                        alert.transaction_id,

                    "alert_type":
                        alert.alert_type,

                    "severity":
                        alert.severity,

                    "risk_score":
                        float(alert.risk_score),

                    "description":
                        alert.description,

                    "status":
                        alert.status,

                    "created_at":
                        (
                            alert.created_at.isoformat()
                            if alert.created_at
                            else None
                        )
                },

                "transaction": {

                    "transaction_id":
                        transaction.transaction_id,

                    "event_id":
                        transaction.event_id,

                    "source_account_id":
                        transaction.source_account_id,

                    "destination_account_id":
                        transaction.destination_account_id,

                    "amount":
                        float(transaction.amount),

                    "currency":
                        transaction.currency,

                    "channel":
                        transaction.channel,

                    "occurred_at":
                        (
                            transaction.occurred_at.isoformat()
                            if transaction.occurred_at
                            else None
                        ),

                    "transaction_type":
                        transaction.transaction_type,

                    "created_at":
                        (
                            transaction.created_at.isoformat()
                            if transaction.created_at
                            else None
                        )
                },

                "previous_transactions":
                    previous_transaction_list
            }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# ALL CUSTOMERS RISK
# ============================================================

@app.get("/api/v1/customers/risk")
def get_all_customers_risk(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):
    """
    Calculate AML risk profiles for all customers.

    Uses the same calculate_customer_risk() engine as the
    individual customer risk endpoint.
    """

    customer_sql = text("""
        SELECT customer_id
        FROM customers
        ORDER BY customer_id
    """)

    transaction_count_sql = text("""
        SELECT COUNT(*)
        FROM transactions t
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
    """)

    alert_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
    """)

    large_transaction_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
          AND al.alert_type = 'LARGE_TRANSACTION'
    """)

    high_velocity_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
          AND al.alert_type = 'HIGH_VELOCITY'
    """)

    structuring_count_sql = text("""
        SELECT COUNT(*)
        FROM alerts al
        INNER JOIN transactions t
            ON t.transaction_id = al.transaction_id
        INNER JOIN accounts a
            ON a.account_id = t.source_account_id
        WHERE a.customer_id = :customer_id
          AND al.alert_type = 'STRUCTURING'
    """)

    try:

        with engine.connect() as connection:

            customers = connection.execute(
                customer_sql
            ).mappings().all()

            results = []

            for customer in customers:

                customer_id = customer["customer_id"]

                transaction_count = connection.execute(
                    transaction_count_sql,
                    {"customer_id": customer_id}
                ).scalar()

                alert_count = connection.execute(
                    alert_count_sql,
                    {"customer_id": customer_id}
                ).scalar()

                large_transaction_count = connection.execute(
                    large_transaction_count_sql,
                    {"customer_id": customer_id}
                ).scalar()

                high_velocity_count = connection.execute(
                    high_velocity_count_sql,
                    {"customer_id": customer_id}
                ).scalar()

                structuring_count = connection.execute(
                    structuring_count_sql,
                    {"customer_id": customer_id}
                ).scalar()

                # --------------------------------------------
                # Use the SAME customer risk engine as the
                # individual customer risk endpoint.
                # --------------------------------------------

                risk_assessment = calculate_customer_risk(
                    transaction_count=transaction_count,
                    alert_count=alert_count,
                    large_transaction_count=large_transaction_count,
                    high_velocity_count=high_velocity_count,
                    structuring_count=structuring_count
                )

                results.append({
                    "customer_id": customer_id,
                    "transaction_count": int(transaction_count or 0),
                    "alert_count": int(alert_count or 0),
                    "large_transaction_count": int(large_transaction_count or 0),
                    "high_velocity_count": int(high_velocity_count or 0),
                    "structuring_count": int(structuring_count or 0),
                    "customer_risk_score": risk_assessment[
                        "customer_risk_score"
                    ],
                    "risk_level": risk_assessment[
                        "risk_level"
                    ]
                })

            # -----------------------------------------------
            # Sort highest-risk customers first.
            # -----------------------------------------------

            risk_priority = {
                "CRITICAL": 4,
                "HIGH": 3,
                "MEDIUM": 2,
                "LOW": 1
            }

            results.sort(
                key=lambda customer: (
                    risk_priority[customer["risk_level"]],
                    customer["customer_risk_score"],
                    customer["alert_count"]
                ),
                reverse=True
            )

            return {
                "total_customers": len(results),
                "customers": results
            }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# CREATE CASE
# ============================================================

@app.post("/api/v1/cases")
def create_case(
    case: CaseCreate,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    allowed_priorities = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]

    priority = case.priority.upper()

    if priority not in allowed_priorities:
        raise HTTPException(
            status_code=400,
            detail=(
                "Invalid priority. "
                f"Allowed values: {allowed_priorities}"
            )
        )

    case_id = f"CASE_{uuid4().hex[:10].upper()}"

    try:

        with engine.begin() as connection:

            # ------------------------------------------------
            # Check alert
            # ------------------------------------------------

            alert = connection.execute(
                text("""
                    SELECT
                        a.alert_id,
                        a.transaction_id,
                        a.alert_type,
                        a.severity,
                        a.risk_score,
                        t.source_account_id
                    FROM alerts a
                    JOIN transactions t
                        ON t.transaction_id = a.transaction_id
                    WHERE a.alert_id = :alert_id
                """),
                {
                    "alert_id": case.alert_id
                }
            ).mappings().first()

            if not alert:
                raise HTTPException(
                    status_code=404,
                    detail="Alert not found"
                )

            # ------------------------------------------------
            # Find customer from source account
            # ------------------------------------------------

            customer = connection.execute(
                text("""
                    SELECT customer_id
                    FROM accounts
                    WHERE account_id = :account_id
                """),
                {
                    "account_id":
                        alert["source_account_id"]
                }
            ).mappings().first()

            customer_id = (
                customer["customer_id"]
                if customer
                else None
            )

            # ------------------------------------------------
            # Check if case already exists
            # ------------------------------------------------

            existing_case = connection.execute(
                text("""
                    SELECT case_id
                    FROM cases
                    WHERE alert_id = :alert_id
                """),
                {
                    "alert_id": case.alert_id
                }
            ).mappings().first()

            if existing_case:
                raise HTTPException(
                    status_code=409,
                    detail=(
                        "A case already exists for this alert"
                    )
                )

            # ------------------------------------------------
            # Create case
            # ------------------------------------------------

            result = connection.execute(
                text("""
                    INSERT INTO cases (
                        case_id,
                        alert_id,
                        customer_id,
                        case_status,
                        priority,
                        assigned_to,
                        notes
                    )
                    VALUES (
                        :case_id,
                        :alert_id,
                        :customer_id,
                        'OPEN',
                        :priority,
                        :assigned_to,
                        :notes
                    )
                    RETURNING
                        case_id,
                        alert_id,
                        customer_id,
                        case_status,
                        priority,
                        assigned_to,
                        disposition,
                        notes,
                        created_at,
                        updated_at
                """),
                {
                    "case_id": case_id,
                    "alert_id": case.alert_id,
                    "customer_id": customer_id,
                    "priority": priority,
                    "assigned_to": case.assigned_to,
                    "notes": case.notes
                }
            ).mappings().first()

            response = {
                "message": "Case created successfully",
                "case": {
                    "case_id":
                        result["case_id"],

                    "alert_id":
                        result["alert_id"],

                    "customer_id":
                        result["customer_id"],

                    "case_status":
                        result["case_status"],

                    "priority":
                        result["priority"],

                    "assigned_to":
                        result["assigned_to"],

                    "disposition":
                        result["disposition"],

                    "notes":
                        result["notes"],

                    "created_at":
                        result["created_at"].isoformat()
                        if result["created_at"]
                        else None,

                    "updated_at":
                        result["updated_at"].isoformat()
                        if result["updated_at"]
                        else None
                }
            }

            try:

                create_audit_log(
                    user_id=current_user["user_id"],
                    username=current_user["username"],
                    user_role=current_user["role"],
                    action="CREATE_CASE",
                    resource_type="CASE",
                    resource_id=case_id,
                    description=f"Case created for alert {case.alert_id}"
                )

            except Exception:

                # Audit failure must not break the existing operation.
                pass

            return response

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# GET ALL CASES
# ============================================================

@app.get("/api/v1/cases")
def get_cases(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):
    try:

        with engine.connect() as connection:

            result = connection.execute(
                text("""
                    SELECT
                        case_id,
                        alert_id,
                        customer_id,
                        case_status,
                        priority,
                        assigned_to,
                        disposition,
                        notes,
                        created_at,
                        updated_at
                    FROM cases
                    ORDER BY created_at DESC
                """)
            ).mappings().all()

            cases = []

            for row in result:

                cases.append({
                    "case_id":
                        row["case_id"],

                    "alert_id":
                        row["alert_id"],

                    "customer_id":
                        row["customer_id"],

                    "case_status":
                        row["case_status"],

                    "priority":
                        row["priority"],

                    "assigned_to":
                        row["assigned_to"],

                    "disposition":
                        row["disposition"],

                    "notes":
                        row["notes"],

                    "created_at":
                        row["created_at"].isoformat()
                        if row["created_at"]
                        else None,

                    "updated_at":
                        row["updated_at"].isoformat()
                        if row["updated_at"]
                        else None
                })

            return {
                "count": len(cases),
                "cases": cases
            }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# CASE SUMMARY
# IMPORTANT:
# This route MUST be before /api/v1/cases/{case_id}
# ============================================================

@app.get("/api/v1/cases/summary")
def get_case_summary(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):
    with engine.connect() as conn:

        # Total cases
        total_cases = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM cases
            """)
        ).scalar()

        # Cases by status
        status_rows = conn.execute(
            text("""
                SELECT case_status, COUNT(*)
                FROM cases
                GROUP BY case_status
            """)
        ).fetchall()

        status_summary = {
            row[0]: row[1]
            for row in status_rows
        }

        # Cases by priority
        priority_rows = conn.execute(
            text("""
                SELECT priority, COUNT(*)
                FROM cases
                GROUP BY priority
            """)
        ).fetchall()

        priority_summary = {
            row[0]: row[1]
            for row in priority_rows
        }

        # Cases by disposition
        disposition_rows = conn.execute(
            text("""
                SELECT disposition, COUNT(*)
                FROM cases
                WHERE disposition IS NOT NULL
                GROUP BY disposition
            """)
        ).fetchall()

        disposition_summary = {
            row[0]: row[1]
            for row in disposition_rows
        }

    return {
        "total_cases": total_cases,
        "status_summary": status_summary,
        "priority_summary": priority_summary,
        "disposition_summary": disposition_summary
    }


# ============================================================
# GET CASE DETAILS
# ============================================================

@app.get("/api/v1/cases/{case_id}")
def get_case(
    case_id: str,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):
    try:

        with engine.connect() as connection:

            case = connection.execute(
                text("""
                    SELECT
                        c.case_id,
                        c.alert_id,
                        c.customer_id,
                        c.case_status,
                        c.priority,
                        c.assigned_to,
                        c.disposition,
                        c.notes,
                        c.created_at,
                        c.updated_at,

                        a.alert_type,
                        a.severity,
                        a.risk_score,
                        a.description,

                        a.transaction_id

                    FROM cases c

                    JOIN alerts a
                        ON a.alert_id = c.alert_id

                    WHERE c.case_id = :case_id
                """),
                {
                    "case_id": case_id
                }
            ).mappings().first()

            if not case:

                raise HTTPException(
                    status_code=404,
                    detail="Case not found"
                )

            return {
                "case": {
                    "case_id":
                        case["case_id"],

                    "alert_id":
                        case["alert_id"],

                    "customer_id":
                        case["customer_id"],

                    "case_status":
                        case["case_status"],

                    "priority":
                        case["priority"],

                    "assigned_to":
                        case["assigned_to"],

                    "disposition":
                        case["disposition"],

                    "notes":
                        case["notes"],

                    "created_at":
                        case["created_at"].isoformat()
                        if case["created_at"]
                        else None,

                    "updated_at":
                        case["updated_at"].isoformat()
                        if case["updated_at"]
                        else None
                },

                "alert": {
                    "alert_id":
                        case["alert_id"],

                    "alert_type":
                        case["alert_type"],

                    "severity":
                        case["severity"],

                    "risk_score":
                        float(case["risk_score"]),

                    "description":
                        case["description"],

                    "transaction_id":
                        case["transaction_id"]
                }
            }

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


# ============================================================
# UPDATE CASE
# ============================================================

@app.patch("/api/v1/cases/{case_id}")
def update_case(
    case_id: str,
    case_update: CaseUpdate,
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER"
        )
    )
):

    allowed_statuses = [
        "OPEN",
        "UNDER_REVIEW",
        "ESCALATED",
        "RESOLVED",
        "CLOSED"
    ]

    allowed_priorities = [
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL"
    ]

    allowed_dispositions = [
        "TRUE_POSITIVE",
        "FALSE_POSITIVE",
        "SUSPICIOUS",
        "NO_ACTION"
    ]

    try:

        with engine.begin() as connection:

            existing = connection.execute(
                text("""
                    SELECT case_id
                    FROM cases
                    WHERE case_id = :case_id
                """),
                {
                    "case_id": case_id
                }
            ).mappings().first()

            if not existing:

                raise HTTPException(
                    status_code=404,
                    detail="Case not found"
                )

            updates = []
            params = {
                "case_id": case_id
            }

            if case_update.case_status is not None:

                status = case_update.case_status.upper()

                if status not in allowed_statuses:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Invalid case status. "
                            f"Allowed values: {allowed_statuses}"
                        )
                    )

                updates.append(
                    "case_status = :case_status"
                )

                params["case_status"] = status

            if case_update.priority is not None:

                priority = case_update.priority.upper()

                if priority not in allowed_priorities:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Invalid priority. "
                            f"Allowed values: {allowed_priorities}"
                        )
                    )

                updates.append(
                    "priority = :priority"
                )

                params["priority"] = priority

            if case_update.assigned_to is not None:

                updates.append(
                    "assigned_to = :assigned_to"
                )

                params["assigned_to"] = (
                    case_update.assigned_to
                )

            if case_update.disposition is not None:

                disposition = (
                    case_update.disposition.upper()
                )

                if disposition not in allowed_dispositions:

                    raise HTTPException(
                        status_code=400,
                        detail=(
                            "Invalid disposition. "
                            f"Allowed values: "
                            f"{allowed_dispositions}"
                        )
                    )

                updates.append(
                    "disposition = :disposition"
                )

                params["disposition"] = disposition

            if case_update.notes is not None:

                updates.append(
                    "notes = :notes"
                )

                params["notes"] = case_update.notes

            if not updates:

                raise HTTPException(
                    status_code=400,
                    detail="No fields provided for update"
                )

            updates.append(
                "updated_at = CURRENT_TIMESTAMP"
            )

            update_sql = text(
                f"""
                UPDATE cases
                SET {", ".join(updates)}
                WHERE case_id = :case_id
                RETURNING
                    case_id,
                    alert_id,
                    customer_id,
                    case_status,
                    priority,
                    assigned_to,
                    disposition,
                    notes,
                    created_at,
                    updated_at
                """
            )

            result = connection.execute(
                update_sql,
                params
            ).mappings().first()

            response = {
                "message": "Case updated successfully",
                "case": {
                    "case_id":
                        result["case_id"],

                    "alert_id":
                        result["alert_id"],

                    "customer_id":
                        result["customer_id"],

                    "case_status":
                        result["case_status"],

                    "priority":
                        result["priority"],

                    "assigned_to":
                        result["assigned_to"],

                    "disposition":
                        result["disposition"],

                    "notes":
                        result["notes"],

                    "created_at":
                        result["created_at"].isoformat()
                        if result["created_at"]
                        else None,

                    "updated_at":
                        result["updated_at"].isoformat()
                        if result["updated_at"]
                        else None
                }
            }

            try:

                create_audit_log(
                    user_id=current_user["user_id"],
                    username=current_user["username"],
                    user_role=current_user["role"],
                    action="UPDATE_CASE",
                    resource_type="CASE",
                    resource_id=case_id,
                    description="Case information updated"
                )

            except Exception:

                # Audit failure must not break the existing operation.
                pass

            return response

    except HTTPException:
        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )
# ============================================================
# AML DASHBOARD SUMMARY
# ============================================================

@app.get("/api/v1/dashboard/summary")
def get_dashboard_summary(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    with engine.connect() as conn:

        # ----------------------------------------------------
        # TRANSACTIONS
        # ----------------------------------------------------
        total_transactions = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM transactions
            """)
        ).scalar()

        # ----------------------------------------------------
        # ALERTS
        # ----------------------------------------------------
        total_alerts = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM alerts
            """)
        ).scalar()

        open_alerts = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM alerts
                WHERE status = 'OPEN'
            """)
        ).scalar()

        closed_alerts = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM alerts
                WHERE status = 'CLOSED'
            """)
        ).scalar()

        # ----------------------------------------------------
        # ALERT RISK SUMMARY
        # ----------------------------------------------------
        risk_rows = conn.execute(
            text("""
                SELECT risk_score, COUNT(*)
                FROM alerts
                GROUP BY risk_score
                ORDER BY risk_score
            """)
        ).fetchall()

        risk_summary = {
            "LOW": 0,
            "MEDIUM": 0,
            "HIGH": 0,
            "CRITICAL": 0
        }

        for risk_score, count in risk_rows:

            if risk_score >= 90:
                risk_summary["CRITICAL"] += count

            elif risk_score >= 70:
                risk_summary["HIGH"] += count

            elif risk_score >= 40:
                risk_summary["MEDIUM"] += count

            else:
                risk_summary["LOW"] += count

        # ----------------------------------------------------
        # CUSTOMERS
        # ----------------------------------------------------
        total_customers = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM customers
            """)
        ).scalar()

        # ----------------------------------------------------
        # CASES
        # ----------------------------------------------------
        total_cases = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM cases
            """)
        ).scalar()

        open_cases = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM cases
                WHERE case_status = 'OPEN'
            """)
        ).scalar()

        under_review_cases = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM cases
                WHERE case_status = 'UNDER_REVIEW'
            """)
        ).scalar()

        closed_cases = conn.execute(
            text("""
                SELECT COUNT(*)
                FROM cases
                WHERE case_status = 'CLOSED'
            """)
        ).scalar()

        # ----------------------------------------------------
        # CASE PRIORITY SUMMARY
        # ----------------------------------------------------
        priority_rows = conn.execute(
            text("""
                SELECT priority, COUNT(*)
                FROM cases
                GROUP BY priority
            """)
        ).fetchall()

        priority_summary = {}

        for priority, count in priority_rows:
            priority_summary[priority] = count

        # ----------------------------------------------------
        # CASE DISPOSITION SUMMARY
        # ----------------------------------------------------
        disposition_rows = conn.execute(
            text("""
                SELECT disposition, COUNT(*)
                FROM cases
                WHERE disposition IS NOT NULL
                GROUP BY disposition
            """)
        ).fetchall()

        disposition_summary = {}

        for disposition, count in disposition_rows:
            disposition_summary[disposition] = count

    return {
        "transactions": {
            "total": total_transactions
        },

        "alerts": {
            "total": total_alerts,
            "open": open_alerts,
            "closed": closed_alerts
        },

        "risk_summary": risk_summary,

        "customers": {
            "total": total_customers
        },

        "cases": {
            "total": total_cases,
            "open": open_cases,
            "under_review": under_review_cases,
            "closed": closed_cases
        },

        "case_priority_summary": priority_summary,

        "case_disposition_summary": disposition_summary
    }
# ============================================================
# REPORTING & EXPORT API
# ============================================================
# This module is isolated from existing AML processing.
# Existing transaction, alert, case, risk, audit,
# authentication, RBAC and dashboard logic remains unchanged.
# ============================================================


# ============================================================
# TRANSACTION REPORT
# ============================================================

@app.get("/api/v1/reports/transactions")
def get_transaction_report(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    try:

        transactions = generate_transaction_report()

        return {
            "count": len(transactions),
            "transactions": transactions
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Report generation error: {str(e)}"
        )


# ============================================================
# ALERT REPORT
# ============================================================

@app.get("/api/v1/reports/alerts")
def get_alert_report(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    try:

        alerts = generate_alert_report()

        return {
            "count": len(alerts),
            "alerts": alerts
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Report generation error: {str(e)}"
        )


# ============================================================
# CUSTOMER RISK REPORT
# ============================================================

@app.get("/api/v1/reports/customer-risk")
def get_customer_risk_report(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    try:

        customers = generate_customer_risk_report()

        return {
            "count": len(customers),
            "customers": customers
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Report generation error: {str(e)}"
        )


# ============================================================
# CASE REPORT
# ============================================================

@app.get("/api/v1/reports/cases")
def get_case_report(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    try:

        cases = generate_case_report()

        return {
            "count": len(cases),
            "cases": cases
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Report generation error: {str(e)}"
        )


# ============================================================
# AML INVESTIGATION REPORT
# ============================================================

@app.get("/api/v1/reports/investigation")
def get_investigation_report(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER"
        )
    )
):

    try:

        return generate_investigation_report()

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Report generation error: {str(e)}"
        )


# ============================================================
# ALERT CSV EXPORT
# ============================================================

@app.get("/api/v1/reports/alerts/csv")
def export_alert_report_csv(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    try:

        csv_data = export_to_csv(
            generate_alert_report()
        )

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=aml_alert_report.csv"
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"CSV export error: {str(e)}"
        )


# ============================================================
# TRANSACTION CSV EXPORT
# ============================================================

@app.get("/api/v1/reports/transactions/csv")
def export_transaction_report_csv(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    try:

        csv_data = export_to_csv(
            generate_transaction_report()
        )

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=aml_transaction_report.csv"
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"CSV export error: {str(e)}"
        )


# ============================================================
# CUSTOMER RISK CSV EXPORT
# ============================================================

@app.get("/api/v1/reports/customer-risk/csv")
def export_customer_risk_report_csv(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    try:

        csv_data = export_to_csv(
            generate_customer_risk_report()
        )

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=customer_risk_report.csv"
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"CSV export error: {str(e)}"
        )


# ============================================================
# CASE CSV EXPORT
# ============================================================

@app.get("/api/v1/reports/cases/csv")
def export_case_report_csv(
    current_user=Depends(
        require_roles(
            "ADMIN",
            "MANAGER",
            "ANALYST"
        )
    )
):

    try:

        csv_data = export_to_csv(
            generate_case_report()
        )

        return Response(
            content=csv_data,
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=aml_case_report.csv"
            }
        )

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"CSV export error: {str(e)}"
        )