from backend.risk_engine import calculate_overall_risk


print("\n========================================")
print("RISK SCORING ENGINE TESTS")
print("========================================")


# ============================================================
# TEST 1: NO RULES TRIGGERED
# ============================================================

result = calculate_overall_risk([])

print("\nTest 1: No AML rules triggered")
print(result)

assert result["overall_risk_score"] == 0
assert result["risk_level"] == "LOW"
assert result["triggered_rule_count"] == 0

print("PASS")


# ============================================================
# TEST 2: ONE LOW/MEDIUM RISK RULE
# ============================================================

alerts = [
    {
        "alert_type": "TEST_RULE",
        "risk_score": 30
    }
]

result = calculate_overall_risk(alerts)

print("\nTest 2: One rule with score 30")
print(result)

assert result["overall_risk_score"] == 30
assert result["risk_level"] == "LOW"
assert result["triggered_rule_count"] == 1

print("PASS")


# ============================================================
# TEST 3: ONE HIGH RISK RULE
# ============================================================

alerts = [
    {
        "alert_type": "LARGE_TRANSACTION",
        "risk_score": 80
    }
]

result = calculate_overall_risk(alerts)

print("\nTest 3: One rule with score 80")
print(result)

assert result["overall_risk_score"] == 80
assert result["risk_level"] == "HIGH"
assert result["triggered_rule_count"] == 1

print("PASS")


# ============================================================
# TEST 4: TWO RULES TRIGGERED
# ============================================================

alerts = [
    {
        "alert_type": "LARGE_TRANSACTION",
        "risk_score": 80
    },
    {
        "alert_type": "HIGH_VELOCITY",
        "risk_score": 85
    }
]

result = calculate_overall_risk(alerts)

print("\nTest 4: Two AML rules triggered")
print(result)

assert result["overall_risk_score"] == 90
assert result["risk_level"] == "CRITICAL"
assert result["triggered_rule_count"] == 2

print("PASS")


# ============================================================
# TEST 5: THREE RULES TRIGGERED
# ============================================================

alerts = [
    {
        "alert_type": "LARGE_TRANSACTION",
        "risk_score": 80
    },
    {
        "alert_type": "HIGH_VELOCITY",
        "risk_score": 85
    },
    {
        "alert_type": "STRUCTURING",
        "risk_score": 90
    }
]

result = calculate_overall_risk(alerts)

print("\nTest 5: Three AML rules triggered")
print(result)

assert result["overall_risk_score"] == 100
assert result["risk_level"] == "CRITICAL"
assert result["triggered_rule_count"] == 3

print("PASS")


# ============================================================
# TEST 6: SCORE CANNOT EXCEED 100
# ============================================================

alerts = [
    {
        "alert_type": "RULE_1",
        "risk_score": 100
    },
    {
        "alert_type": "RULE_2",
        "risk_score": 100
    },
    {
        "alert_type": "RULE_3",
        "risk_score": 100
    }
]

result = calculate_overall_risk(alerts)

print("\nTest 6: Maximum score capped at 100")
print(result)

assert result["overall_risk_score"] == 100
assert result["risk_level"] == "CRITICAL"

print("PASS")


# ============================================================
# FINAL RESULT
# ============================================================

print("\n========================================")
print("ALL RISK SCORING TESTS PASSED")
print("========================================")

print("\nRisk levels:")
print("0-39   -> LOW")
print("40-69  -> MEDIUM")
print("70-89  -> HIGH")
print("90-100 -> CRITICAL")