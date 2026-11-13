# AML Transaction Monitoring Platform

A full-stack **Anti-Money Laundering (AML) Transaction Monitoring
Platform** built with **Python, FastAPI, PostgreSQL,
SQLAlchemy/Pydantic, and Streamlit**.

The platform analyzes financial transactions using rule-based AML
detection, advanced behavioral rules, customer risk scoring,
investigation workflows, case management, notifications, authentication,
and role-based access control (RBAC).

------------------------------------------------------------------------

## 🚀 Project Overview

The AML Transaction Monitoring Platform is designed to help financial
institutions identify and investigate potentially suspicious
transactions.

The system provides:

-   Transaction monitoring
-   AML rule detection
-   Advanced suspicious-activity detection
-   Risk scoring
-   Customer risk profiling
-   Alert generation
-   Customer and alert investigation
-   Case management
-   Case lifecycle workflow
-   Notifications
-   Authentication
-   Role-Based Access Control (RBAC)
-   Audit trail
-   Streamlit dashboard
-   FastAPI REST API
-   PostgreSQL database integration

------------------------------------------------------------------------

## 🏗️ Technology Stack

  Component              Technology
  ---------------------- ----------------------------------
  Programming Language   Python
  Backend API            FastAPI
  Data Validation        Pydantic
  Database               PostgreSQL
  ORM / Database Layer   SQLAlchemy
  Database Driver        psycopg
  Dashboard              Streamlit
  Authentication         Token-based authentication
  Authorization          Role-Based Access Control (RBAC)
  API Documentation      Swagger / OpenAPI
  Testing                Python test modules
  Environment            Python Virtual Environment

------------------------------------------------------------------------

## 📁 Project Structure

``` text
aml-platform/
│
├── backend/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── models.py
│   ├── aml_rules.py
│   ├── advanced_aml_rules.py
│   ├── risk_engine.py
│   ├── customer_investigation.py
│   ├── investigation.py
│   ├── reporting.py
│   ├── notification.py
│   ├── notification_trigger.py
│   ├── audit_trail.py
│   ├── case_workflow.py
│   ├── auth.py
│   ├── auth_models.py
│   ├── dependencies.py
│   ├── user_auth.py
│   └── auth_routes.py
│
├── tests/
│   ├── test_rules.py
│   ├── test_advanced_aml_rules.py
│   ├── test_risk_engine.py
│   ├── test_customer_risk.py
│   ├── test_customer_investigation.py
│   ├── test_investigation.py
│   ├── test_case_workflow.py
│   ├── test_notifications.py
│   ├── test_auth.py
│   ├── test_rbac.py
│   └── test_endpoint_security.py
│
├── dashboard.py
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

> **Note:** `.env` and the Python virtual environment should never be
> committed to GitHub.

------------------------------------------------------------------------

# 🔍 AML Detection Rules

## 1. Large Transaction

Detects transactions above the configured threshold.

**Threshold:**

``` text
₹500,000
```

Example:

``` text
₹750,000 → Alert
₹100,000 → No Alert
₹500,000 → No Alert
```

Risk score:

``` text
80
```

------------------------------------------------------------------------

## 2. High Velocity

Detects multiple transactions occurring within a short period.

Current rule:

``` text
5 or more transactions within 10 minutes
```

Example:

``` text
5 transactions within 10 minutes → Alert
4 transactions within 10 minutes → No Alert
```

Risk score:

``` text
85
```

------------------------------------------------------------------------

## 3. Structuring

Detects multiple smaller transactions that collectively exceed the AML
threshold.

Current logic includes:

``` text
At least 3 transactions
within 24 hours
combined amount > ₹500,000
individual transactions below the large-transaction threshold
```

Example:

``` text
Transaction 1 → ₹150,000
Transaction 2 → ₹175,000
Transaction 3 → ₹225,000

Total → ₹550,000

Result → Structuring Alert
```

Risk score:

``` text
90
```

------------------------------------------------------------------------

# 🧠 Advanced AML Rules

The platform also implements advanced behavioral detection rules:

### Rapid Fund Movement

Detects suspicious movement of funds through transactions occurring
rapidly.

### Unusual Transaction Amount

Detects transactions whose amounts are unusual compared with the
customer's transaction behavior.

### Unusual Transaction Frequency

Detects unusual transaction activity based on transaction frequency.

### Round Number Transaction

Detects suspicious round-number transaction amounts.

Examples:

``` text
₹100,000
₹250,000
₹500,000
```

### Multiple Counterparties

Detects customers interacting with multiple counterparties in suspicious
patterns.

------------------------------------------------------------------------

# ⚠️ Alert Management

When a transaction triggers an AML rule, the system can generate an
alert containing information such as:

-   Alert ID
-   Transaction ID
-   Customer ID
-   Rule type
-   Severity
-   Risk score
-   Alert status
-   Investigation information

A single transaction can trigger multiple AML rules.

Example:

``` text
TXN_123
│
├── ALT_001 → LARGE_TRANSACTION
├── ALT_002 → HIGH_VELOCITY
└── ALT_003 → ROUND_NUMBER_TRANSACTION
                │
                ▼
             CASE_ABC123
```

Multiple alerts related to the same suspicious transaction can therefore
be associated with a single investigation case.

------------------------------------------------------------------------

# 📊 Risk Scoring

The platform contains a risk scoring engine that evaluates AML activity.

Example risk levels:

    Risk Score Risk Level
  ------------ -------------------
         0--49 LOW
        50--79 MEDIUM / elevated
        80--89 HIGH
       90--100 CRITICAL

The final risk score is capped at:

``` text
100
```

The platform also supports customer-level risk profiling based on
transaction and alert activity.

------------------------------------------------------------------------

# 👤 Customer Risk Profiling

Customer risk is calculated using indicators such as:

-   Transaction count
-   Alert count
-   Large transaction count
-   High velocity count
-   Structuring count

Example:

``` text
Normal customer
→ LOW risk

Customer with suspicious activity
→ HIGH risk

Customer with multiple serious AML indicators
→ CRITICAL risk
```

------------------------------------------------------------------------

# 🔎 Investigation Module

The investigation module allows analysts to examine suspicious activity.

Investigation information can include:

-   Customer information
-   Transaction information
-   Related transactions
-   Related alerts
-   Customer risk score
-   Recommended action

Example investigation result:

``` text
Customer: CUST_0001
Risk: HIGH
Risk Score: 80
Related Transactions: 20
Related Alerts: 32
Recommendation: Analyst review required
```

------------------------------------------------------------------------

# 📂 Case Management

Suspicious activity can be converted into an investigation case.

The case workflow supports:

``` text
Create Case
     ↓
Assign Case
     ↓
Investigate
     ↓
Update Disposition
     ↓
Close Case
```

Supported workflow operations include:

-   Create case
-   Assign case
-   Update case
-   Set disposition
-   Close case

Example dispositions include:

``` text
SUSPICIOUS
```

------------------------------------------------------------------------

# 🔔 Notifications

The notification module supports:

-   Notification creation
-   Notification retrieval
-   Notification status updates
-   Automatic notifications based on risk severity

High-risk and critical-risk activity can generate notifications.

Low-risk activity does not generate the same escalation notification.

------------------------------------------------------------------------

# 🔐 Authentication

The platform includes user authentication.

Authentication protects API endpoints and provides user identity
information for authorization.

The authentication system supports different application roles.

------------------------------------------------------------------------

# 🛡️ Role-Based Access Control (RBAC)

The platform implements four primary roles:

-   ADMIN
-   MANAGER
-   ANALYST
-   VIEWER

## Permission Matrix

  Operation             ADMIN   MANAGER   ANALYST   VIEWER
  -------------------- ------- --------- --------- --------
  View Alerts            ✅       ✅        ✅        ✅
  Create Transaction     ✅       ✅        ✅        ❌
  Update Alert           ✅       ✅        ❌        ❌
  View Case              ✅       ✅        ✅        ✅
  Create Case            ✅       ✅        ✅        ❌
  Update Case            ✅       ✅        ❌        ❌
  Customer Risk          ✅       ✅        ✅        ✅

The backend enforces these permissions at the API level, while the
Streamlit dashboard also hides unauthorized controls.

------------------------------------------------------------------------

# 🧾 Audit Trail

The platform includes an audit trail module for recording important
system actions.

This provides a foundation for tracking operational activity and
supporting AML investigation accountability.

------------------------------------------------------------------------

# 🖥️ Streamlit Dashboard

The project includes a Streamlit dashboard for interacting with the AML
platform.

The dashboard provides a user-friendly interface for activities such as:

-   Transaction monitoring
-   Alert viewing
-   Risk information
-   Customer investigation
-   Case workflow
-   Notifications
-   Role-based functionality

Unauthorized update controls are hidden according to the user's role.

------------------------------------------------------------------------

# 🔌 REST API

The backend is implemented using FastAPI.

Start the API with:

``` powershell
.\venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

API:

``` text
http://127.0.0.1:8000
```

Swagger API documentation:

``` text
http://127.0.0.1:8000/docs
```

ReDoc:

``` text
http://127.0.0.1:8000/redoc
```

------------------------------------------------------------------------

# 📊 Run the Streamlit Dashboard

Start the dashboard using:

``` powershell
.\venv\Scripts\python.exe -m streamlit run dashboard.py
```

Streamlit will provide the local dashboard URL in the terminal.

------------------------------------------------------------------------

# 🗄️ Database

The application uses PostgreSQL as the primary relational database.

Database configuration is loaded through environment variables.

Example `.env` structure:

``` env
DATABASE_URL=your_database_connection_string
SECRET_KEY=your_secret_key
```

Do **not** publish real database credentials, API keys, passwords, or
secret keys.

------------------------------------------------------------------------

# 🧪 Testing

The project contains independent test modules for the major components.

Examples:

``` powershell
python -m tests.test_rules
python -m tests.test_advanced_aml_rules
python -m tests.test_risk_engine
python -m tests.test_customer_risk
python -m tests.test_customer_investigation
python -m tests.test_investigation
python -m tests.test_case_workflow
python -m tests.test_notifications
python -m tests.test_auth
python -m tests.test_rbac
python -m tests.test_endpoint_security
```

The endpoint security tests verify authentication and role-based
authorization.

Expected security behavior includes:

``` text
ADMIN   → authorized
MANAGER → authorized
ANALYST → restricted from alert/case updates
VIEWER  → restricted from transaction creation and updates
```

------------------------------------------------------------------------

# ✅ Validation

The project has been validated across the major modules.

### AML Rules

-   Large transaction detection
-   High velocity detection
-   Structuring detection

### Advanced AML

-   Rapid fund movement
-   Unusual transaction amount
-   Unusual transaction frequency
-   Round-number transactions
-   Multiple counterparties

### Risk

-   Transaction risk scoring
-   Customer risk profiling
-   Risk level classification

### Investigation

-   Customer investigation
-   Alert investigation
-   Related transactions
-   Related alerts

### Case Management

-   Case creation
-   Case assignment
-   Disposition update
-   Case closure

### Notifications

-   Notification creation
-   Notification retrieval
-   Notification status updates
-   Automatic high/critical notifications

### Security

-   Authentication
-   Token validation
-   RBAC
-   Endpoint-level authorization
-   Unauthorized update prevention

### Code Quality

The project has been checked using Python bytecode compilation:

``` powershell
python -m compileall backend tests
```

Successful compilation produces output similar to:

``` text
Listing 'backend'...
Listing 'tests'...
```

with no compilation errors.

------------------------------------------------------------------------

# 🔒 Security and GitHub Safety

Before pushing the project to GitHub, make sure sensitive files are
ignored.

Recommended `.gitignore`:

``` gitignore
__pycache__/
*.py[cod]
*.pyo
venv/
.venv/
env/
.env
.env.*
!.env.example
.vscode/
.idea/
.pytest_cache/
.coverage
htmlcov/
*.log
*.tmp
*.temp
.DS_Store
Thumbs.db
*.db
*.sqlite
*.sqlite3
.ipynb_checkpoints/
```

Verify ignored files before committing:

``` powershell
git check-ignore -v .env
git check-ignore -v venv
```

Never commit:

-   Database passwords
-   Authentication secrets
-   API keys
-   `.env`
-   `venv/`
-   Personal credentials
-   Production secrets

------------------------------------------------------------------------

# ⚙️ Installation

## 1. Clone the repository

``` bash
git clone <your-github-repository-url>
cd aml-platform
```

## 2. Create a virtual environment

Windows:

``` powershell
python -m venv venv
```

## 3. Activate the environment

``` powershell
.\venv\Scripts\Activate.ps1
```

## 4. Install dependencies

``` powershell
pip install -r requirements.txt
```

## 5. Configure environment variables

Create a `.env` file and configure your PostgreSQL connection and
application secrets.

## 6. Start the FastAPI server

``` powershell
uvicorn backend.main:app --reload
```

## 7. Start the dashboard

Open another terminal:

``` powershell
streamlit run dashboard.py
```

------------------------------------------------------------------------

# 🔄 Application Workflow

The overall AML workflow can be summarized as:

``` text
                    Transaction
                         │
                         ▼
                Transaction Validation
                         │
                         ▼
                  AML Rule Engine
                         │
              ┌──────────┴──────────┐
              ▼                     ▼
        No Suspicious             Suspicious
           Activity                 Activity
              │                     │
              ▼                     ▼
       SAFE TRANSACTION          Alert Creation
                                    │
                                    ▼
                              Risk Calculation
                                    │
                                    ▼
                              Investigation
                                    │
                                    ▼
                               Case Creation
                                    │
                                    ▼
                              Analyst Review
                                    │
                                    ▼
                              Disposition
                                    │
                                    ▼
                              Case Closure
```

------------------------------------------------------------------------

# 🎯 Project Objectives

The project aims to provide a practical AML monitoring solution that
can:

1.  Detect suspicious financial transactions.
2.  Apply multiple AML detection rules.
3.  Calculate transaction and customer risk.
4.  Generate and manage AML alerts.
5.  Support customer investigations.
6.  Create and manage investigation cases.
7.  Notify users about high-risk activity.
8.  Enforce role-based security.
9.  Maintain an audit trail.
10. Provide a dashboard for AML monitoring.

------------------------------------------------------------------------

# 📌 Current Project Status

The core AML Transaction Monitoring Platform is implemented and has
completed module-level and endpoint-security validation.

Current focus:

``` text
Core Development        → COMPLETE
AML Rule Engine         → COMPLETE
Advanced AML Rules     → COMPLETE
Risk Engine             → COMPLETE
Investigation           → COMPLETE
Case Workflow           → COMPLETE
Notifications           → COMPLETE
Authentication          → COMPLETE
RBAC                    → COMPLETE
Endpoint Security       → COMPLETE
Compilation Check       → COMPLETE
Final GitHub QA         → IN PROGRESS
```

------------------------------------------------------------------------

# 👨‍💻 Author

**Vetrivelann S**

B.Tech Computer Science and Engineering

GitHub:

https://github.com/vetrivelann

------------------------------------------------------------------------

# 📄 License

This project is intended for educational, portfolio, and demonstration
purposes.

Add an appropriate open-source license if you decide to distribute the
project publicly.
