import os
import random
from datetime import datetime, timedelta

import numpy as np
import pandas as pd


# -----------------------------
# Configuration
# -----------------------------

NUM_CUSTOMERS = 100
NUM_ACCOUNTS = 120
NUM_TRANSACTIONS = 5000

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))

random.seed(42)
np.random.seed(42)


# -----------------------------
# Customer data
# -----------------------------

def generate_customers():
    occupations = [
        "Software Engineer",
        "Teacher",
        "Business Owner",
        "Doctor",
        "Student",
        "Accountant",
        "Consultant",
        "Shop Owner",
        "Freelancer",
        "Engineer"
    ]

    risk_ratings = ["LOW", "MEDIUM", "HIGH"]

    customers = []

    for i in range(1, NUM_CUSTOMERS + 1):

        occupation = random.choice(occupations)

        if occupation in ["Student", "Teacher"]:
            expected_activity = random.randint(10000, 50000)

        elif occupation in ["Software Engineer", "Doctor", "Engineer"]:
            expected_activity = random.randint(50000, 200000)

        elif occupation in ["Business Owner", "Shop Owner"]:
            expected_activity = random.randint(100000, 500000)

        else:
            expected_activity = random.randint(30000, 150000)

        risk_rating = random.choices(
            risk_ratings,
            weights=[60, 30, 10],
            k=1
        )[0]

        customers.append({
            "customer_id": f"CUST_{i:04d}",
            "customer_ref": f"CREF_{i:04d}",
            "customer_type": "INDIVIDUAL",
            "occupation": occupation,
            "expected_monthly_activity": expected_activity,
            "risk_rating": risk_rating,
            "kyc_status": "VERIFIED",
            "onboarding_date": (
                datetime(2024, 1, 1)
                + timedelta(days=random.randint(0, 700))
            ).date()
        })

    return pd.DataFrame(customers)


# -----------------------------
# Account data
# -----------------------------

def generate_accounts(customers):
    accounts = []

    for i, customer in customers.iterrows():

        # Some customers have more than one account
        number_of_accounts = 1

        if random.random() < 0.20:
            number_of_accounts = 2

        for account_number in range(number_of_accounts):

            account_id = f"ACC_{len(accounts) + 1:05d}"

            accounts.append({
                "account_id": account_id,
                "customer_id": customer["customer_id"],
                "account_ref": f"ACREF_{len(accounts) + 1:05d}",
                "currency": "INR",
                "opened_at": (
                    datetime.combine(
                        customer["onboarding_date"],
                        datetime.min.time()
                    )
                    + timedelta(days=random.randint(0, 30))
                ),
                "status": "ACTIVE"
            })

    return pd.DataFrame(accounts)


# -----------------------------
# Normal transactions
# -----------------------------

def generate_normal_transactions(accounts, customers):

    transactions = []

    account_ids = accounts["account_id"].tolist()

    customer_expected = customers.set_index(
        "customer_id"
    )["expected_monthly_activity"].to_dict()

    account_customer = accounts.set_index(
        "account_id"
    )["customer_id"].to_dict()

    start_date = datetime(2026, 1, 1)

    for i in range(NUM_TRANSACTIONS):

        source = random.choice(account_ids)

        destination = random.choice(account_ids)

        # Prevent self-transfer
        while destination == source:
            destination = random.choice(account_ids)

        source_customer = account_customer[source]

        expected = customer_expected[source_customer]

        amount = max(
            100,
            np.random.normal(
                expected / 20,
                expected / 50
            )
        )

        amount = round(float(amount), 2)

        occurred_at = (
            start_date
            + timedelta(
                days=random.randint(0, 300),
                minutes=random.randint(0, 1439)
            )
        )

        transactions.append({
            "transaction_id": f"TXN_{i + 1:07d}",
            "event_id": f"EVT_{i + 1:07d}",
            "source_account_id": source,
            "destination_account_id": destination,
            "amount": amount,
            "currency": "INR",
            "channel": random.choice(
                ["UPI", "IMPS", "NEFT", "RTGS"]
            ),
            "occurred_at": occurred_at,
            "transaction_type": "NORMAL"
        })

    return transactions


# -----------------------------
# Suspicious: High velocity
# -----------------------------

def add_high_velocity_scenario(transactions, accounts):

    account = random.choice(accounts["account_id"].tolist())

    start_time = datetime(2026, 10, 15, 10, 0, 0)

    account_ids = accounts["account_id"].tolist()

    for i in range(20):

        destination = random.choice(account_ids)

        while destination == account:
            destination = random.choice(account_ids)

        transactions.append({
            "transaction_id": f"TXN_SUSP_VEL_{i + 1:04d}",
            "event_id": f"EVT_SUSP_VEL_{i + 1:04d}",
            "source_account_id": account,
            "destination_account_id": destination,
            "amount": round(random.uniform(5000, 15000), 2),
            "currency": "INR",
            "channel": "IMPS",
            "occurred_at": start_time + timedelta(minutes=i),
            "transaction_type": "HIGH_VELOCITY"
        })


# -----------------------------
# Suspicious: Fan-in
# -----------------------------

def add_fan_in_scenario(transactions, accounts):

    target = random.choice(accounts["account_id"].tolist())

    other_accounts = [
        a for a in accounts["account_id"].tolist()
        if a != target
    ]

    start_time = datetime(2026, 10, 20, 12, 0, 0)

    senders = random.sample(other_accounts, 12)

    for i, sender in enumerate(senders):

        transactions.append({
            "transaction_id": f"TXN_SUSP_IN_{i + 1:04d}",
            "event_id": f"EVT_SUSP_IN_{i + 1:04d}",
            "source_account_id": sender,
            "destination_account_id": target,
            "amount": round(random.uniform(8000, 20000), 2),
            "currency": "INR",
            "channel": "IMPS",
            "occurred_at": start_time + timedelta(minutes=i * 2),
            "transaction_type": "FAN_IN"
        })


# -----------------------------
# Suspicious: Fan-out
# -----------------------------

def add_fan_out_scenario(transactions, accounts):

    source = random.choice(accounts["account_id"].tolist())

    other_accounts = [
        a for a in accounts["account_id"].tolist()
        if a != source
    ]

    destinations = random.sample(other_accounts, 10)

    start_time = datetime(2026, 10, 21, 15, 0, 0)

    for i, destination in enumerate(destinations):

        transactions.append({
            "transaction_id": f"TXN_SUSP_OUT_{i + 1:04d}",
            "event_id": f"EVT_SUSP_OUT_{i + 1:04d}",
            "source_account_id": source,
            "destination_account_id": destination,
            "amount": round(random.uniform(10000, 30000), 2),
            "currency": "INR",
            "channel": "IMPS",
            "occurred_at": start_time + timedelta(minutes=i * 3),
            "transaction_type": "FAN_OUT"
        })


# -----------------------------
# Suspicious: Rapid in/out
# -----------------------------

def add_rapid_movement_scenario(transactions, accounts):

    account_ids = accounts["account_id"].tolist()

    middle_account = random.choice(account_ids)

    other_accounts = [
        a for a in account_ids
        if a != middle_account
    ]

    sender = random.choice(other_accounts)

    receiver = random.choice([
        a for a in other_accounts
        if a != sender
    ])

    base_time = datetime(2026, 10, 25, 14, 0, 0)

    amount = 75000

    transactions.append({
        "transaction_id": "TXN_SUSP_RAPID_0001",
        "event_id": "EVT_SUSP_RAPID_0001",
        "source_account_id": sender,
        "destination_account_id": middle_account,
        "amount": amount,
        "currency": "INR",
        "channel": "IMPS",
        "occurred_at": base_time,
        "transaction_type": "RAPID_IN"
    })

    transactions.append({
        "transaction_id": "TXN_SUSP_RAPID_0002",
        "event_id": "EVT_SUSP_RAPID_0002",
        "source_account_id": middle_account,
        "destination_account_id": receiver,
        "amount": 73000,
        "currency": "INR",
        "channel": "IMPS",
        "occurred_at": base_time + timedelta(minutes=5),
        "transaction_type": "RAPID_OUT"
    })


# -----------------------------
# Main
# -----------------------------

def main():

    print("Generating synthetic AML data...")

    customers = generate_customers()

    accounts = generate_accounts(customers)

    transactions = generate_normal_transactions(
        accounts,
        customers
    )

    add_high_velocity_scenario(
        transactions,
        accounts
    )

    add_fan_in_scenario(
        transactions,
        accounts
    )

    add_fan_out_scenario(
        transactions,
        accounts
    )

    add_rapid_movement_scenario(
        transactions,
        accounts
    )

    transactions_df = pd.DataFrame(transactions)

    customers_path = os.path.join(
        OUTPUT_DIR,
        "customers.csv"
    )

    accounts_path = os.path.join(
        OUTPUT_DIR,
        "accounts.csv"
    )

    transactions_path = os.path.join(
        OUTPUT_DIR,
        "transactions.csv"
    )

    customers.to_csv(
        customers_path,
        index=False
    )

    accounts.to_csv(
        accounts_path,
        index=False
    )

    transactions_df.to_csv(
        transactions_path,
        index=False
    )

    print("\nData generation completed.")

    print(f"\nCustomers: {len(customers)}")
    print(f"Accounts: {len(accounts)}")
    print(f"Transactions: {len(transactions_df)}")

    print("\nTransaction types:")
    print(
        transactions_df["transaction_type"]
        .value_counts()
    )

    print("\nFiles created:")

    print(customers_path)
    print(accounts_path)
    print(transactions_path)


if __name__ == "__main__":
    main()