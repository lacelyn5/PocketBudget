# PocketBudget AI

PocketBudget AI is a Django web application for tracking personal expenses, budgets and saving goals. It also has a local assistant called **Max** that gives simple money tips and creates charts from saved data.

The project works locally. It does not use a paid API.

## Main features

- user registration, login and logout
- dashboard with monthly spending summary
- add, edit, delete and filter expenses
- filter expenses by category and date
- add, edit and delete custom categories
- overall monthly budget
- category budgets with percentage from the overall budget
- month and year filter for budgets
- saving goals with progress bars
- Max Tips page with local budget advice
- Max Charts page with downloadable SVG charts and CSV data
- admin statistics page
- link to Django Admin for database management
- automatic default categories through migrations
- tests for the main functions

## Technologies used

- Python
- Django
- SQLite
- Django ORM
- HTML
- CSS
- JavaScript
- SVG charts

## How to run the project

### Requirements

- Python 3.10 or newer.
- pip (Python package installer).

### Installation on Windows

1. Open the project folder in Command Prompt or PowerShell. It should be the folder containing `manage.py`.

2. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment.

   **Command Prompt:**

   ```bat
   venv\Scripts\activate
   ```

   **PowerShell:**

   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

4. Install the dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Apply database migrations:

   ```bash
   python manage.py migrate
   ```

6. Start the development server:

   ```bash
   python manage.py runserver
   ```

7. Open the application in your browser:

   **http://127.0.0.1:8000/**

## Admin statistics page

The application also includes a custom statistics page for viewing project data.

After starting the server and logging in, open:

[Admin Statistics](http://127.0.0.1:8000/admin-stats/)

## How Max works

Max is a local rule-based assistant. It checks the saved data in the database and gives short tips. It looks at monthly spending, budgets, category limits, saving goals and charts.

Max can warn the user when spending is close to the budget limit, show the top spending category, check saving goals and explain charts.

## Run tests

```bash
python manage.py test
```

## Suggested demo flow

1. Register a normal user.
2. Add a custom category.
3. Add a few expenses.
4. Create an overall monthly budget.
5. Add one category budget.
6. Create a saving goal.
7. Open Max Tips.
8. Open Max Charts.
9. Download one SVG chart or CSV file.
10. Open Admin Stats and Django Admin.
