# PocketBudget — Personal Budget Tracker

**A Django-based personal finance application for tracking expenses, managing budgets, setting saving goals, and analysing spending habits.**

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-5.1%2B-092E20?logo=django&logoColor=white)
![Database](https://img.shields.io/badge/Database-SQLite-003B57?logo=sqlite&logoColor=white)
![Charts](https://img.shields.io/badge/Charts-SVG%20%7C%20CSV-23A6D5)
![License](https://img.shields.io/badge/Project-Portfolio%20Project-blue)

## Overview

PocketBudget is a personal finance web application built with Python and Django.

It allows users to record expenses, organise transactions into categories, set monthly budgets, create saving goals, and monitor their financial activity through a personal dashboard.

The application also includes **Max**, a local rule-based budgeting assistant that analyses saved financial data and generates simple spending insights without relying on external paid APIs.

PocketBudget uses SQLite for local data storage and is designed as a practical web development project.

## Main Features

### 1. User Accounts

- User registration.
- Login and logout.
- Personal dashboard for authenticated users.
- User-specific financial records.

### 2. Expense Management

- Add, edit, and delete expenses.
- Store expense title, amount, date, category, and optional notes.
- Filter expenses by category.
- Filter expenses by date.
- View recent expenses on the dashboard.
- Keep expense records separated by user account.

### 3. Categories

- Built-in default expense categories.
- Create custom categories.
- Edit and delete custom categories.
- Choose category icons and colours.
- Prevent deletion of categories that are already used by expenses or budgets.

### 4. Monthly Budgets

- Set an overall monthly budget.
- Create separate budgets for individual categories.
- View category budget percentages relative to the overall budget.
- Select a month and year.
- Edit and delete existing budgets.
- Compare spending with configured budget limits.

### 5. Saving Goals

- Create personal saving goals.
- Set target and current amounts.
- Add an optional deadline.
- Choose a goal colour.
- Track progress with percentage indicators.
- Edit and delete goals.
- Identify overdue goals.

### 6. Max — Local Budgeting Assistant

Max analyses the financial information saved in the application and generates rule-based recommendations.

It can:

- Monitor overall monthly budget usage.
- Warn when spending approaches or exceeds a budget limit.
- Identify categories with high spending.
- Highlight large expenses.
- Check saving goal progress and overdue deadlines.
- Generate short budgeting suggestions based on available data.

**Important:** Max is a local rule-based assistant. It does not use a generative AI model, external AI API, or paid third-party service.

### 7. Charts and Reports

The application includes a dedicated charts page with three chart types:

- **Category chart** — spending distribution by category.
- **Daily chart** — spending activity over the recent 14-day period.
- **Budget chart** — comparison of monthly spending with the configured budget.

Charts are generated from the user's saved financial data.

Available downloads:

- SVG chart files.
- CSV data exports.

### 8. Administration

The project includes two administration interfaces:

**Django Admin**

The standard Django administration interface for managing database records.

**Admin Statistics**

A custom statistics page showing:

- Total registered users.
- Total expenses.
- Total budgets and saving goals.
- Overall spending statistics.
- Average expense amount.
- Spending by category.
- Recent users and expenses.
- Current-month budget information.

The custom statistics page is restricted to administrator or staff accounts.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Main programming language |
| Django | Web framework |
| SQLite | Local relational database |
| Django ORM | Database models and queries |
| Django Authentication | User registration and authentication |
| HTML5 | Page structure |
| CSS3 | Interface styling |
| JavaScript | Frontend interactions |
| SVG | Chart rendering |
| CSV | Financial data export |
| Django TestCase | Automated application tests |

Dependency information:

```text
Django>=5.1,<7.0
```

The exact Django version installed depends on the Python environment and package resolver.

## Application Pages

| Page | URL | Purpose |
|---|---|---|
| Dashboard | `/` | Monthly financial overview |
| Registration | `/register/` | Create an account |
| Login | `/login/` | Sign in |
| Expenses | `/expenses/` | View and filter expenses |
| Categories | `/categories/` | Manage expense categories |
| Budgets | `/budgets/` | Manage monthly budgets |
| Saving Goals | `/goals/` | Track saving goals |
| Charts | `/charts/` | View spending charts |
| Max Insights | `/insights/` | View budgeting recommendations |
| Admin Statistics | `/admin-stats/` | View administrative statistics |
| Django Admin | `/admin/` | Manage application records |

Most personal finance pages require authentication.

## Quick Start — Windows

### Requirements

- Windows 10 or Windows 11.
- Python 3.12 or newer recommended.
- pip (Python package installer).
- A modern web browser.

### 1. Clone the repository

Open Command Prompt or PowerShell and run:

```powershell
git clone https://github.com/lacelyn5/PocketBudget.git
cd PocketBudget
```

Alternatively, download the repository as a ZIP archive and extract it.

### 2. Create a virtual environment

```powershell
py -m venv venv
```

### 3. Activate the virtual environment

**Command Prompt:**

```bat
venv\Scripts\activate.bat
```

**PowerShell:**

```powershell
.\venv\Scripts\Activate.ps1
```

If PowerShell blocks script execution, you can use Command Prompt instead.

### 4. Install dependencies

Upgrade pip:

```powershell
python -m pip install --upgrade pip
```

Install the project dependencies:

```powershell
python -m pip install -r requirements.txt
```

### 5. Apply database migrations

```powershell
python manage.py migrate
```

The migrations create the required database structure and default expense categories.

### 6. Create an administrator account (optional)

```powershell
python manage.py createsuperuser
```

Follow the prompts to create your administrator credentials.

### 7. Start the development server

```powershell
python manage.py runserver
```

Open the application in your browser:

**http://127.0.0.1:8000/**

You can register a new account through the registration page:

**http://127.0.0.1:8000/register/**

## Administration

After creating a superuser, the standard Django Admin interface is available at:

**http://127.0.0.1:8000/admin/**

The custom Admin Statistics page is available at:

**http://127.0.0.1:8000/admin-stats/**

The custom statistics page requires an administrator or staff account.

## How Max Works

Max uses locally implemented rules and calculations to analyse saved financial information.

It does not send user financial data to an external AI service.

Examples of generated insights include:

- Monthly budget usage warnings.
- Category budget limit warnings.
- Identification of the largest expense.
- Spending distribution observations.
- Saving goal deadline warnings.
- Suggestions based on monthly spending patterns.

The recommendations are informational and are not professional financial or investment advice.

## Running Tests

Run the Django test suite from the project root after activating the virtual environment:

```powershell
python manage.py test
```

The tests cover the main application workflows, including:

- Registration and login.
- Authentication requirements.
- Expense creation and editing.
- Expense date filtering.
- User-specific expense access.
- Custom category creation and validation.
- Monthly budget creation and updates.
- Budget period filtering and calculations.
- Saving goal creation, editing, and validation.
- Max budgeting insights.
- Admin statistics access control.
- Chart page rendering.
- SVG and CSV chart downloads.

The test suite uses Django's built-in testing framework and a separate test database.

## Main Data Models

PocketBudget uses several Django models to organise financial information.

| Model | Purpose |
|---|---|
| Category | Default and user-created expense categories |
| Expense | Personal expense records |
| MonthlyBudget | Overall and category budgets for selected months |
| SavingGoal | Personal saving targets and progress |
| AIInsight | Locally generated budgeting insights |

Financial records are associated with user accounts to keep personal data separated.

## Project Structure

```text
PocketBudget/
│
├── budget/
│   ├── migrations/
│   ├── admin.py
│   ├── ai_engine.py
│   ├── apps.py
│   ├── chart_engine.py
│   ├── forms.py
│   ├── models.py
│   ├── services.py
│   ├── tests.py
│   ├── urls.py
│   └── views.py
│
├── docx/
│
├── pocketbudget_project/
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── static/
├── templates/
├── .gitignore
├── manage.py
├── requirements.txt
└── README.md
```

## Local Data Storage

PocketBudget uses SQLite for local development.

The database file is created in the project directory after running migrations.

The application stores:

- User accounts.
- Expenses.
- Expense categories.
- Monthly budgets.
- Saving goals.
- Generated budgeting insights.

Keep a backup of the local database if you need to preserve your records.

## Development Configuration and Limitations

PocketBudget is currently intended for local development and portfolio demonstration.

The supplied Django settings use development configuration, including `DEBUG=True` and a development secret key.

Before any public deployment:

- Generate a new secret key and keep it outside the repository.
- Set `DEBUG=False`.
- Configure `ALLOWED_HOSTS`.
- Configure secure cookies and HTTPS.
- Review authentication and permission settings.
- Use an appropriately managed database.
- Add a proper production configuration.

Do not use the current development configuration to host real personal financial data on a public server.

The Max assistant provides simple rule-based insights and does not replace professional financial advice.

## Possible Future Improvements

Potential enhancements for future versions:

- Interactive date-range analytics.
- Additional chart types.
- Budget notifications.
- Recurring expenses.
- Exportable monthly reports.
- Improved mobile interface.
- Production deployment configuration.
- Additional automated tests.

These are possible future improvements and are not presented as existing features.

---

**Created by Maksim Kernazhytski**
