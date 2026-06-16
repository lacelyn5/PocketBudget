from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, LogoutView
from django.db.models.deletion import ProtectedError
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils import timezone

from .ai_engine import generate_ai_insights
from .chart_engine import CHART_KEYS, build_chart_svg, chart_filename, charts_context, csv_for_chart
from .forms import (
    BudgetPeriodForm,
    CategoryForm,
    ExpenseFilterForm,
    ExpenseForm,
    MonthlyBudgetForm,
    RegisterForm,
    SavingGoalForm,
    category_queryset_for_user,
)
from .models import Category, Expense, MonthlyBudget, SavingGoal
from .services import admin_stats_context, budget_page_context, dashboard_context


class BudgetLoginView(LoginView):
    template_name = 'budget/login.html'


class BudgetLogoutView(LogoutView):
    next_page = 'login'


def register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, 'Account created. Max is ready to help with your budget.')
        return redirect('dashboard')
    return render(request, 'budget/register.html', {'form': form})


@login_required
def dashboard(request):
    return render(request, 'budget/dashboard.html', dashboard_context(request.user))


@login_required
def expense_list(request):
    categories = category_queryset_for_user(request.user)
    filter_form = ExpenseFilterForm(request.GET or None, categories=categories)
    expenses = Expense.objects.filter(user=request.user).select_related('category')

    if filter_form.is_valid():
        category = filter_form.cleaned_data.get('category')
        selected_date = filter_form.cleaned_data.get('date')
        if category:
            expenses = expenses.filter(category=category)
        if selected_date:
            expenses = expenses.filter(date=selected_date)

    return render(request, 'budget/expense_list.html', {
        'expenses': expenses,
        'filter_form': filter_form,
    })


@login_required
def add_expense(request):
    form = ExpenseForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        expense = form.save(commit=False)
        expense.user = request.user
        expense.save()
        generate_ai_insights(request.user, persist=True)
        messages.success(request, 'Expense added. Max updated the numbers.')
        return redirect('dashboard')
    return render(request, 'budget/expense_form.html', {'form': form, 'title': 'Add expense', 'button_label': 'Save expense'})


@login_required
def edit_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    form = ExpenseForm(request.POST or None, instance=expense, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        generate_ai_insights(request.user, persist=True)
        messages.success(request, 'Expense updated.')
        return redirect('expense_list')
    return render(request, 'budget/expense_form.html', {'form': form, 'title': 'Edit expense', 'button_label': 'Save changes'})


@login_required
@require_POST
def delete_expense(request, expense_id):
    expense = get_object_or_404(Expense, id=expense_id, user=request.user)
    expense.delete()
    generate_ai_insights(request.user, persist=True)
    messages.success(request, 'Expense deleted.')
    return redirect('expense_list')


def _budget_redirect(month):
    return f'{reverse("budgets")}?month_number={month.month}&year_number={month.year}'


@login_required
def budgets(request):
    today = timezone.localdate().replace(day=1)
    period_form = BudgetPeriodForm(request.GET or None, initial_date=today)
    selected_month = period_form.selected_month()

    form = MonthlyBudgetForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        budget = form.save(commit=False)
        budget.user = request.user
        budget.month = form.cleaned_data['month_text']
        MonthlyBudget.objects.update_or_create(
            user=request.user,
            category=budget.category,
            month=budget.month,
            defaults={'amount': budget.amount},
        )
        generate_ai_insights(request.user, persist=True)
        messages.success(request, 'Budget saved.')
        return redirect(_budget_redirect(budget.month))

    context = budget_page_context(request.user, selected_month)
    context.update({'form': form, 'period_form': period_form})
    return render(request, 'budget/budgets.html', context)


@login_required
def edit_budget(request, budget_id):
    budget = get_object_or_404(MonthlyBudget, id=budget_id, user=request.user)
    form = MonthlyBudgetForm(request.POST or None, instance=budget, user=request.user)
    if request.method == 'POST' and form.is_valid():
        new_category = form.cleaned_data['category']
        new_month = form.cleaned_data['month_text']
        duplicate = MonthlyBudget.objects.filter(
            user=request.user,
            category=new_category,
            month=new_month,
        ).exclude(id=budget.id).first()
        if duplicate:
            duplicate.amount = form.cleaned_data['amount']
            duplicate.save(update_fields=['amount'])
            budget.delete()
            saved_month = duplicate.month
        else:
            updated = form.save(commit=False)
            updated.user = request.user
            updated.month = new_month
            updated.save()
            saved_month = updated.month
        generate_ai_insights(request.user, persist=True)
        messages.success(request, 'Budget updated.')
        return redirect(_budget_redirect(saved_month))
    return render(request, 'budget/budget_form.html', {'form': form, 'budget': budget})


@login_required
@require_POST
def delete_budget(request, budget_id):
    budget = get_object_or_404(MonthlyBudget, id=budget_id, user=request.user)
    month = budget.month
    budget.delete()
    generate_ai_insights(request.user, persist=True)
    messages.success(request, 'Budget deleted.')
    return redirect(_budget_redirect(month))


@login_required
def goals(request):
    form = SavingGoalForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        goal = form.save(commit=False)
        goal.user = request.user
        goal.save()
        generate_ai_insights(request.user, persist=True)
        messages.success(request, 'Saving goal saved.')
        return redirect('goals')
    return render(request, 'budget/goals.html', {
        'form': form,
        'goals': SavingGoal.objects.filter(user=request.user),
    })


@login_required
def edit_goal(request, goal_id):
    goal = get_object_or_404(SavingGoal, id=goal_id, user=request.user)
    form = SavingGoalForm(request.POST or None, instance=goal)
    if request.method == 'POST' and form.is_valid():
        form.save()
        generate_ai_insights(request.user, persist=True)
        messages.success(request, 'Goal updated.')
        return redirect('goals')
    return render(request, 'budget/goal_form.html', {'form': form, 'goal': goal})


@login_required
@require_POST
def delete_goal(request, goal_id):
    goal = get_object_or_404(SavingGoal, id=goal_id, user=request.user)
    goal.delete()
    generate_ai_insights(request.user, persist=True)
    messages.success(request, 'Goal deleted.')
    return redirect('goals')


@login_required
def categories(request):
    form = CategoryForm(request.POST or None, user=request.user)
    if request.method == 'POST' and form.is_valid():
        category = form.save(commit=False)
        category.user = request.user
        category.is_default = False
        category.save()
        messages.success(request, 'Category added.')
        return redirect('categories')
    return render(request, 'budget/categories.html', {
        'form': form,
        'categories': category_queryset_for_user(request.user),
    })


@login_required
def edit_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user, is_default=False)
    form = CategoryForm(request.POST or None, instance=category, user=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Category updated.')
        return redirect('categories')
    return render(request, 'budget/category_form.html', {'form': form, 'category': category})


@login_required
@require_POST
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id, user=request.user, is_default=False)
    if category.expenses.exists() or category.budgets.exists():
        messages.error(request, 'This category is already used, so it cannot be deleted.')
        return redirect('categories')
    try:
        category.delete()
        messages.success(request, 'Category deleted.')
    except ProtectedError:
        messages.error(request, 'This category is already used, so it cannot be deleted.')
    return redirect('categories')


@login_required
def charts(request):
    return render(request, 'budget/charts.html', charts_context(request.user))


@login_required
def download_chart_svg(request, chart_key):
    if chart_key not in CHART_KEYS:
        chart_key = 'category'
    svg = build_chart_svg(request.user, chart_key)
    response = HttpResponse(svg, content_type='image/svg+xml')
    response['Content-Disposition'] = f'attachment; filename="{chart_filename(chart_key, "svg")}"'
    return response


@login_required
def download_chart_csv(request, chart_key):
    if chart_key not in CHART_KEYS:
        chart_key = 'category'
    csv_data = csv_for_chart(request.user, chart_key)
    response = HttpResponse(csv_data, content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{chart_filename(chart_key, "csv")}"'
    return response


@login_required
def ai_insights(request):
    insights = generate_ai_insights(request.user, persist=True)
    return render(request, 'budget/ai_insights.html', {'insights': insights})


def _is_admin_user(user):
    return user.is_authenticated and (user.is_staff or user.username == 'admin')


@user_passes_test(_is_admin_user)
def admin_stats(request):
    return render(request, 'budget/admin_stats.html', admin_stats_context())
