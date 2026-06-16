from decimal import Decimal
from django.contrib.auth.models import User
from django.db.models import Avg, Count, Sum
from django.utils import timezone

from .ai_engine import generate_ai_insights, generate_month_summary, get_category_totals, get_total_spent, month_start
from .models import Category, Expense, MonthlyBudget, SavingGoal


def _percent(part, whole, places=1):
    if not whole:
        return Decimal('0.0')
    value = (Decimal(part) / Decimal(whole)) * Decimal('100')
    return value.quantize(Decimal('0.1')) if places == 1 else int(value)


def _current_month():
    return month_start()


def dashboard_context(user):
    start = _current_month()
    total_spent = get_total_spent(user, start)
    category_totals = get_category_totals(user, start)
    overall_budget = MonthlyBudget.objects.filter(user=user, category__isnull=True, month=start).first()
    budget_amount = overall_budget.amount if overall_budget else Decimal('0.00')
    budget_percent = int((total_spent / budget_amount) * 100) if budget_amount else 0
    budget_percent = min(100, budget_percent)

    category_rows = []
    for category, total in sorted(category_totals.items(), key=lambda item: item[1], reverse=True):
        share = int((total / total_spent) * 100) if total_spent else 0
        category_rows.append({'name': category, 'total': total, 'share': share})

    return {
        'total_spent': total_spent,
        'monthly_budget': budget_amount,
        'budget_percent': budget_percent,
        'budget_left': max(Decimal('0.00'), budget_amount - total_spent) if budget_amount else Decimal('0.00'),
        'category_rows': category_rows,
        'recent_expenses': Expense.objects.filter(user=user).select_related('category')[:6],
        'goals': SavingGoal.objects.filter(user=user, is_active=True)[:4],
        'insights': generate_ai_insights(user, persist=True),
        'month_summary': generate_month_summary(user),
    }


def budget_page_context(user, selected_month):
    budgets = MonthlyBudget.objects.filter(user=user, month=selected_month).select_related('category')
    overall_budget = None
    category_budgets = []

    for budget in budgets:
        if budget.category_id is None:
            overall_budget = budget
        else:
            category_budgets.append(budget)

    overall_amount = overall_budget.amount if overall_budget else Decimal('0.00')
    category_rows = []
    for budget in sorted(category_budgets, key=lambda item: item.category.name):
        share = _percent(budget.amount, overall_amount)
        category_rows.append({
            'budget': budget,
            'share': share,
            'bar_width': min(100, float(share)),
        })

    total_category_limits = sum((row['budget'].amount for row in category_rows), Decimal('0.00'))
    planned_percent = _percent(total_category_limits, overall_amount) if overall_amount else Decimal('0.0')

    return {
        'selected_month': selected_month,
        'overall_budget': overall_budget,
        'category_budgets': category_rows,
        'total_category_limits': total_category_limits,
        'planned_percent': planned_percent,
        'planned_width': min(100, float(planned_percent)),
    }


def admin_stats_context():
    total_users = User.objects.count()
    total_expenses = Expense.objects.count()
    total_budgets = MonthlyBudget.objects.count()
    total_goals = SavingGoal.objects.count()
    total_spent = Expense.objects.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
    average_expense = Expense.objects.aggregate(avg=Avg('amount'))['avg'] or Decimal('0.00')
    current_month = _current_month()
    month_spent = Expense.objects.filter(date__gte=current_month).aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    top_category = (
        Expense.objects.values('category__name')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')
        .first()
    )

    category_rows_raw = list(
        Expense.objects.values('category__name', 'category__icon', 'category__color')
        .annotate(total=Sum('amount'), count=Count('id'))
        .order_by('-total')[:8]
    )
    biggest_category_total = category_rows_raw[0]['total'] if category_rows_raw else Decimal('0.00')
    category_rows = []
    for row in category_rows_raw:
        share = _percent(row['total'], total_spent)
        width = int((row['total'] / biggest_category_total) * 100) if biggest_category_total else 0
        category_rows.append({**row, 'share': share, 'width': width})

    user_rows_raw = list(
        User.objects.annotate(expense_count=Count('expenses'), expense_total=Sum('expenses__amount'))
        .order_by('-date_joined')[:6]
    )
    user_rows = []
    for user in user_rows_raw:
        user_rows.append({
            'username': user.username,
            'is_staff': user.is_staff,
            'expense_count': user.expense_count,
            'expense_total': user.expense_total or Decimal('0.00'),
            'date_joined': user.date_joined,
        })

    budget_rows_raw = list(
        MonthlyBudget.objects.select_related('user', 'category')
        .filter(month=current_month)
        .order_by('category__name', 'user__username')[:8]
    )

    return {
        'total_users': total_users,
        'total_expenses': total_expenses,
        'total_budgets': total_budgets,
        'total_goals': total_goals,
        'total_spent': total_spent,
        'average_expense': average_expense,
        'month_spent': month_spent,
        'current_month': current_month,
        'top_category': top_category,
        'recent_expenses': Expense.objects.select_related('user', 'category')[:10],
        'category_rows': category_rows,
        'recent_users': user_rows,
        'budget_rows': budget_rows_raw,
        'category_count': Category.objects.count(),
    }
