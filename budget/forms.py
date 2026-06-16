from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify

from .models import Category, Expense, MonthlyBudget, SavingGoal



CATEGORY_ICON_CHOICES = [
    ('💸', '💸 General / Other'),
    ('💰', '💰 Money / Savings'),
    ('💳', '💳 Card / Subscriptions'),
    ('🍔', '🍔 Food'),
    ('☕', '☕ Coffee'),
    ('🚌', '🚌 Transport'),
    ('🚗', '🚗 Car'),
    ('🏠', '🏠 Rent / Home'),
    ('💡', '💡 Utilities / Bills'),
    ('🎮', '🎮 Entertainment'),
    ('📚', '📚 Education'),
    ('🛍️', '🛍️ Shopping'),
    ('💊', '💊 Health'),
    ('🐶', '🐶 Pets'),
    ('✈️', '✈️ Travel'),
    ('📱', '📱 Phone'),
    ('💻', '💻 Technology'),
    ('🎁', '🎁 Gifts'),
    ('🏋️', '🏋️ Fitness'),
    ('🧼', '🧼 Cleaning'),
]

MONTH_CHOICES = [
    (1, 'January'),
    (2, 'February'),
    (3, 'March'),
    (4, 'April'),
    (5, 'May'),
    (6, 'June'),
    (7, 'July'),
    (8, 'August'),
    (9, 'September'),
    (10, 'October'),
    (11, 'November'),
    (12, 'December'),
]




def category_queryset_for_user(user):
    if not user or not user.is_authenticated:
        return Category.objects.filter(is_default=True)
    return Category.objects.filter(Q(is_default=True) | Q(user=user)).order_by('is_default', 'name')

def year_choices():
    current_year = timezone.localdate().year
    return [(year, year) for year in range(current_year - 2, current_year + 5)]


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class ExpenseForm(forms.ModelForm):
    class Meta:
        model = Expense
        fields = ['title', 'amount', 'category', 'date', 'note']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Optional note...'}),
            'title': forms.TextInput(attrs={'placeholder': 'Coffee, groceries, bus ticket...'}),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = category_queryset_for_user(user)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Amount must be greater than zero.')
        return amount


class ExpenseFilterForm(forms.Form):
    category = forms.ModelChoiceField(
        queryset=None,
        required=False,
        empty_label='All categories',
        label='Category',
    )
    date = forms.DateField(
        required=False,
        label='Date',
        widget=forms.DateInput(attrs={'type': 'date'}),
    )

    def __init__(self, *args, **kwargs):
        categories = kwargs.pop('categories')
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = categories


class MonthlyBudgetForm(forms.ModelForm):
    month_number = forms.ChoiceField(
        label='Month',
        choices=MONTH_CHOICES,
        help_text='Choose the month for this budget.'
    )
    year_number = forms.ChoiceField(
        label='Year',
        choices=year_choices,
        help_text='Choose the year for this budget.'
    )

    class Meta:
        model = MonthlyBudget
        fields = ['category', 'amount']
        labels = {
            'category': 'Budget type',
            'amount': 'Budget amount',
        }
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        today = timezone.localdate()
        self.fields['category'].queryset = category_queryset_for_user(user)
        self.fields['month_number'].choices = MONTH_CHOICES
        self.fields['year_number'].choices = year_choices()
        if self.instance and self.instance.pk:
            self.fields['month_number'].initial = self.instance.month.month
            self.fields['year_number'].initial = self.instance.month.year
        else:
            self.fields['month_number'].initial = today.month
            self.fields['year_number'].initial = today.year
        self.fields['category'].empty_label = 'Overall budget'
        self.order_fields(['category', 'amount', 'month_number', 'year_number'])

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if amount <= 0:
            raise forms.ValidationError('Budget must be greater than zero.')
        return amount

    def clean(self):
        cleaned = super().clean()
        month = cleaned.get('month_number')
        year = cleaned.get('year_number')
        if month and year:
            cleaned['month_text'] = timezone.datetime(int(year), int(month), 1).date()
        return cleaned


class BudgetPeriodForm(forms.Form):
    month_number = forms.ChoiceField(label='Month', choices=MONTH_CHOICES)
    year_number = forms.ChoiceField(label='Year', choices=year_choices)

    def __init__(self, *args, **kwargs):
        initial_date = kwargs.pop('initial_date', timezone.localdate())
        super().__init__(*args, **kwargs)
        self.fields['year_number'].choices = year_choices()
        self.fields['month_number'].initial = initial_date.month
        self.fields['year_number'].initial = initial_date.year

    def selected_month(self):
        if self.is_valid():
            return timezone.datetime(
                int(self.cleaned_data['year_number']),
                int(self.cleaned_data['month_number']),
                1,
            ).date()
        today = timezone.localdate()
        return today.replace(day=1)


class SavingGoalForm(forms.ModelForm):
    class Meta:
        model = SavingGoal
        fields = ['name', 'target_amount', 'current_amount', 'deadline', 'color']
        labels = {
            'target_amount': 'Target amount',
            'current_amount': 'Current amount',
        }
        widgets = {
            'deadline': forms.DateInput(attrs={'type': 'date'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
            'target_amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'current_amount': forms.NumberInput(attrs={'min': '0.00', 'step': '0.01'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['deadline'].widget.attrs['min'] = timezone.localdate().isoformat()

    def clean_deadline(self):
        deadline = self.cleaned_data.get('deadline')
        if deadline and deadline < timezone.localdate():
            raise forms.ValidationError('Deadline cannot be in the past.')
        return deadline

    def clean(self):
        cleaned = super().clean()
        target = cleaned.get('target_amount')
        current = cleaned.get('current_amount')
        if target is not None and target <= 0:
            self.add_error('target_amount', 'Target must be greater than zero.')
        if current is not None and current < 0:
            self.add_error('current_amount', 'Current amount cannot be negative.')
        return cleaned


class CategoryForm(forms.ModelForm):
    icon = forms.ChoiceField(
        label='Icon',
        choices=CATEGORY_ICON_CHOICES,
        initial='💸',
        help_text='Choose an icon from the list. It will be shown near expenses and in category cards.',
    )

    class Meta:
        model = Category
        fields = ['name', 'icon', 'color']
        labels = {
            'name': 'Category name',
            'color': 'Color',
        }
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Subscriptions, pets, travel...'}),
            'color': forms.TextInput(attrs={'type': 'color'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.icon:
            valid_icons = {value for value, _label in CATEGORY_ICON_CHOICES}
            if self.instance.icon not in valid_icons:
                self.fields['icon'].choices = [(self.instance.icon, f'{self.instance.icon} Current icon')] + list(CATEGORY_ICON_CHOICES)


    def clean_name(self):
        name = (self.cleaned_data.get('name') or '').strip()
        if not name:
            raise forms.ValidationError('Category name is required.')
        slug = slugify(name)
        if not slug:
            raise forms.ValidationError('Use at least one normal letter or number.')
        existing = category_queryset_for_user(self.user).filter(slug=slug)
        if self.instance and self.instance.pk:
            existing = existing.exclude(pk=self.instance.pk)
        if existing.exists():
            raise forms.ValidationError('This category already exists.')
        self.cleaned_data['slug_value'] = slug
        return name

    def save(self, commit=True):
        category = super().save(commit=False)
        category.slug = self.cleaned_data.get('slug_value') or slugify(category.name)
        if self.user and self.user.is_authenticated and not category.is_default:
            category.user = self.user
        if commit:
            category.save()
        return category
