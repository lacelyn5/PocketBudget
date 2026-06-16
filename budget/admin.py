from django.contrib import admin
from .models import AIInsight, Category, Expense, MonthlyBudget, SavingGoal


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'user', 'icon', 'color', 'is_default')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'user__username')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'category', 'amount', 'date')
    list_filter = ('category', 'date')
    search_fields = ('user__username', 'title', 'note')


@admin.register(MonthlyBudget)
class MonthlyBudgetAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'month', 'amount')
    list_filter = ('month', 'category')


@admin.register(SavingGoal)
class SavingGoalAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'target_amount', 'current_amount', 'deadline', 'is_active')
    list_filter = ('is_active', 'deadline')


@admin.register(AIInsight)
class AIInsightAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'severity', 'created_at')
    list_filter = ('severity', 'insight_type')
    search_fields = ('user__username', 'title', 'message')
