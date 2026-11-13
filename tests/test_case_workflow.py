from backend.case_workflow import (
    create_case_from_alert,
    assign_case,
    update_case_disposition,
    close_case
)


print("=" * 60)
print("AML CASE WORKFLOW MODULE TEST")
print("=" * 60)


# ------------------------------------------------------------
# EXISTING TEST ALERT
# ------------------------------------------------------------

alert_id = "ALT_DED683AE4B60"


# ------------------------------------------------------------
# 1. CREATE CASE
# ------------------------------------------------------------

print("\n1. Creating case from alert...")

case = create_case_from_alert(
    alert_id=alert_id,
    user_id="USR_237F80826E",
    username="aml_admin",
    user_role="ADMIN"
)

print("Case result:")
print(case)


if not case:
    raise Exception("Case creation failed")


case_id = case["case_id"]


# ------------------------------------------------------------
# 2. ASSIGN CASE
# ------------------------------------------------------------

print("\n2. Assigning case...")

assignment = assign_case(
    case_id=case_id,
    assigned_to="aml_test_user",
    user_id="USR_237F80826E",
    username="aml_admin",
    user_role="ADMIN"
)

print("Assignment result:")
print(assignment)


if not assignment:
    raise Exception("Case assignment failed")


# ------------------------------------------------------------
# 3. UPDATE DISPOSITION
# ------------------------------------------------------------

print("\n3. Updating case disposition...")

disposition = update_case_disposition(
    case_id=case_id,
    disposition="SUSPICIOUS",
    notes="Suspicious transaction requires further AML review.",
    user_id="USR_237F80826E",
    username="aml_admin",
    user_role="ADMIN"
)

print("Disposition result:")
print(disposition)


if not disposition:
    raise Exception("Disposition update failed")


# ------------------------------------------------------------
# 4. CLOSE CASE
# ------------------------------------------------------------

print("\n4. Closing case...")

closed = close_case(
    case_id=case_id,
    user_id="USR_237F80826E",
    username="aml_admin",
    user_role="ADMIN"
)

print("Close result:")
print(closed)


if not closed:
    raise Exception("Case closure failed")


print("\n" + "=" * 60)
print("AML CASE WORKFLOW MODULE TEST COMPLETED")
print("=" * 60)