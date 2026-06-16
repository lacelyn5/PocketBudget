from collections import defaultdict
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone

from .models import AIInsight, Expense, MonthlyBudget, SavingGoal


def month_start(date=None):
    date = date or timezone.localdate()
    return date.replace(day=1)


def get_month_range(date=None):
    start = month_start(date)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def get_month_expenses(user, date=None):
    start, end = get_month_range(date)
    return Expense.objects.filter(user=user, date__gte=start, date__lt=end).select_related('category')


def get_category_totals(user, date=None):
    totals = defaultdict(Decimal)
    for expense in get_month_expenses(user, date):
        totals[expense.category.name] += expense.amount
    return dict(totals)


def get_total_spent(user, date=None):
    total = get_month_expenses(user, date).aggregate(total=Sum('amount'))['total']
    return total or Decimal('0.00')


def _money(value):
    return f'{Decimal(value):.2f}'


def detect_budget_risks(user, date=None):
    start = month_start(date)
    expenses = get_month_expenses(user, date)
    insights = []

    overall_budget = MonthlyBudget.objects.filter(user=user, category__isnull=True, month=start).first()
    total_spent = get_total_spent(user, date)
    if overall_budget:
        percent = int((total_spent / overall_budget.amount) * 100) if overall_budget.amount else 0
        if percent >= 100:
            insights.append({
                'type': 'budget',
                'severity': 'danger',
                'title': 'Monthly budget is over limit',
                'message': f'You spent {_money(total_spent)} zł out of {_money(overall_budget.amount)} zł this month. Max would stop the random extras for a few days and keep only the necessary stuff.',
            })
        elif percent >= 80:
            insights.append({
                'type': 'budget',
                'severity': 'warning',
                'title': 'Budget warning',
                'message': f'You used about {percent}% of your monthly budget. It is not ruined, but this is the moment to slow down a bit.',
            })
        else:
            insights.append({
                'type': 'budget',
                'severity': 'positive',
                'title': 'Budget looks okay',
                'message': f'You used about {percent}% of your monthly budget. Keep this pace and the end of the month should be fine.',
            })

    category_spending = expenses.values('category__name').annotate(total=Sum('amount')).order_by('-total')
    for row in category_spending[:3]:
        category_name = row['category__name']
        spent = row['total'] or Decimal('0.00')
        category_budget = MonthlyBudget.objects.filter(
            user=user,
            category__name=category_name,
            month=start,
        ).first()
        if category_budget:
            percent = int((spent / category_budget.amount) * 100) if category_budget.amount else 0
            if percent >= 100:
                insights.append({
                    'type': 'category_budget',
                    'severity': 'danger',
                    'title': f'{category_name} budget exceeded',
                    'message': f'{category_name} is already at {_money(spent)} zł out of {_money(category_budget.amount)} zł. Max suggests setting a small weekly limit for this category.',
                })
            elif percent >= 80:
                insights.append({
                    'type': 'category_budget',
                    'severity': 'warning',
                    'title': f'{category_name} is close to the limit',
                    'message': f'{category_name} is at around {percent}% of its budget. A few cheaper choices now can save the month.',
                })
    return insights


def detect_spending_patterns(user, date=None):
    expenses = list(get_month_expenses(user, date).order_by('-amount'))
    total = get_total_spent(user, date)
    insights = []

    if not expenses:
        insights.append({
            'type': 'getting_started',
            'severity': 'info',
            'title': 'Start tracking',
            'message': 'Add a few expenses and Max will start finding patterns. For now there is not enough data to say anything useful.',
        })
        return insights

    biggest = expenses[0]
    if biggest.amount >= Decimal('100.00'):
        insights.append({
            'type': 'large_expense',
            'severity': 'info',
            'title': 'Largest expense spotted',
            'message': f'Your biggest expense this month is "{biggest.title}" at {_money(biggest.amount)} zł. If it was planned, fine. If not, it is worth checking.',
        })

    category_totals = get_category_totals(user, date)
    if category_totals and total > 0:
        top_category, top_total = max(category_totals.items(), key=lambda item: item[1])
        share = int((top_total / total) * 100)
        if share >= 45:
            insights.append({
                'type': 'category_share',
                'severity': 'warning',
                'title': f'{top_category} takes a big part',
                'message': f'{top_category} is about {share}% of your monthly spending. Max would check this category first before cutting anything else.',
            })
        else:
            insights.append({
                'type': 'balanced_spending',
                'severity': 'positive',
                'title': 'Spending is fairly balanced',
                'message': f'Your top category is {top_category} at about {share}% of monthly spending. Nothing looks crazy right now.',
            })

    recent_count = len([expense for expense in expenses if (timezone.localdate() - expense.date).days <= 7])
    if recent_count >= 5:
        insights.append({
            'type': 'frequency',
            'severity': 'info',
            'title': 'Busy spending week',
            'message': f'You added {recent_count} expenses in the last 7 days. Max suggests checking if these are real needs or just small leaks.',
        })

    return insights


def detect_goal_status(user):
    insights = []
    today = timezone.localdate()
    for goal in SavingGoal.objects.filter(user=user, is_active=True)[:3]:
        progress = goal.progress_percent
        if goal.deadline and goal.deadline < today and progress < 100:
            days_late = (today - goal.deadline).days
            insights.append({
                'type': 'goal_deadline',
                'severity': 'danger',
                'title': f'{goal.name} deadline passed',
                'message': f'The deadline for "{goal.name}" passed {days_late} day(s) ago. Max would update the date or lower the target so the goal becomes realistic again.',
            })
        elif progress >= 100:
            insights.append({
                'type': 'goal',
                'severity': 'positive',
                'title': f'{goal.name} is complete',
                'message': f'You reached your saving goal "{goal.name}". Max says this one can be marked as a win.',
            })
        elif progress >= 60:
            insights.append({
                'type': 'goal',
                'severity': 'positive',
                'title': f'{goal.name} is moving well',
                'message': f'You are {progress}% toward "{goal.name}". Keep adding small amounts and it should be realistic.',
            })
        else:
            insights.append({
                'type': 'goal',
                'severity': 'info',
                'title': f'{goal.name} needs a plan',
                'message': f'You are {progress}% toward "{goal.name}". Try adding a small fixed amount after every payday.',
            })
    return insights


def generate_ai_insights(user, persist=False):
    raw = []
    raw.extend(detect_budget_risks(user))
    raw.extend(detect_spending_patterns(user))
    raw.extend(detect_goal_status(user))

    unique = []
    seen = set()
    for item in raw:
        key = (item['type'], item['title'])
        if key not in seen:
            seen.add(key)
            unique.append(item)

    if persist:
        AIInsight.objects.filter(user=user).delete()
        for item in unique[:8]:
            AIInsight.objects.create(
                user=user,
                insight_type=item['type'],
                title=item['title'],
                message=item['message'],
                severity=item['severity'],
            )
    return unique[:8]


def generate_month_summary(user):
    total = get_total_spent(user)
    totals = get_category_totals(user)
    if not totals:
        return 'No spending data yet. Add expenses first and Max will make a useful monthly summary.'
    top_category, top_total = max(totals.items(), key=lambda item: item[1])
    return (
        f'This month you spent {_money(total)} zł in total. '
        f'The biggest category is {top_category} with {_money(top_total)} zł. '
        f'Max would start there if you want to save money fast.'
    )
