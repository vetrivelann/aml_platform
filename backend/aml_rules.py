from decimal import Decimal
from datetime import datetime, timedelta


# ============================================================
# AML RULE CONFIGURATION
# ============================================================

# Rule 1: Large Transaction
LARGE_TRANSACTION_THRESHOLD = Decimal("500000")


# Rule 2: High Velocity
HIGH_VELOCITY_TRANSACTION_COUNT = 5
HIGH_VELOCITY_WINDOW_MINUTES = 10


# Rule 3: Structuring / Smurfing
STRUCTURING_MIN_TRANSACTION_COUNT = 3
STRUCTURING_WINDOW_HOURS = 24
STRUCTURING_TOTAL_THRESHOLD = Decimal("500000")


# ============================================================
# RULE 1: LARGE TRANSACTION
# ============================================================

def check_large_transaction(amount):
    """
    Detect transactions whose amount exceeds
    the configured large transaction threshold.

    Threshold:
        ₹500,000

    Risk Score:
        80

    Severity:
        HIGH
    """

    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))

    if amount > LARGE_TRANSACTION_THRESHOLD:

        return {
            "triggered": True,
            "alert_type": "LARGE_TRANSACTION",
            "severity": "HIGH",
            "risk_score": 80,
            "description": (
                f"Transaction amount ₹{amount} "
                f"exceeds the threshold of "
                f"₹{LARGE_TRANSACTION_THRESHOLD}"
            )
        }

    return {
        "triggered": False
    }


# ============================================================
# RULE 2: HIGH VELOCITY
# ============================================================

def check_high_velocity(
    transaction_time,
    previous_transactions
):
    """
    Detect whether an account has performed
    5 or more transactions within a 10-minute window.

    Parameters
    ----------
    transaction_time:
        Datetime of the current transaction.

    previous_transactions:
        List of previous transaction records.

        Each record should contain:

        {
            "occurred_at": datetime
        }

    Returns
    -------
    dict
        AML rule result.
    """

    if not previous_transactions:

        return {
            "triggered": False
        }

    # --------------------------------------------------------
    # Make sure current transaction is timezone-aware
    # --------------------------------------------------------

    if transaction_time.tzinfo is None:

        raise ValueError(
            "transaction_time must be timezone-aware"
        )

    # --------------------------------------------------------
    # Define the 10-minute window
    # --------------------------------------------------------

    window_start = (
        transaction_time
        - timedelta(
            minutes=HIGH_VELOCITY_WINDOW_MINUTES
        )
    )

    # Current transaction counts as transaction #1
    transaction_count = 1

    # --------------------------------------------------------
    # Check previous transactions
    # --------------------------------------------------------

    for transaction in previous_transactions:

        occurred_at = transaction["occurred_at"]

        # --------------------------------------------
        # Convert string datetime to datetime object
        # --------------------------------------------

        if isinstance(occurred_at, str):

            occurred_at = datetime.fromisoformat(
                occurred_at
            )

        # --------------------------------------------
        # Skip timezone-naive timestamps
        # --------------------------------------------

        if occurred_at.tzinfo is None:

            raise ValueError(
                "Previous transaction timestamp "
                "must be timezone-aware"
            )

        # --------------------------------------------
        # Check whether transaction is inside
        # the 10-minute window
        # --------------------------------------------

        if (
            window_start
            <= occurred_at
            <= transaction_time
        ):

            transaction_count += 1

    # --------------------------------------------------------
    # Trigger HIGH VELOCITY
    # --------------------------------------------------------

    if (
        transaction_count
        >= HIGH_VELOCITY_TRANSACTION_COUNT
    ):

        return {
            "triggered": True,
            "alert_type": "HIGH_VELOCITY",
            "severity": "HIGH",
            "risk_score": 85,
            "description": (
                f"Account performed "
                f"{transaction_count} or more transactions "
                f"within "
                f"{HIGH_VELOCITY_WINDOW_MINUTES} minutes"
            )
        }

    return {
        "triggered": False
    }


# ============================================================
# RULE 3: STRUCTURING / SMURFING
# ============================================================

def check_structuring(
    current_transaction_amount,
    previous_transactions
):
    """
    Detect potential structuring / smurfing.

    Rule:
        - At least 3 transactions
        - Within 24 hours
        - Each transaction below ₹500,000
        - Combined amount exceeds ₹500,000

    Parameters
    ----------
    current_transaction_amount:
        Amount of the current transaction.

    previous_transactions:
        List of previous transaction records.

        Each record should contain:

        {
            "amount": Decimal,
            "occurred_at": datetime
        }

    Returns
    -------
    dict
        AML rule result.
    """

    # --------------------------------------------------------
    # Convert current amount to Decimal
    # --------------------------------------------------------

    if not isinstance(
        current_transaction_amount,
        Decimal
    ):

        current_transaction_amount = Decimal(
            str(current_transaction_amount)
        )

    # --------------------------------------------------------
    # Current transaction must be below the
    # large transaction threshold
    # --------------------------------------------------------

    if (
        current_transaction_amount
        >= LARGE_TRANSACTION_THRESHOLD
    ):

        return {
            "triggered": False
        }

    # --------------------------------------------------------
    # No previous transactions
    # --------------------------------------------------------

    if not previous_transactions:

        return {
            "triggered": False
        }

    # --------------------------------------------------------
    # Calculate 24-hour window
    #
    # We use the latest/current transaction time.
    # --------------------------------------------------------

    current_time = None

    for transaction in previous_transactions:

        occurred_at = transaction["occurred_at"]

        if isinstance(occurred_at, str):

            occurred_at = datetime.fromisoformat(
                occurred_at
            )

        if occurred_at.tzinfo is None:

            raise ValueError(
                "Previous transaction timestamp "
                "must be timezone-aware"
            )

        if (
            current_time is None
            or occurred_at > current_time
        ):

            current_time = occurred_at

    # --------------------------------------------------------
    # If previous transaction list has no valid time
    # --------------------------------------------------------

    if current_time is None:

        return {
            "triggered": False
        }

    # --------------------------------------------------------
    # 24-hour window
    # --------------------------------------------------------

    window_start = (
        current_time
        - timedelta(
            hours=STRUCTURING_WINDOW_HOURS
        )
    )

    # --------------------------------------------------------
    # Start with current transaction
    # --------------------------------------------------------

    qualifying_transactions = 1

    total_amount = current_transaction_amount

    # --------------------------------------------------------
    # Check previous transactions
    # --------------------------------------------------------

    for transaction in previous_transactions:

        amount = transaction["amount"]

        occurred_at = transaction["occurred_at"]

        # --------------------------------------------
        # Convert amount
        # --------------------------------------------

        if not isinstance(amount, Decimal):

            amount = Decimal(str(amount))

        # --------------------------------------------
        # Convert timestamp
        # --------------------------------------------

        if isinstance(occurred_at, str):

            occurred_at = datetime.fromisoformat(
                occurred_at
            )

        # --------------------------------------------
        # Ignore transactions that are individually
        # above or equal to ₹500,000.
        #
        # Those belong to LARGE_TRANSACTION.
        # --------------------------------------------

        if (
            amount >= LARGE_TRANSACTION_THRESHOLD
        ):

            continue

        # --------------------------------------------
        # Check 24-hour window
        # --------------------------------------------

        if (
            window_start
            <= occurred_at
            <= current_time
        ):

            qualifying_transactions += 1

            total_amount += amount

    # --------------------------------------------------------
    # Trigger STRUCTURING
    # --------------------------------------------------------

    if (
        qualifying_transactions
        >= STRUCTURING_MIN_TRANSACTION_COUNT
        and
        total_amount
        > STRUCTURING_TOTAL_THRESHOLD
    ):

        return {
            "triggered": True,
            "alert_type": "STRUCTURING",
            "severity": "HIGH",
            "risk_score": 90,
            "description": (
                f"Potential structuring detected: "
                f"{qualifying_transactions} transactions "
                f"within {STRUCTURING_WINDOW_HOURS} hours "
                f"with combined amount "
                f"₹{total_amount}, "
                f"below the individual transaction threshold"
            )
        }

    return {
        "triggered": False
    }