from decimal import Decimal
from datetime import datetime, timedelta


# ============================================================
# ADVANCED AML RULE CONFIGURATION
# ============================================================

RAPID_MOVEMENT_MIN_AMOUNT = Decimal("100000")

RAPID_MOVEMENT_WINDOW_MINUTES = 60

RAPID_MOVEMENT_PERCENTAGE = Decimal("0.80")

UNUSUAL_AMOUNT_MULTIPLIER = Decimal("3")

UNUSUAL_FREQUENCY_MULTIPLIER = 3

ROUND_NUMBER_MIN_AMOUNT = Decimal("100000")

MULTIPLE_COUNTERPARTIES_LIMIT = 5

MULTIPLE_COUNTERPARTIES_WINDOW_MINUTES = 60


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def _to_decimal(value):
    """
    Safely convert numeric values to Decimal.
    """

    if isinstance(value, Decimal):
        return value

    return Decimal(str(value))


def _get_datetime(transaction):
    """
    Get transaction timestamp.

    Supports:
    - occurred_at
    - timestamp
    """

    value = transaction.get("occurred_at")

    if value is None:
        value = transaction.get("timestamp")

    if isinstance(value, str):
        value = datetime.fromisoformat(
            value.replace("Z", "+00:00")
        )

    return value


# ============================================================
# 1. RAPID FUND MOVEMENT
# ============================================================

def detect_rapid_fund_movement(
    transactions,
    min_amount=RAPID_MOVEMENT_MIN_AMOUNT,
    window_minutes=RAPID_MOVEMENT_WINDOW_MINUTES,
    movement_percentage=RAPID_MOVEMENT_PERCENTAGE
):
    """
    Detect situations where money enters an account and
    a large percentage of that amount leaves shortly afterward.

    Example:

    Incoming:
        ₹500,000

    Shortly afterward:

    Outgoing:
        ₹450,000

    This can indicate rapid movement of funds.
    """

    alerts = []

    incoming = [
        transaction
        for transaction in transactions
        if transaction.get("transaction_direction") == "IN"
        or transaction.get("direction") == "IN"
    ]

    outgoing = [
        transaction
        for transaction in transactions
        if transaction.get("transaction_direction") == "OUT"
        or transaction.get("direction") == "OUT"
    ]

    for incoming_txn in incoming:

        incoming_amount = _to_decimal(
            incoming_txn.get("amount", 0)
        )

        if incoming_amount < min_amount:
            continue

        incoming_time = _get_datetime(incoming_txn)

        if incoming_time is None:
            continue

        window_end = (
            incoming_time
            + timedelta(minutes=window_minutes)
        )

        outgoing_total = Decimal("0")

        related_outgoing = []

        for outgoing_txn in outgoing:

            outgoing_time = _get_datetime(outgoing_txn)

            if outgoing_time is None:
                continue

            if (
                incoming_time
                <= outgoing_time
                <= window_end
            ):

                outgoing_amount = _to_decimal(
                    outgoing_txn.get("amount", 0)
                )

                outgoing_total += outgoing_amount

                related_outgoing.append(
                    outgoing_txn
                )

        if outgoing_total == 0:
            continue

        percentage = (
            outgoing_total / incoming_amount
        )

        if percentage >= movement_percentage:

            alerts.append({
                "rule_type": "RAPID_FUND_MOVEMENT",
                "risk_score": 85,
                "risk_level": "HIGH",
                "trigger_transaction_id":
                    incoming_txn.get("transaction_id"),
                "description":
                    "Large incoming funds were followed "
                    "by rapid outgoing transactions.",
                "incoming_amount":
                    float(incoming_amount),
                "outgoing_amount":
                    float(outgoing_total),
                "movement_percentage":
                    round(float(percentage * 100), 2),
                "related_transaction_count":
                    len(related_outgoing)
            })

    return alerts


# ============================================================
# 2. UNUSUAL TRANSACTION AMOUNT
# ============================================================

def detect_unusual_transaction_amount(
    transactions,
    multiplier=UNUSUAL_AMOUNT_MULTIPLIER
):
    """
    Detect transactions significantly larger than the
    customer's historical average transaction amount.

    Important:
    The transaction being evaluated is excluded from its own
    historical baseline. This prevents the unusual transaction
    from increasing the average and hiding the anomaly.
    """

    alerts = []

    if not transactions:
        return alerts

    customer_transactions = {}

    for transaction in transactions:

        customer_id = transaction.get(
            "customer_id"
        )

        if not customer_id:
            continue

        customer_transactions.setdefault(
            customer_id,
            []
        ).append(transaction)

    for customer_id, customer_txns in customer_transactions.items():

        # We need at least 3 transactions so there is enough
        # historical activity to establish a baseline.
        if len(customer_txns) < 3:
            continue

        for index, transaction in enumerate(customer_txns):

            amount = _to_decimal(
                transaction.get("amount", 0)
            )

            if amount <= 0:
                continue

            # Exclude the current transaction from the
            # historical baseline.
            historical_transactions = (
                customer_txns[:index] +
                customer_txns[index + 1:]
            )

            historical_amounts = [
                _to_decimal(
                    historical_transaction.get(
                        "amount",
                        0
                    )
                )
                for historical_transaction
                in historical_transactions
            ]

            historical_amounts = [
                value
                for value in historical_amounts
                if value > 0
            ]

            if not historical_amounts:
                continue

            historical_average = (
                sum(historical_amounts)
                / len(historical_amounts)
            )

            if historical_average <= 0:
                continue

            if (
                amount
                >= historical_average * multiplier
            ):

                alerts.append({
                    "rule_type":
                        "UNUSUAL_TRANSACTION_AMOUNT",

                    "risk_score": 75,

                    "risk_level": "HIGH",

                    "customer_id":
                        customer_id,

                    "trigger_transaction_id":
                        transaction.get(
                            "transaction_id"
                        ),

                    "transaction_amount":
                        float(amount),

                    "historical_average":
                        round(
                            float(
                                historical_average
                            ),
                            2
                        ),

                    "description":
                        "Transaction amount is significantly "
                        "higher than the customer's historical "
                        "average."
                })

    return alerts


# ============================================================
# 3. UNUSUAL TRANSACTION FREQUENCY
# ============================================================

def detect_unusual_transaction_frequency(
    transactions,
    multiplier=UNUSUAL_FREQUENCY_MULTIPLIER
):
    """
    Detect a sudden increase in transaction frequency.

    Compares recent transaction activity against
    the customer's historical average activity.
    """

    alerts = []

    customer_transactions = {}

    for transaction in transactions:

        customer_id = transaction.get(
            "customer_id"
        )

        transaction_time = _get_datetime(
            transaction
        )

        if not customer_id or not transaction_time:
            continue

        customer_transactions.setdefault(
            customer_id,
            []
        ).append(transaction)

    for customer_id, customer_txns in customer_transactions.items():

        if len(customer_txns) < 6:
            continue

        customer_txns.sort(
            key=lambda x: _get_datetime(x)
        )

        # Use the first 70% as historical activity.
        historical_count = max(
            3,
            int(len(customer_txns) * 0.7)
        )

        historical = customer_txns[
            :historical_count
        ]

        recent = customer_txns[
            historical_count:
        ]

        if not recent:
            continue

        historical_times = [
            _get_datetime(txn)
            for txn in historical
        ]

        recent_times = [
            _get_datetime(txn)
            for txn in recent
        ]

        historical_duration = (
            max(historical_times)
            - min(historical_times)
        ).total_seconds()

        recent_duration = (
            max(recent_times)
            - min(recent_times)
        ).total_seconds()

        if historical_duration <= 0:
            continue

        historical_rate = (
            len(historical)
            / historical_duration
        )

        if recent_duration <= 0:
            recent_rate = len(recent)
        else:
            recent_rate = (
                len(recent)
                / recent_duration
            )

        if (
            recent_rate
            >= historical_rate * multiplier
        ):

            alerts.append({
                "rule_type":
                    "UNUSUAL_TRANSACTION_FREQUENCY",
                "risk_score": 80,
                "risk_level": "HIGH",
                "customer_id":
                    customer_id,
                "historical_transaction_count":
                    len(historical),
                "recent_transaction_count":
                    len(recent),
                "description":
                    "Customer transaction frequency "
                    "increased significantly compared "
                    "with historical activity."
            })

    return alerts


# ============================================================
# 4. ROUND-NUMBER TRANSACTION
# ============================================================

def detect_round_number_transactions(
    transactions,
    minimum_amount=ROUND_NUMBER_MIN_AMOUNT
):
    """
    Detect unusually large round-number transactions.

    Examples:

        100000
        200000
        500000
        1000000
    """

    alerts = []

    for transaction in transactions:

        amount = _to_decimal(
            transaction.get("amount", 0)
        )

        if amount < minimum_amount:
            continue

        # Amount must be divisible by 10,000.
        if amount % Decimal("10000") == 0:

            alerts.append({
                "rule_type":
                    "ROUND_NUMBER_TRANSACTION",
                "risk_score": 60,
                "risk_level": "MEDIUM",
                "trigger_transaction_id":
                    transaction.get("transaction_id"),
                "transaction_amount":
                    float(amount),
                "description":
                    "Large round-number transaction "
                    "detected."
            })

    return alerts


# ============================================================
# 5. MULTIPLE COUNTERPARTIES
# ============================================================

def detect_multiple_counterparties(
    transactions,
    counterparty_limit=MULTIPLE_COUNTERPARTIES_LIMIT,
    window_minutes=MULTIPLE_COUNTERPARTIES_WINDOW_MINUTES
):
    """
    Detect accounts sending money to many different
    counterparties within a short period.
    """

    alerts = []

    grouped_transactions = {}

    for transaction in transactions:

        source_account = transaction.get(
            "source_account_id"
        )

        transaction_time = _get_datetime(
            transaction
        )

        if not source_account or not transaction_time:
            continue

        grouped_transactions.setdefault(
            source_account,
            []
        ).append(transaction)

    for source_account, account_transactions in grouped_transactions.items():

        account_transactions.sort(
            key=lambda x: _get_datetime(x)
        )

        for index, transaction in enumerate(
            account_transactions
        ):

            start_time = _get_datetime(
                transaction
            )

            end_time = (
                start_time
                + timedelta(minutes=window_minutes)
            )

            counterparties = set()

            related_transactions = []

            for candidate in account_transactions[
                index:
            ]:

                candidate_time = _get_datetime(
                    candidate
                )

                if candidate_time > end_time:
                    break

                destination_account = candidate.get(
                    "destination_account_id"
                )

                if destination_account:
                    counterparties.add(
                        destination_account
                    )

                    related_transactions.append(
                        candidate
                    )

            if len(counterparties) >= counterparty_limit:

                alerts.append({
                    "rule_type":
                        "MULTIPLE_COUNTERPARTIES",
                    "risk_score": 80,
                    "risk_level": "HIGH",
                    "source_account_id":
                        source_account,
                    "trigger_transaction_id":
                        transaction.get(
                            "transaction_id"
                        ),
                    "counterparty_count":
                        len(counterparties),
                    "transaction_count":
                        len(related_transactions),
                    "description":
                        "Account sent transactions "
                        "to multiple counterparties "
                        "within a short period."
                })

                break

    return alerts


# ============================================================
# RUN ALL ADVANCED AML RULES
# ============================================================

def run_advanced_aml_rules(transactions):
    """
    Execute all advanced AML rules.

    Returns one combined list of triggered alerts.
    """

    all_alerts = []

    all_alerts.extend(
        detect_rapid_fund_movement(
            transactions
        )
    )

    all_alerts.extend(
        detect_unusual_transaction_amount(
            transactions
        )
    )

    all_alerts.extend(
        detect_unusual_transaction_frequency(
            transactions
        )
    )

    all_alerts.extend(
        detect_round_number_transactions(
            transactions
        )
    )

    all_alerts.extend(
        detect_multiple_counterparties(
            transactions
        )
    )

    return all_alerts