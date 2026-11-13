from backend.investigation import get_alert_investigation


print("=" * 60)
print("AML INVESTIGATION MODULE TEST")
print("=" * 60)


# ============================================================
# USE AN EXISTING ALERT
# ============================================================

alert_id = "ALT_DED683AE4B60"


# ============================================================
# RUN INVESTIGATION
# ============================================================

print("\n1. Getting alert investigation...")

investigation = get_alert_investigation(
    alert_id
)


# ============================================================
# VALIDATE RESULT
# ============================================================

if investigation:

    print("\nPASS")

    print("\nAlert:")
    print(investigation["alert"])

    print("\nTransaction:")
    print(investigation["transaction"])

    print("\nCustomer:")
    print(investigation["customer"])

    print("\nRelated transactions:")
    print(
        len(
            investigation[
                "related_transactions"
            ]
        )
    )

    print("\nRelated alerts:")
    print(
        len(
            investigation[
                "related_alerts"
            ]
        )
    )

    print("\nTransaction summary:")
    print(
        investigation[
            "transaction_summary"
        ]
    )

    print("\nAlert summary:")
    print(
        investigation[
            "alert_summary"
        ]
    )

    print("\nRisk assessment:")
    print(
        investigation[
            "risk_assessment"
        ]
    )

    print("\nInvestigation summary:")
    print(
        investigation[
            "investigation_summary"
        ]
    )

else:

    print("\nFAIL")
    print(
        f"Alert {alert_id} was not found."
    )


print("\n" + "=" * 60)
print("AML INVESTIGATION MODULE TEST COMPLETED")
print("=" * 60)