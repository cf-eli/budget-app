# Budget Finance API

A personal finance management API built with Quasar, Litestar, and PostgreSQL. Features envelope budgeting, transaction categorization, line-item breakdowns, and SimpleFin integration for automatic bank account syncing.

## Features

- 🏦 **Bank Account Integration** - Automatic transaction sync via SimpleFin
- 💰 **Envelope Budgeting** - Allocate funds to income, expenses, and savings funds
- 📊 **Transaction Management** - Categorize, split, and track all transactions
- 🔍 **Line Item Breakdowns** - Break down transactions into individual items
- 📈 **Budget Snapshots** - Monthly rollover with historical tracking
- 🔄 **Transfer Detection** - Mark transfers and payments to exclude from budgets
- 🔐 **User Authentication** - Secure user management


## Key Concepts

### Envelope Budgeting

The system uses envelope budgeting where you allocate money to different categories:
- **Income**: Expected incoming money (salary, etc.)
- **Expenses**: Fixed and flexible expenses
- **Funds**: Savings goals with priority-based allocation

### Monthly Snapshots

At month-end, the system creates a snapshot capturing:
- Actual income vs expected
- Actual expenses vs expected
- Fund balances before/after allocation
- Surplus/deficit carried over

### Transaction Types

Transactions can be marked as:
- `transfer` - Money moving between your accounts
- `credit_payment` - Credit card payments
- `loan_payment` - Loan payments
- Regular transactions (default)

Transactions can be excluded from budget calculations.

## SimpleFin Integration

To use SimpleFin for automatic bank syncing:

1. Sign up at [SimpleFin](https://beta-bridge.simplefin.org/)
2. Get your access token
3. Use the API /user/token endpoint to sync transactions
4. Use the API /transactions/sync endpoint to sync transactions

## Starting the backend Server
Refer to the [backend README](backend/README.md) for instructions on setting up and running the backend server.

## Starting the Frontend
Refer to the [frontend README](frontend/README.md) for instructions on setting up and running the frontend application.

## Tech Stack

- **Backend**: Python 3.12+, Litestar/FastAPI
- **Frontend**: Quasar Framework (Vue.js)
- **Database**: PostgreSQL with SQLAlchemy 2.0 
