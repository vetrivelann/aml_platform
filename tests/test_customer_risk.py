from backend.customer_risk import calculate_customer_risk


print("=" * 40)
print("CUSTOMER RISK PROFILING TESTS")
print("=" * 40)


# Test 1
print("\nTest 1: Normal customer")

result = calculate_customer_risk(
    transaction_count=10,
    alert_count=0,
    large_transaction_count=0,
    high_velocity_count=0,
    structuring_count=0
)

print(result)

assert result["customer_risk_score"] == 0
assert result["risk_level"] == "LOW"

print("PASS")


# Test 2
print("\nTest 2: Customer with one AML alert")

result = calculate_customer_risk(
    transaction_count=20,
    alert_count=1,
    large_transaction_count=1,
    high_velocity_count=0,
    structuring_count=0
)

print(result)

assert result["customer_risk_score"] == 20
assert result["risk_level"] == "LOW"

print("PASS")


# Test 3
print("\nTest 3: High-risk customer")

result = calculate_customer_risk(
    transaction_count=60,
    alert_count=3,
    large_transaction_count=2,
    high_velocity_count=1,
    structuring_count=1
)

print(result)

assert result["customer_risk_score"] == 70
assert result["risk_level"] == "HIGH"

print("PASS")


# Test 4
print("\nTest 4: Critical-risk customer")

result = calculate_customer_risk(
    transaction_count=150,
    alert_count=5,
    large_transaction_count=3,
    high_velocity_count=3,
    structuring_count=3
)

print(result)

assert result["customer_risk_score"] == 100
assert result["risk_level"] == "CRITICAL"

print("PASS")


print("\n" + "=" * 40)
print("ALL CUSTOMER RISK TESTS PASSED")
print("=" * 40)