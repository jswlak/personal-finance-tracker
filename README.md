# Personal Finance Tracker

A comprehensive personal finance tracking application with GUI interface, multi-currency support, and data visualization.

## Features

- **Income and Expense Tracking**: Track both income and expenses with detailed categorization
- **Multi-Currency Support**: Support for multiple currencies with real-time exchange rates
- **Transaction Categorization**: Organized categories for income and expenses
- **Spending Trends Visualization**: Interactive charts showing spending patterns
- **Financial Dashboard**: Summary view with net worth calculations
- **Data Export**: Export transactions to CSV format
- **Modern GUI**: Tabbed interface for easy navigation

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the application:
```bash
python src/main.py
```

## Usage

### Transactions Tab
- Select currency and transaction type (income/expense)
- Enter date, category, description, and amount
- View all transactions in a sortable table
- Edit or delete existing transactions

### Dashboard Tab
- View financial summary including total income, expenses, and net worth
- See category breakdown showing income vs expenses per category

### Charts Tab
- Generate various charts:
  - Monthly income vs expenses trends
  - Expense categories pie chart
  - Income vs expenses bar chart by category

### Settings Tab
- Configure base currency
- View current exchange rates
- Update exchange rates from API

## Data Storage

The application uses JSON files for data storage in the `data/` directory:
- `income.json`: Income transactions
- `expenses.json`: Expense transactions  
- `exchange_rates.json`: Cached exchange rates

All data is stored in human-readable JSON format, making it easy to backup, transfer, or manually edit if needed.

## Currency Support

Supported currencies: USD, EUR, GBP, JPY, CAD, AUD, INR

Exchange rates are fetched from exchangerate-api.com and cached locally.

## Categories

### Income Categories
- Salary
- Freelance
- Investment
- Bonus
- Other Income

### Expense Categories
- Food
- Transport
- Bills
- Shopping
- Entertainment
- Healthcare
- Education
- Other
