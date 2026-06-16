from decimal import Decimal
from django.contrib.auth.models import User
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from .ai_engine import generate_ai_insights
from .models import Category, Expense, MonthlyBudget, SavingGoal


@override_settings(PASSWORD_HASHERS=['django.contrib.auth.hashers.MD5PasswordHasher'])
class PocketBudgetTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        User.objects.create_superuser(username='admin', password='adminpass123')

    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='player', password='pass12345')
        self.category = Category.objects.get(slug='food')
        self.transport = Category.objects.get(slug='transport')

    def test_register_page_loads(self):
        response = self.client.get(reverse('register'))
        self.assertEqual(response.status_code, 200)

    def test_user_registration_works(self):
        response = self.client.post(reverse('register'), {
            'username': 'newplayer',
            'email': 'new@example.com',
            'password1': 'StrongPass12345',
            'password2': 'StrongPass12345',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username='newplayer').exists())

    def test_login_works(self):
        response = self.client.post(reverse('login'), {'username': 'player', 'password': 'pass12345'})
        self.assertEqual(response.status_code, 302)

    def test_seed_categories_created_without_demo_user(self):
        self.assertGreaterEqual(Category.objects.count(), 8)
        self.assertFalse(User.objects.filter(username='demo').exists())
        self.assertTrue(User.objects.filter(username='admin', is_staff=True).exists())

    def test_dashboard_requires_login(self):
        response = self.client.get(reverse('dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertIn('/login/', response.url)

    def test_add_expense_works(self):
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('add_expense'), {
            'title': 'Coffee',
            'amount': '6.50',
            'category': self.category.id,
            'date': timezone.localdate().isoformat(),
            'note': 'Test note',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(user=self.user, title='Coffee').exists())

    def test_edit_expense_works(self):
        expense = Expense.objects.create(user=self.user, title='Coffee', amount=Decimal('6.50'), category=self.category)
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('edit_expense', args=[expense.id]), {
            'title': 'Coffee and snack',
            'amount': '12.00',
            'category': self.category.id,
            'date': expense.date.isoformat(),
            'note': 'Updated',
        })
        self.assertEqual(response.status_code, 302)
        expense.refresh_from_db()
        self.assertEqual(expense.title, 'Coffee and snack')
        self.assertEqual(expense.amount, Decimal('12.00'))

    def test_expense_date_filter_works(self):
        today = timezone.localdate()
        yesterday = today - timezone.timedelta(days=1)
        Expense.objects.create(user=self.user, title='Today lunch', amount=Decimal('20.00'), category=self.category, date=today)
        Expense.objects.create(user=self.user, title='Yesterday bus', amount=Decimal('8.00'), category=self.transport, date=yesterday)
        self.client.login(username='player', password='pass12345')
        response = self.client.get(reverse('expense_list'), {'date': today.isoformat()})
        self.assertContains(response, 'Today lunch')
        self.assertNotContains(response, 'Yesterday bus')

    def test_expense_list_only_shows_current_user(self):
        other = User.objects.create_user(username='other', password='pass12345')
        Expense.objects.create(user=self.user, title='Mine', amount=Decimal('5.00'), category=self.category)
        Expense.objects.create(user=other, title='Other expense', amount=Decimal('5.00'), category=self.category)
        self.client.login(username='player', password='pass12345')
        response = self.client.get(reverse('expense_list'))
        self.assertContains(response, 'Mine')
        self.assertNotContains(response, 'Other expense')

    def test_category_page_can_add_custom_category(self):
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('categories'), {
            'name': 'Subscriptions',
            'icon': '💳',
            'color': '#23c4ff',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(user=self.user, name='Subscriptions', is_default=False).exists())

    def test_custom_category_can_be_used_for_expense(self):
        category = Category.objects.create(user=self.user, name='Pets', slug='pets', icon='🐶', color='#4cc38a', is_default=False)
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('add_expense'), {
            'title': 'Dog food',
            'amount': '40.00',
            'category': category.id,
            'date': timezone.localdate().isoformat(),
            'note': '',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Expense.objects.filter(user=self.user, title='Dog food', category=category).exists())

    def test_used_category_cannot_be_deleted(self):
        category = Category.objects.create(user=self.user, name='Pets', slug='pets', icon='🐶', color='#4cc38a', is_default=False)
        Expense.objects.create(user=self.user, title='Dog food', amount=Decimal('40.00'), category=category)
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('delete_category', args=[category.id]))
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(id=category.id).exists())


    def test_category_form_uses_icon_dropdown(self):
        self.client.login(username='player', password='pass12345')
        response = self.client.get(reverse('categories'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '<select name="icon"', html=False)
        self.assertContains(response, '💳 Card / Subscriptions')

    def test_monthly_budget_can_be_saved(self):
        self.client.login(username='player', password='pass12345')
        today = timezone.localdate()
        response = self.client.post(reverse('budgets'), {
            'category': '',
            'amount': '500.00',
            'month_number': today.month,
            'year_number': today.year,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(MonthlyBudget.objects.filter(user=self.user, amount=Decimal('500.00')).exists())

    def test_budget_month_filter_and_share_display(self):
        self.client.login(username='player', password='pass12345')
        month = timezone.datetime(2026, 8, 1).date()
        MonthlyBudget.objects.create(user=self.user, month=month, amount=Decimal('1000.00'))
        MonthlyBudget.objects.create(user=self.user, month=month, category=self.category, amount=Decimal('250.00'))
        response = self.client.get(reverse('budgets'), {'month_number': 8, 'year_number': 2026})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'August 2026')
        self.assertContains(response, '25.0% of overall budget')

    def test_edit_and_delete_budget_work(self):
        budget = MonthlyBudget.objects.create(user=self.user, month=timezone.localdate().replace(day=1), amount=Decimal('600.00'))
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('edit_budget', args=[budget.id]), {
            'category': '',
            'amount': '700.00',
            'month_number': budget.month.month,
            'year_number': budget.month.year,
        })
        self.assertEqual(response.status_code, 302)
        budget.refresh_from_db()
        self.assertEqual(budget.amount, Decimal('700.00'))
        response = self.client.post(reverse('delete_budget', args=[budget.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(MonthlyBudget.objects.filter(id=budget.id).exists())

    def test_saving_goal_can_be_saved(self):
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('goals'), {
            'name': 'Laptop',
            'target_amount': '1000.00',
            'current_amount': '200.00',
            'deadline': timezone.localdate().isoformat(),
            'color': '#23c4ff',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(SavingGoal.objects.filter(user=self.user, name='Laptop').exists())

    def test_past_goal_deadline_is_rejected(self):
        self.client.login(username='player', password='pass12345')
        past = timezone.localdate() - timezone.timedelta(days=1)
        response = self.client.post(reverse('goals'), {
            'name': 'Old goal',
            'target_amount': '1000.00',
            'current_amount': '200.00',
            'deadline': past.isoformat(),
            'color': '#23c4ff',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(SavingGoal.objects.filter(user=self.user, name='Old goal').exists())
        self.assertContains(response, 'Deadline cannot be in the past.')

    def test_ai_warns_about_existing_overdue_goal(self):
        past = timezone.localdate() - timezone.timedelta(days=3)
        SavingGoal.objects.create(user=self.user, name='Old phone', target_amount=Decimal('1000.00'), current_amount=Decimal('100.00'), deadline=past)
        insights = generate_ai_insights(self.user)
        titles = [item['title'] for item in insights]
        self.assertIn('Old phone deadline passed', titles)

    def test_edit_and_delete_goal_work(self):
        goal = SavingGoal.objects.create(user=self.user, name='Phone', target_amount=Decimal('1200.00'), current_amount=Decimal('300.00'))
        self.client.login(username='player', password='pass12345')
        response = self.client.post(reverse('edit_goal', args=[goal.id]), {
            'name': 'New phone',
            'target_amount': '1200.00',
            'current_amount': '500.00',
            'deadline': '',
            'color': '#23c4ff',
        })
        self.assertEqual(response.status_code, 302)
        goal.refresh_from_db()
        self.assertEqual(goal.name, 'New phone')
        self.assertEqual(goal.current_amount, Decimal('500.00'))
        response = self.client.post(reverse('delete_goal', args=[goal.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(SavingGoal.objects.filter(id=goal.id).exists())

    def test_ai_insights_generate_budget_warning(self):
        month = timezone.localdate().replace(day=1)
        MonthlyBudget.objects.create(user=self.user, month=month, amount=Decimal('100.00'))
        Expense.objects.create(user=self.user, title='Big shop', amount=Decimal('95.00'), category=self.category)
        insights = generate_ai_insights(self.user)
        titles = [item['title'] for item in insights]
        self.assertIn('Budget warning', titles)

    def test_ai_insights_page_loads(self):
        self.client.login(username='player', password='pass12345')
        response = self.client.get(reverse('ai_insights'))
        self.assertEqual(response.status_code, 200)

    def test_admin_stats_only_admin(self):
        self.client.login(username='player', password='pass12345')
        response = self.client.get(reverse('admin_stats'))
        self.assertEqual(response.status_code, 302)
        self.client.logout()
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_stats'))
        self.assertEqual(response.status_code, 200)

    def test_admin_stats_contains_extra_sections(self):
        Expense.objects.create(user=self.user, title='Lunch', amount=Decimal('15.00'), category=self.category)
        self.client.login(username='admin', password='adminpass123')
        response = self.client.get(reverse('admin_stats'))
        self.assertContains(response, 'Category breakdown')
        self.assertContains(response, 'Budgets this month')
        self.assertContains(response, 'Average expense')

    def test_charts_page_loads(self):
        self.client.login(username='player', password='pass12345')
        Expense.objects.create(user=self.user, title='Lunch', amount=Decimal('15.00'), category=self.category)
        response = self.client.get(reverse('charts'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Max charts')
        self.assertContains(response, 'Download SVG')

    def test_chart_svg_download_works(self):
        self.client.login(username='player', password='pass12345')
        Expense.objects.create(user=self.user, title='Lunch', amount=Decimal('15.00'), category=self.category)
        response = self.client.get(reverse('download_chart_svg', args=['category']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'image/svg+xml')
        self.assertIn(b'<svg', response.content)

    def test_chart_csv_download_works(self):
        self.client.login(username='player', password='pass12345')
        Expense.objects.create(user=self.user, title='Lunch', amount=Decimal('15.00'), category=self.category)
        response = self.client.get(reverse('download_chart_csv', args=['category']))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn(b'category,amount_zl,share_percent', response.content)
