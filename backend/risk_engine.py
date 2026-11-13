def calculate_overall_risk(triggered_alerts):
    """
    Calculate overall transaction risk based on triggered AML rules.
    """

    if not triggered_alerts:
        return {
            "overall_risk_score": 0,
            "risk_level": "LOW",
            "triggered_rule_count": 0
        }

    scores = [
        alert["risk_score"]
        for alert in triggered_alerts
        if alert.get("risk_score") is not None
    ]

    if not scores:
        return {
            "overall_risk_score": 0,
            "risk_level": "LOW",
            "triggered_rule_count": 0
        }

    highest_score = max(scores)
    rule_count = len(scores)

    # Additional risk for multiple AML rules triggering
    if rule_count >= 3:
        overall_score = min(100, highest_score + 10)
    elif rule_count == 2:
        overall_score = min(100, highest_score + 5)
    else:
        overall_score = highest_score

    # Risk classification
    if overall_score >= 90:
        risk_level = "CRITICAL"
    elif overall_score >= 70:
        risk_level = "HIGH"
    elif overall_score >= 40:
        risk_level = "MEDIUM"
    else:
        risk_level = "LOW"

    return {
        "overall_risk_score": overall_score,
        "risk_level": risk_level,
        "triggered_rule_count": rule_count
    }