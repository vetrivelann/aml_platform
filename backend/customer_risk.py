# ============================================================
# CUSTOMER RISK PROFILING ENGINE
# ============================================================

def calculate_customer_risk(
    transaction_count,
    alert_count,
    large_transaction_count,
    high_velocity_count,
    structuring_count
):
    """
    Calculate customer-level AML risk score.

    Risk factors:
        AML alerts
        Large transactions
        High velocity activity
        Structuring activity
        Overall transaction activity

    Risk Levels:
        0-39   -> LOW
        40-69  -> MEDIUM
        70-89  -> HIGH
        90-100 -> CRITICAL
    """

    score = 0

    # --------------------------------------------------------
    # Transaction activity
    # --------------------------------------------------------
    if transaction_count >= 100:
        score += 10
    elif transaction_count >= 50:
        score += 5

    # --------------------------------------------------------
    # AML alert count
    # --------------------------------------------------------
    if alert_count >= 5:
        score += 25
    elif alert_count >= 3:
        score += 20
    elif alert_count >= 1:
        score += 10

    # --------------------------------------------------------
    # Large transaction activity
    # --------------------------------------------------------
    if large_transaction_count >= 3:
        score += 20
    elif large_transaction_count >= 1:
        score += 10

    # --------------------------------------------------------
    # High velocity activity
    # --------------------------------------------------------
    if high_velocity_count >= 3:
        score += 20
    elif high_velocity_count >= 1:
        score += 15

    # --------------------------------------------------------
    # Structuring activity
    # --------------------------------------------------------
    if structuring_count >= 3:
        score += 25
    elif structuring_count >= 1:
        score += 20

    # --------------------------------------------------------
    # Cap score at 100
    # --------------------------------------------------------
    score = min(100, score)

    # --------------------------------------------------------
    # Risk level
    # --------------------------------------------------------
    if score >= 90:
        risk_level = "CRITICAL"
    elif score >= 70:
        risk_level = "HIGH"
    elif score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "customer_risk_score": score,
        "risk_level": risk_level
    }