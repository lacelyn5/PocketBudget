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

Open the project folder in terminal. It should be the folder where `manage.py` is located.

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Then open:

```text
http://127.0.0.1:8000/
```

## Admin panel

After creating a superuser, open:

```text
http://127.0.0.1:8000/admin/
```

The custom project stats page is here:

```text
http://127.0.0.1:8000/admin-stats/
```

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
