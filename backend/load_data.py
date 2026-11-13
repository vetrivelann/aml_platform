import os
import pandas as pd

from dotenv import load_dotenv
from sqlalchemy import create_engine


# Load .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")


# Create database connection
engine = create_engine(DATABASE_URL)


# CSV paths
BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "synthetic"
)

customers_file = os.path.join(
    DATA_DIR,
    "customers.csv"
)

accounts_file = os.path.join(
    DATA_DIR,
    "accounts.csv"
)

transactions_file = os.path.join(
    DATA_DIR,
    "transactions.csv"
)


def load_csv_data():

    print("Loading CSV files...")

    customers = pd.read_csv(customers_file)
    accounts = pd.read_csv(accounts_file)
    transactions = pd.read_csv(transactions_file)

    print(f"Customers loaded from CSV: {len(customers)}")
    print(f"Accounts loaded from CSV: {len(accounts)}")
    print(f"Transactions loaded from CSV: {len(transactions)}")

    # Convert dates
    customers["onboarding_date"] = pd.to_datetime(
        customers["onboarding_date"]
    ).dt.date

    accounts["opened_at"] = pd.to_datetime(
        accounts["opened_at"]
    )

    transactions["occurred_at"] = pd.to_datetime(
        transactions["occurred_at"]
    )

    # Insert customers first
    customers.to_sql(
        "customers",
        engine,
        if_exists="append",
        index=False
    )

    print("Customers inserted successfully.")

    # Insert accounts
    accounts.to_sql(
        "accounts",
        engine,
        if_exists="append",
        index=False
    )

    print("Accounts inserted successfully.")

    # Insert transactions
    transactions.to_sql(
        "transactions",
        engine,
        if_exists="append",
        index=False
    )

    print("Transactions inserted successfully.")

    print("\nData loading completed successfully.")


if __name__ == "__main__":
    load_csv_data()