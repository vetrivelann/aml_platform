from backend.audit import (
    create_audit_table,
    create_audit_log,
    get_audit_logs,
    get_audit_logs_by_resource
)


print("=" * 60)
print("AUDIT TRAIL MODULE TEST")
print("=" * 60)


# ============================================================
# CREATE TABLE
# ============================================================

create_audit_table()

print("\nAudit table created successfully.")


# ============================================================
# CREATE TEST AUDIT LOG
# ============================================================

audit = create_audit_log(

    user_id="USR_TEST123",

    username="aml_test_user",

    user_role="ANALYST",

    action="CREATE_TRANSACTION",

    resource_type="TRANSACTION",

    resource_id="TXN_TEST123",

    description="Test transaction created",

    ip_address="127.0.0.1"
)

print("\nAudit log created:")

print(audit)


# ============================================================
# GET AUDIT LOGS
# ============================================================

logs = get_audit_logs()

print("\nLatest audit logs:")

for log in logs:

    print(log)


# ============================================================
# GET RESOURCE AUDIT HISTORY
# ============================================================

resource_logs = get_audit_logs_by_resource(
    resource_type="TRANSACTION",
    resource_id="TXN_TEST123"
)

print("\nTransaction audit history:")

for log in resource_logs:

    print(log)


print("\n" + "=" * 60)
print("AUDIT TRAIL MODULE TEST COMPLETED")
print("=" * 60)