from decimal import Decimal
from django.conf import settings
from django.db import models
from django.utils import timezone


class Category(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='custom_categories',
    )
    name = models.CharField(max_length=80)
    slug = models.SlugField()
    icon = models.CharField(max_length=8, default='💸')
    color = models.CharField(max_length=20, default='#7c5cff')
    is_default = models.BooleanField(default=True)

    class Meta:
        ordering = ['is_default', 'name']
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class Expense(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='expenses')
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name='expenses')
    title = models.CharField(max_length=120)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(default=timezone.localdate)
    note = models.TextField(blank=True)

    class Meta:
        ordering = ['-date', '-id']

    def __str__(self):
        return f'{self.user.username} — {self.title} — {self.amount}'


class MonthlyBudget(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monthly_budgets')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True, related_name='budgets')
    month = models.DateField(help_text='Use the first day of the month.')
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        unique_together = ('user', 'category', 'month')
        ordering = ['-month', 'category__name']

    def __str__(self):
        label = self.category.name if self.category else 'Overall'
        return f'{self.user.username} — {label} — {self.month:%Y-%m}'


class SavingGoal(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='saving_goals')
    name = models.CharField(max_length=120)
    target_amount = models.DecimalField(max_digits=10, decimal_places=2)
    current_amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    deadline = models.DateField(null=True, blank=True)
    color = models.CharField(max_length=20, default='#23c4ff')
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['deadline', 'name']

    @property
    def progress_percent(self):
        if not self.target_amount:
            return 0
        return int(min(100, (self.current_amount / self.target_amount) * 100))

    @property
    def is_overdue(self):
        return bool(self.deadline and self.deadline < timezone.localdate() and self.progress_percent < 100)

    def __str__(self):
        return f'{self.user.username} — {self.name}'


class AIInsight(models.Model):
    SEVERITY_CHOICES = [
        ('positive', 'Positive'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('danger', 'Danger'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='ai_insights')
    insight_type = models.CharField(max_length=50)
    title = models.CharField(max_length=120)
    message = models.TextField()
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='info')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user.username} — {self.title}'
