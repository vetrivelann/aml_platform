import streamlit as st
import requests
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timezone


# ============================================================
# CONFIGURATION
# ============================================================

API_BASE_URL = "http://127.0.0.1:8000/api/v1"

AUTH_TOKEN_URL = f"{API_BASE_URL}/auth/token"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AML Transaction Monitoring Dashboard",
    page_icon="🛡️",
    layout="wide"
)


# ============================================================
# SESSION STATE
# ============================================================

if "access_token" not in st.session_state:
    st.session_state.access_token = None

if "username" not in st.session_state:
    st.session_state.username = None

if "role" not in st.session_state:
    st.session_state.role = None


# ============================================================
# CUSTOM CSS
# ============================================================

st.markdown(
    """
    <style>

    .main {
        padding-top: 1rem;
    }

    .dashboard-title {
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .dashboard-subtitle {
        color: #888;
        font-size: 15px;
        margin-bottom: 25px;
    }

    .section-title {
        font-size: 22px;
        font-weight: 700;
        margin-top: 30px;
        margin-bottom: 15px;
    }

    .login-box {
        max-width: 650px;
        margin: 80px auto;
    }

    </style>
    """,
    unsafe_allow_html=True
)


# ============================================================
# AUTHENTICATION
# ============================================================

def login_user(username, password, selected_role):

    try:

        # ----------------------------------------------------
        # Login using existing OAuth2 token endpoint
        # ----------------------------------------------------

        response = requests.post(
            AUTH_TOKEN_URL,
            data={
                "username": username,
                "password": password
            },
            timeout=10
        )

        if response.status_code == 200:

            result = response.json()

            token = result.get("access_token")

            if not token:
                return False, "Authentication succeeded but no access token was returned."

            st.session_state.access_token = token

            # ------------------------------------------------
            # Get actual user information from backend
            # ------------------------------------------------

            me_response = requests.get(
                f"{API_BASE_URL}/auth/me",
                headers={
                    "Authorization": f"Bearer {token}"
                },
                timeout=10
            )

            if me_response.status_code != 200:

                st.session_state.access_token = None

                return False, "Unable to verify user account."

            user_data = me_response.json()

            actual_username = user_data.get("username")
            actual_role = user_data.get("role")

            # ------------------------------------------------
            # Verify selected role
            # ------------------------------------------------

            if actual_role != selected_role:

                st.session_state.access_token = None
                st.session_state.username = None
                st.session_state.role = None

                return False, (
                    f"Role mismatch. This account is registered "
                    f"as {actual_role}, not {selected_role}."
                )

            # ------------------------------------------------
            # Login successful
            # ------------------------------------------------

            st.session_state.access_token = token
            st.session_state.username = actual_username
            st.session_state.role = actual_role

            return True, user_data

        try:

            error_data = response.json()

            detail = error_data.get(
                "detail",
                "Invalid username or password."
            )

        except Exception:

            detail = "Invalid username or password."

        return False, detail

    except requests.exceptions.ConnectionError:

        return False, (
            "Could not connect to FastAPI backend. "
            "Make sure Uvicorn is running on "
            "http://127.0.0.1:8000."
        )

    except requests.exceptions.Timeout:

        return False, "Authentication request timed out."

    except Exception as e:

        return False, f"Authentication error: {str(e)}"

# ============================================================
# AUTHORIZATION HEADER
# ============================================================

def get_headers():

    token = st.session_state.access_token

    if not token:
        return {}

    return {
        "Authorization": f"Bearer {token}"
    }


# ============================================================
# LOGOUT
# ============================================================

def logout():

    st.session_state.access_token = None
    st.session_state.username = None
    st.session_state.role = None

    st.rerun()


# ============================================================
# LOGIN PAGE
# ============================================================

def show_login_page():

    st.markdown(
        """
        <div class="login-box">
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        "## 🔐 Secure Login"
    )

    st.info(
        "Please login using your AML platform account."
    )

    username = st.text_input(
        "Username",
        value="",
        placeholder="Enter username"
    )

    selected_role = st.selectbox(
        "Role",
        [
            "ADMIN",
            "MANAGER",
            "ANALYST",
            "VIEWER",
            "USER"
        ],
        index=2
    )

    password = st.text_input(
        "Password",
        type="password",
        placeholder="Enter password"
    )

    login_clicked = st.button(
        "🔑 Login",
        use_container_width=True
    )

    if login_clicked:

        if not username or not password:

            st.error(
                "Please enter username and password."
            )

        else:

            success, result = login_user(
                username=username,
                password=password,
                selected_role=selected_role
            )

            if success:

                st.success(
                    f"Login successful as {result['role']}."
                )

                st.rerun()

            else:

                st.error(
                    result
                )

    st.markdown(
        "</div>",
        unsafe_allow_html=True
    )

# ============================================================
# API REQUEST HELPER
# ============================================================

def api_get(endpoint):

    try:

        response = requests.get(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            timeout=10
        )

        if response.status_code == 401:

            st.session_state.access_token = None
            st.session_state.username = None
            st.session_state.role = None

            st.error(
                "Session expired or authentication token is invalid. "
                "Please login again."
            )

            st.rerun()

        return response

    except requests.exceptions.ConnectionError:

        st.error(
            "Could not connect to FastAPI backend."
        )

        return None

    except requests.exceptions.Timeout:

        st.error(
            "API request timed out."
        )

        return None

    except Exception as e:

        st.error(
            f"API request error: {e}"
        )

        return None


# ============================================================
# API POST
# ============================================================

def api_post(endpoint, json_data):

    try:

        response = requests.post(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            json=json_data,
            timeout=10
        )

        if response.status_code == 401:

            st.session_state.access_token = None
            st.session_state.username = None
            st.session_state.role = None

            st.error(
                "Session expired or authentication token is invalid."
            )

            st.rerun()

        return response

    except Exception as e:

        st.error(
            f"API request error: {e}"
        )

        return None


# ============================================================
# API PATCH
# ============================================================

def api_patch(endpoint, json_data):

    try:

        response = requests.patch(
            f"{API_BASE_URL}{endpoint}",
            headers=get_headers(),
            json=json_data,
            timeout=10
        )

        if response.status_code == 401:

            st.session_state.access_token = None
            st.session_state.username = None
            st.session_state.role = None

            st.error(
                "Session expired or authentication token is invalid."
            )

            st.rerun()

        return response

    except Exception as e:

        st.error(
            f"API request error: {e}"
        )

        return None


# ============================================================
# GET DASHBOARD SUMMARY
# ============================================================

def get_dashboard_summary():

    response = api_get(
        "/dashboard/summary"
    )

    if response is None:
        return None

    if response.status_code == 200:

        return response.json()

    st.error(
        f"Dashboard API returned status code "
        f"{response.status_code}"
    )

    return None


# ============================================================
# GET ALERTS
# ============================================================

def get_alerts():

    response = api_get(
        "/alerts"
    )

    if response is None:
        return []

    if response.status_code == 200:

        result = response.json()

        if isinstance(result, list):
            return result

        if isinstance(result, dict):

            if "alerts" in result:
                return result["alerts"]

            if "data" in result:
                return result["data"]

        return []

    st.error(
        f"Alerts API returned status code "
        f"{response.status_code}"
    )

    return []


# ============================================================
# UPDATE ALERT STATUS
# ============================================================

def update_alert_status(alert_id, new_status):

    response = api_patch(
        f"/alerts/{alert_id}/status",
        {
            "status": new_status
        }
    )

    if response is None:
        return False, {"detail": "No response from API"}

    if response.status_code in [200, 201]:

        return True, response.json()

    try:
        return False, response.json()

    except Exception:
        return False, {
            "detail": response.text
        }


# ============================================================
# GET CASES
# ============================================================

def get_cases():

    response = api_get(
        "/cases"
    )

    if response is None:
        return []

    if response.status_code == 200:

        result = response.json()

        if isinstance(result, list):
            return result

        if isinstance(result, dict):

            if "cases" in result:
                return result["cases"]

            if "data" in result:
                return result["data"]

        return []

    st.error(
        f"Cases API returned status code {response.status_code}"
    )

    return []


# ============================================================
# UPDATE CASE
# ============================================================

def update_case(case_id, update_data):

    response = api_patch(
        f"/cases/{case_id}",
        update_data
    )

    if response is None:
        return False, {"detail": "No response from API"}

    if response.status_code in [200, 201]:
        return True, response.json()

    try:
        return False, response.json()

    except Exception:
        return False, {
            "detail": response.text
        }


# ============================================================
# CREATE TRANSACTION
# ============================================================

def create_transaction(transaction_data):

    response = api_post(
        "/transactions",
        transaction_data
    )

    if response is None:
        return False, {"detail": "No response from API."}

    if response.status_code in [200, 201]:
        return True, response.json()

    try:
        return False, response.json()

    except Exception:
        return False, {
            "detail": response.text
        }


# ============================================================
# GET TRANSACTIONS
# ============================================================

def get_transactions():

    response = api_get(
        "/reports/transactions"
    )

    if response is None:
        return []

    if response.status_code == 200:

        result = response.json()

        if isinstance(result, list):
            return result

        if isinstance(result, dict):
            if "transactions" in result:
                return result["transactions"]

            if "data" in result:
                return result["data"]

        return []

    st.error(
        f"Transactions API returned status code {response.status_code}"
    )

    return []


# ============================================================
# LOGIN CHECK
# ============================================================

if not st.session_state.access_token:

    show_login_page()

    st.stop()


# ============================================================
# USER TRANSACTION CREATION
# ============================================================

if st.session_state.role == "USER":

    st.markdown(
        """
        <div class="dashboard-title">
            💳 Create Transaction
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="dashboard-subtitle">
            Submit a transaction for AML monitoring and risk assessment.
        </div>
        """,
        unsafe_allow_html=True
    )

    st.info(
        "You can create transactions. AML rules and risk scoring are handled automatically by the backend."
    )

    with st.form("user_transaction_form"):

        col1, col2 = st.columns(2)

        with col1:

            source_account_id = st.text_input(
                "Source Account ID",
                placeholder="Enter source account ID"
            )

            amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=100000.00,
                step=1000.00
            )

            currency = st.selectbox(
                "Currency",
                ["INR", "USD", "EUR", "GBP"]
            )

        with col2:

            destination_account_id = st.text_input(
                "Destination Account ID",
                placeholder="Enter destination account ID"
            )

            channel = st.selectbox(
                "Channel",
                ["ONLINE", "MOBILE", "BRANCH", "ATM", "UPI", "IMPS", "NEFT", "RTGS"]
            )

            transaction_type = st.selectbox(
                "Transaction Type",
                ["TRANSFER", "PAYMENT", "DEPOSIT", "WITHDRAWAL"]
            )

        submitted = st.form_submit_button(
            "💸 Submit Transaction",
            use_container_width=True
        )

    if submitted:

        if not source_account_id or not destination_account_id:

            st.error("Please enter both source and destination account IDs.")

        elif source_account_id == destination_account_id:

            st.error("Source and destination accounts cannot be the same.")

        else:

            transaction_data = {
                "source_account_id": source_account_id,
                "destination_account_id": destination_account_id,
                "amount": amount,
                "currency": currency,
                "channel": channel,
                "occurred_at": datetime.now(timezone.utc).isoformat(),
                "transaction_type": transaction_type
            }

            success, result = create_transaction(transaction_data)

            if success:

                st.success("Transaction created successfully.")

                transaction_result = result
                risk_result = result.get("risk_assessment", {})

                result_col1, result_col2, result_col3 = st.columns(3)

                with result_col1:
                    st.metric(
                        "Transaction ID",
                        transaction_result.get("transaction_id", "N/A")
                    )

                with result_col2:
                    st.metric(
                        "Risk Score",
                        risk_result.get("overall_risk_score", 0)
                    )

                with result_col3:
                    st.metric(
                        "Risk Level",
                        risk_result.get("risk_level", "LOW")
                    )

                alerts_created = result.get("alerts", [])

                notification_result = result.get("notification", {})

                if alerts_created:

                    st.error(
                        f"AML REVIEW REQUIRED — {len(alerts_created)} alert(s) created. "
                        "Verify the Alert ID, Alert Type and linked Case ID."
                    )

                    st.warning(
                        "🔔 " + notification_result.get(
                            "message",
                            "AML notification status unavailable."
                        )
                    )

                    alert_display_rows = []

                    for alert in alerts_created:

                        alert_display_rows.append({
                            "Alert ID": alert.get("alert_id", "N/A"),
                            "Alert Type": alert.get("alert_type", "N/A"),
                            "Severity": alert.get("severity", "N/A"),
                            "Risk Score": alert.get("risk_score", "N/A"),
                            "Alert Status": alert.get("status", "OPEN"),
                            "Case ID": alert.get("case_id", "N/A"),
                            "Case Status": alert.get("case_status", "OPEN")
                        })

                    st.dataframe(
                        pd.DataFrame(alert_display_rows),
                        use_container_width=True,
                        hide_index=True
                    )

                    st.info(
                        "The AML alert and case were created automatically. "
                        "Use the AML Alert Investigation section to review, "
                        "update the alert, and close/resolve the linked case."
                    )

                else:
                    st.success(
                        "SAFE TRANSACTION — No AML rule was triggered for this transaction."
                    )

                    st.info(
                        "No Alert ID or Case ID was created because this transaction passed the AML checks."
                    )

            else:

                st.error(
                    result.get(
                        "detail",
                        "Transaction creation failed."
                    )
                )

    if st.button("🚪 Logout"):
        logout()

    st.stop()


# ============================================================
# HEADER
# ============================================================

header_col1, header_col2 = st.columns(
    [5, 1]
)

with header_col1:

    st.markdown(
        """
        <div class="dashboard-title">
            🛡️ AML Transaction Monitoring Dashboard
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        """
        <div class="dashboard-subtitle">
            Real-time monitoring, risk analysis and AML investigation
        </div>
        """,
        unsafe_allow_html=True
    )


with header_col2:

    st.write("")

    if st.button(
        "🚪 Logout",
        use_container_width=True
    ):

        logout()


# ============================================================
# USER INFORMATION
# ============================================================

st.info(
    f"Logged in as: **{st.session_state.username}**"
)


# ============================================================
# REFRESH
# ============================================================

col_refresh, col_space = st.columns(
    [1, 5]
)

with col_refresh:

    if st.button(
        "🔄 Refresh Dashboard"
    ):

        st.rerun()


# ============================================================
# LOAD DASHBOARD DATA
# ============================================================

data = get_dashboard_summary()

if data is None:

    st.stop()


# ============================================================
# EXTRACT DASHBOARD DATA
# ============================================================

transactions = data.get(
    "transactions",
    {}
)

alerts = data.get(
    "alerts",
    {}
)

risk_summary = data.get(
    "risk_summary",
    {}
)

customers = data.get(
    "customers",
    {}
)

cases = data.get(
    "cases",
    {}
)


# ============================================================
# TRANSACTION MONITORING
# ============================================================

st.markdown(
    '<div class="section-title">💳 Transaction Monitoring</div>',
    unsafe_allow_html=True
)

st.write(
    "View transactions submitted through the AML platform and their risk assessment."
)

monitoring_transactions = get_transactions()

if monitoring_transactions:

    transactions_df = pd.DataFrame(monitoring_transactions)

    display_transaction_columns = [
        "transaction_id",
        "source_account_id",
        "destination_account_id",
        "amount",
        "currency",
        "channel",
        "transaction_type",
        "risk_score",
        "risk_level",
        "alert_count",
        "created_at"
    ]

    available_transaction_columns = [
        column
        for column in display_transaction_columns
        if column in transactions_df.columns
    ]

    st.dataframe(
        transactions_df[available_transaction_columns],
        use_container_width=True,
        hide_index=True
    )

else:

    st.info("No transactions found.")


# ============================================================
# TRANSACTION RISK REVIEW
# ============================================================

if st.session_state.role in [
    "ADMIN",
    "MANAGER",
    "ANALYST"
]:

    st.markdown(
        '<div class="section-title">🔎 Transaction Risk Review</div>',
        unsafe_allow_html=True
    )

    st.write(
        "High-risk and critical transactions require AML review. "
        "Transactions without AML alerts are shown as safe."
    )

    if monitoring_transactions:

        review_df = transactions_df.copy()

        # --------------------------------------------------------
        # Attach AML alert IDs, alert types and case IDs to each
        # transaction so the investigator can immediately trace a
        # flagged transaction to its alert and case.
        # --------------------------------------------------------

        review_alerts = get_alerts()

        alert_map = {}
        for alert in review_alerts:

            tx_id = str(alert.get("transaction_id", ""))

            if not tx_id:
                continue

            alert_map.setdefault(tx_id, []).append(alert)

        review_df["alert_ids"] = review_df["transaction_id"].apply(
            lambda tx_id: ", ".join(
                str(alert.get("alert_id"))
                for alert in alert_map.get(str(tx_id), [])
            )
            or "-"
        )

        review_df["alert_types"] = review_df["transaction_id"].apply(
            lambda tx_id: ", ".join(
                str(alert.get("alert_type"))
                for alert in alert_map.get(str(tx_id), [])
            )
            or "-"
        )

        review_df["case_ids"] = review_df["transaction_id"].apply(
            lambda tx_id: ", ".join(
                str(alert.get("case_id"))
                for alert in alert_map.get(str(tx_id), [])
                if alert.get("case_id")
            )
            or "-"
        )

        # --------------------------------------------------------
        # Derive transaction review status from backend AML alerts
        # --------------------------------------------------------

        # The transaction report can contain incomplete or stale
        # risk fields. The AML alerts endpoint is the authoritative
        # source for deciding whether a transaction requires review.
        alert_transaction_ids = set()

        for alert in review_alerts:

            alert_transaction_id = alert.get("transaction_id")

            if alert_transaction_id:
                alert_transaction_ids.add(
                    str(alert_transaction_id)
                )

        def get_transaction_review_status(row):

            transaction_id = str(
                row.get("transaction_id", "")
            )

            risk_level = str(
                row.get("risk_level", "LOW")
            ).upper()

            try:
                alert_count = int(
                    row.get("alert_count", 0) or 0
                )
            except Exception:
                alert_count = 0

            # AML alerts are the authoritative decision for this review
            # screen. A transaction is SAFE only when no alert exists for
            # that exact transaction ID. This prevents stale report risk
            # fields from turning an otherwise safe transaction into review.
            if transaction_id in alert_transaction_ids:
                return "AML REVIEW REQUIRED"

            return "SAFE TRANSACTION"


        review_df["transaction_status"] = review_df.apply(
            get_transaction_review_status,
            axis=1
        )

        # --------------------------------------------------------
        # Review filter
        # --------------------------------------------------------

        review_filter = st.selectbox(
            "Transaction Review Status",
            [
                "ALL",
                "AML REVIEW REQUIRED",
                "SAFE TRANSACTION"
            ]
        )

        if review_filter != "ALL":

            review_df = review_df[
                review_df["transaction_status"]
                == review_filter
            ]

        st.write(
            f"Showing **{len(review_df)}** transaction(s)"
        )

        # --------------------------------------------------------
        # Review queue table
        # --------------------------------------------------------

        review_columns = [
            "transaction_id",
            "source_account_id",
            "destination_account_id",
            "amount",
            "currency",
            "risk_score",
            "risk_level",
            "alert_count",
            "alert_ids",
            "alert_types",
            "case_ids",
            "transaction_status",
            "created_at"
        ]

        available_review_columns = [
            column
            for column in review_columns
            if column in review_df.columns
        ]

        if not review_df.empty:

            st.dataframe(
                review_df[available_review_columns],
                use_container_width=True,
                hide_index=True
            )

        else:

            if review_filter == "SAFE TRANSACTION":

                st.success(
                    "No safe transactions found."
                )

            elif review_filter == "AML REVIEW REQUIRED":

                st.success(
                    "No high-risk or critical transactions require review."
                )

            else:

                st.info(
                    "No transactions found."
                )



# ============================================================
# OVERALL OVERVIEW
# ============================================================

st.markdown(
    '<div class="section-title">📊 Overall Overview</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Total Transactions",
        f"{transactions.get('total', 0):,}"
    )


with col2:

    st.metric(
        "Total Alerts",
        f"{alerts.get('total', 0):,}"
    )


with col3:

    st.metric(
        "Total Customers",
        f"{customers.get('total', 0):,}"
    )


with col4:

    st.metric(
        "Total Cases",
        f"{cases.get('total', 0):,}"
    )


# ============================================================
# ALERT AND CASE STATUS
# ============================================================

st.markdown(
    '<div class="section-title">🚨 Alert & Investigation Status</div>',
    unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)


with col1:

    st.metric(
        "Open Alerts",
        f"{alerts.get('open', 0):,}"
    )


with col2:

    st.metric(
        "Closed Alerts",
        f"{alerts.get('closed', 0):,}"
    )


with col3:

    st.metric(
        "Open Cases",
        f"{cases.get('open', 0):,}"
    )


with col4:

    st.metric(
        "Closed Cases",
        f"{cases.get('closed', 0):,}"
    )


# ============================================================
# RISK DISTRIBUTION
# ============================================================

st.markdown(
    '<div class="section-title">⚠️ Customer / Transaction Risk Distribution</div>',
    unsafe_allow_html=True
)

risk_col1, risk_col2 = st.columns(2)


with risk_col1:

    st.markdown("### Risk Levels")

    r1, r2 = st.columns(2)

    with r1:

        st.metric(
            "LOW",
            f"{risk_summary.get('LOW', 0):,}"
        )

        st.metric(
            "HIGH",
            f"{risk_summary.get('HIGH', 0):,}"
        )

    with r2:

        st.metric(
            "MEDIUM",
            f"{risk_summary.get('MEDIUM', 0):,}"
        )

        st.metric(
            "CRITICAL",
            f"{risk_summary.get('CRITICAL', 0):,}"
        )


with risk_col2:

    risk_data = {
        "LOW": risk_summary.get(
            "LOW",
            0
        ),
        "MEDIUM": risk_summary.get(
            "MEDIUM",
            0
        ),
        "HIGH": risk_summary.get(
            "HIGH",
            0
        ),
        "CRITICAL": risk_summary.get(
            "CRITICAL",
            0
        )
    }

    risk_df = pd.DataFrame(
        list(risk_data.items()),
        columns=[
            "Risk Level",
            "Count"
        ]
    )

    fig, ax = plt.subplots(
        figsize=(7, 4)
    )

    ax.bar(
        risk_df["Risk Level"],
        risk_df["Count"]
    )

    ax.set_title(
        "Risk Level Distribution"
    )

    ax.set_xlabel(
        "Risk Level"
    )

    ax.set_ylabel(
        "Number of Records"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


# ============================================================
# CASE SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">📁 Case Investigation Summary</div>',
    unsafe_allow_html=True
)

case_col1, case_col2 = st.columns(2)


with case_col1:

    case_data = {
        "Open": cases.get(
            "open",
            0
        ),

        "Under Review": cases.get(
            "under_review",
            0
        ),

        "Closed": cases.get(
            "closed",
            0
        )
    }

    case_df = pd.DataFrame(
        list(case_data.items()),
        columns=[
            "Case Status",
            "Count"
        ]
    )

    fig, ax = plt.subplots(
        figsize=(7, 4)
    )

    ax.bar(
        case_df["Case Status"],
        case_df["Count"]
    )

    ax.set_title(
        "Case Status Distribution"
    )

    ax.set_xlabel(
        "Status"
    )

    ax.set_ylabel(
        "Number of Cases"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


with case_col2:

    st.markdown(
        "### Case Statistics"
    )

    st.metric(
        "Total Cases",
        f"{cases.get('total', 0):,}"
    )

    st.metric(
        "Under Review",
        f"{cases.get('under_review', 0):,}"
    )

    st.metric(
        "Closed",
        f"{cases.get('closed', 0):,}"
    )


# ============================================================
# ALERT SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">🚨 Alert Summary</div>',
    unsafe_allow_html=True
)

alert_col1, alert_col2 = st.columns(2)


with alert_col1:

    alert_data = {
        "Open": alerts.get(
            "open",
            0
        ),

        "Closed": alerts.get(
            "closed",
            0
        )
    }

    alert_df = pd.DataFrame(
        list(alert_data.items()),
        columns=[
            "Alert Status",
            "Count"
        ]
    )

    fig, ax = plt.subplots(
        figsize=(7, 4)
    )

    ax.bar(
        alert_df["Alert Status"],
        alert_df["Count"]
    )

    ax.set_title(
        "Alert Status Distribution"
    )

    ax.set_xlabel(
        "Status"
    )

    ax.set_ylabel(
        "Number of Alerts"
    )

    plt.tight_layout()

    st.pyplot(fig)

    plt.close(fig)


with alert_col2:

    st.markdown(
        "### Alert Statistics"
    )

    st.metric(
        "Total Alerts",
        f"{alerts.get('total', 0):,}"
    )

    st.metric(
        "Open Alerts",
        f"{alerts.get('open', 0):,}"
    )

    st.metric(
        "Closed Alerts",
        f"{alerts.get('closed', 0):,}"
    )


# ============================================================
# AML ALERT INVESTIGATION
# ============================================================

st.markdown("---")

st.markdown(
    '<div class="section-title">🔎 AML Alert Investigation</div>',
    unsafe_allow_html=True
)

st.write(
    "Review, filter and investigate individual AML alerts."
)


# ============================================================
# LOAD ALERTS
# ============================================================

# Reuse the alerts already loaded for transaction risk review.
# If the review section was skipped, load them here.
if "review_alerts" in locals():
    all_alerts = review_alerts
else:
    all_alerts = get_alerts()


if not all_alerts:

    st.info(
        "No AML alerts found."
    )

else:

    alerts_df = pd.DataFrame(
        all_alerts
    )


    # ========================================================
    # FILTERS
    # ========================================================

    filter_col1, filter_col2, filter_col3 = st.columns(3)


    # --------------------------------------------------------
    # STATUS FILTER
    # --------------------------------------------------------

    with filter_col1:

        if "status" in alerts_df.columns:

            statuses = (
                alerts_df["status"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            statuses = [
                "ALL"
            ] + sorted(statuses)

            selected_status = st.selectbox(
                "Alert Status",
                statuses
            )

        else:

            selected_status = "ALL"


    # --------------------------------------------------------
    # ALERT TYPE FILTER
    # --------------------------------------------------------

    with filter_col2:

        if "alert_type" in alerts_df.columns:

            alert_types = (
                alerts_df["alert_type"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            alert_types = [
                "ALL"
            ] + sorted(alert_types)

            selected_type = st.selectbox(
                "Alert Type",
                alert_types
            )

        else:

            selected_type = "ALL"


    # --------------------------------------------------------
    # RISK FILTER
    # --------------------------------------------------------

    with filter_col3:

        if "risk_level" in alerts_df.columns:

            risk_levels = (
                alerts_df["risk_level"]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            risk_levels = [
                "ALL"
            ] + sorted(risk_levels)

            selected_risk = st.selectbox(
                "Risk Level",
                risk_levels
            )

        else:

            selected_risk = "ALL"


    # ========================================================
    # APPLY FILTERS
    # ========================================================

    filtered_df = alerts_df.copy()


    if (
        selected_status != "ALL"
        and "status" in filtered_df.columns
    ):

        filtered_df = filtered_df[
            filtered_df["status"].astype(str)
            == selected_status
        ]


    if (
        selected_type != "ALL"
        and "alert_type" in filtered_df.columns
    ):

        filtered_df = filtered_df[
            filtered_df["alert_type"].astype(str)
            == selected_type
        ]


    if (
        selected_risk != "ALL"
        and "risk_level" in filtered_df.columns
    ):

        filtered_df = filtered_df[
            filtered_df["risk_level"].astype(str)
            == selected_risk
        ]


    # ========================================================
    # ALERT TABLE
    # ========================================================

    st.markdown(
        "### 📋 Alert List"
    )

    st.write(
        f"Showing **{len(filtered_df)}** alert(s)"
    )


    if not filtered_df.empty:

        display_columns = [
            "alert_id",
            "alert_type",
            "severity",
            "risk_level",
            "risk_score",
            "status",
            "customer_id",
            "transaction_id",
            "created_at"
        ]

        available_columns = [
            column
            for column in display_columns
            if column in filtered_df.columns
        ]

        st.dataframe(
            filtered_df[
                available_columns
            ],
            use_container_width=True,
            hide_index=True
        )


        # ====================================================
        # SELECT ALERT
        # ====================================================

        st.markdown(
            "### 🔎 Select Alert for Investigation"
        )


        if "alert_id" in filtered_df.columns:

            alert_ids = (
                filtered_df["alert_id"]
                .astype(str)
                .tolist()
            )

            selected_alert_id = st.selectbox(
                "Select Alert ID",
                alert_ids
            )


            # =================================================
            # FIND SELECTED ALERT
            # =================================================

            selected_alert = None

            for alert in all_alerts:

                if str(
                    alert.get("alert_id")
                ) == str(
                    selected_alert_id
                ):

                    selected_alert = alert
                    break


            if selected_alert:

                st.markdown("---")


                # =================================================
                # ALERT DETAILS
                # =================================================

                detail_col1, detail_col2 = st.columns(2)


                with detail_col1:

                    st.markdown(
                        "### 🚨 Alert Details"
                    )

                    st.write(
                        "**Alert ID:**",
                        selected_alert.get(
                            "alert_id",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Alert Type:**",
                        selected_alert.get(
                            "alert_type",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Severity:**",
                        selected_alert.get(
                            "severity",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Risk Level:**",
                        selected_alert.get(
                            "risk_level",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Risk Score:**",
                        selected_alert.get(
                            "risk_score",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Status:**",
                        selected_alert.get(
                            "status",
                            "N/A"
                        )
                    )


                # =================================================
                # TRANSACTION / CUSTOMER
                # =================================================

                with detail_col2:

                    st.markdown(
                        "### 👤 Transaction / Customer"
                    )

                    st.write(
                        "**Customer ID:**",
                        selected_alert.get(
                            "customer_id",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Transaction ID:**",
                        selected_alert.get(
                            "transaction_id",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Amount:**",
                        selected_alert.get(
                            "amount",
                            "N/A"
                        )
                    )

                    st.write(
                        "**Created At:**",
                        selected_alert.get(
                            "created_at",
                            "N/A"
                        )
                    )


                # =================================================
                # DESCRIPTION
                # =================================================

                st.markdown(
                    "### 📝 Alert Description"
                )

                st.info(
                    selected_alert.get(
                        "description",
                        "No description available."
                    )
                )


                # =================================================
                # LINKED CASE
                # =================================================

                st.markdown(
                    "### 📁 Linked AML Case"
                )

                case_id = selected_alert.get(
                    "case_id",
                    None
                )

                case_status = selected_alert.get(
                    "case_status",
                    "OPEN"
                )

                if case_id:

                    case_col1, case_col2 = st.columns(2)

                    with case_col1:

                        st.write(
                            "**Case ID:**",
                            case_id
                        )

                    with case_col2:

                        st.write(
                            "**Case Status:**",
                            case_status
                        )

                    # =================================================
                    # CASE UPDATE CONTROLS
                    # =================================================

                    if st.session_state.role in [
                        "ADMIN",
                        "MANAGER"
                    ]:

                        case_status_options = [
                            "OPEN",
                            "UNDER_REVIEW",
                            "ESCALATED",
                            "RESOLVED",
                            "CLOSED"
                        ]

                        if case_status in case_status_options:
                            case_status_index = case_status_options.index(
                                case_status
                            )
                        else:
                            case_status_index = 0

                        new_case_status = st.selectbox(
                            "Case Status",
                            case_status_options,
                            index=case_status_index,
                            key=f"case_status_{case_id}"
                        )

                        disposition_options = [
                            "TRUE_POSITIVE",
                            "FALSE_POSITIVE",
                            "SUSPICIOUS",
                            "NO_ACTION"
                        ]

                        new_disposition = st.selectbox(
                            "Case Disposition",
                            disposition_options,
                            key=f"case_disposition_{case_id}"
                        )

                        if st.button(
                            "💾 Update Case",
                            key=f"update_case_{case_id}"
                        ):

                            case_success, case_result = update_case(
                                case_id,
                                {
                                    "case_status": new_case_status,
                                    "disposition": new_disposition
                                }
                            )

                            if case_success:

                                st.success(
                                    "Case updated successfully."
                                )

                                st.rerun()

                            else:

                                st.error(
                                    case_result.get(
                                        "detail",
                                        "Failed to update case."
                                    )
                                )

                    else:

                        st.info(
                            "👁️ READ-ONLY access: Case details are read-only."
                        )

                else:

                    st.warning(
                        "No case is linked to this alert yet."
                    )


                # =================================================
                # UPDATE ALERT STATUS
                # =================================================

                if st.session_state.role in [
                    "ADMIN",
                    "MANAGER"
                ]:

                    st.markdown(
                        "### 🔄 Update Alert Status"
                    )

                    allowed_statuses = [
                        "OPEN",
                        "UNDER_REVIEW",
                        "ESCALATED",
                        "RESOLVED",
                        "FALSE_POSITIVE"
                    ]

                    current_status = str(
                        selected_alert.get(
                            "status",
                            "OPEN"
                        )
                    )

                    if current_status in allowed_statuses:

                        status_index = (
                            allowed_statuses.index(
                                current_status
                            )
                        )

                    else:

                        status_index = 0

                    new_status = st.selectbox(
                        "New Status",
                        allowed_statuses,
                        index=status_index
                    )

                    if st.button(
                        "💾 Update Alert Status"
                    ):

                        success, result = (
                            update_alert_status(
                                selected_alert_id,
                                new_status
                            )
                        )

                        if success:

                            st.success(
                                "Alert status updated successfully."
                            )

                            st.rerun()

                        else:

                            st.error(
                                result.get(
                                    "detail",
                                    "Failed to update alert."
                                )
                            )

                else:

                    st.info(
                        "👁️ READ-ONLY access: Alert status is read-only."
                    )


# ============================================================
# FOOTER
# ============================================================

st.markdown("---")

st.caption(
    "AML Transaction Monitoring Platform • "
    "FastAPI + PostgreSQL + Streamlit"
)