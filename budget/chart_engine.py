import csv
from collections import OrderedDict
from decimal import Decimal
from html import escape
from io import StringIO

from django.db.models import Sum
from django.utils import timezone

from .ai_engine import get_month_expenses, get_total_spent, month_start
from .models import Expense, MonthlyBudget


CHART_KEYS = {'category', 'daily', 'budget'}


def _money(value):
    return f'{Decimal(value):.2f}'


def _decimal_to_float(value):
    return float(value or Decimal('0.00'))


def _format_zl(value):
    return f'{_money(value)} zł'


def _svg_shell(title, subtitle, body, width=760, height=360):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="100%" viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">
    <defs>
        <linearGradient id="pbGrad" x1="0" x2="1" y1="0" y2="0">
            <stop offset="0%" stop-color="#6c63ff" />
            <stop offset="100%" stop-color="#23c4ff" />
        </linearGradient>
        <filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">
            <feDropShadow dx="0" dy="10" stdDeviation="12" flood-color="#000000" flood-opacity="0.20" />
        </filter>
    </defs>
    <rect width="{width}" height="{height}" rx="24" fill="#151a2e" />
    <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="23" fill="none" stroke="rgba(255,255,255,0.12)" />
    <text x="32" y="44" fill="#f4f6ff" font-family="Segoe UI, Arial" font-size="24" font-weight="700">{escape(title)}</text>
    <text x="32" y="72" fill="#aeb8d9" font-family="Segoe UI, Arial" font-size="14">{escape(subtitle)}</text>
    {body}
</svg>'''


def category_chart_rows(user):
    rows = []
    total = get_total_spent(user)
    data = (
        get_month_expenses(user)
        .values('category__name', 'category__icon')
        .annotate(total=Sum('amount'))
        .order_by('-total')
    )
    for row in data:
        amount = row['total'] or Decimal('0.00')
        share = int((amount / total) * 100) if total else 0
        rows.append({
            'category': row['category__name'],
            'icon': row['category__icon'] or '•',
            'amount': amount,
            'share': share,
        })
    return rows


def daily_chart_rows(user, days=14):
    today = timezone.localdate()
    start_date = today - timezone.timedelta(days=days - 1)
    raw = (
        Expense.objects.filter(user=user, date__gte=start_date, date__lte=today)
        .values('date')
        .annotate(total=Sum('amount'))
        .order_by('date')
    )
    totals = {item['date']: item['total'] or Decimal('0.00') for item in raw}
    rows = []
    for index in range(days):
        day = start_date + timezone.timedelta(days=index)
        rows.append({
            'date': day,
            'label': day.strftime('%d %b'),
            'amount': totals.get(day, Decimal('0.00')),
        })
    return rows


def budget_chart_rows(user):
    start = month_start()
    spent = get_total_spent(user)
    budget = MonthlyBudget.objects.filter(user=user, category__isnull=True, month=start).first()
    limit = budget.amount if budget else Decimal('0.00')
    left = max(Decimal('0.00'), limit - spent) if limit else Decimal('0.00')
    percent = int((spent / limit) * 100) if limit else 0
    return {
        'spent': spent,
        'limit': limit,
        'left': left,
        'percent': min(100, percent),
        'raw_percent': percent,
    }


def max_chart_comment(user, chart_key):
    if chart_key == 'category':
        rows = category_chart_rows(user)
        if not rows:
            return 'Max: Add a few expenses first. Empty charts look clean, but they do not say much.'
        top = rows[0]
        if top['share'] >= 45:
            return f'Max: {top["category"]} is taking {top["share"]}% of this month. I would check that category first.'
        return f'Max: Top category is {top["category"]}, but the spending does not look too one-sided right now.'
    if chart_key == 'daily':
        rows = daily_chart_rows(user)
        non_zero = [row for row in rows if row['amount'] > 0]
        if len(non_zero) >= 5:
            return 'Max: This chart shows a pretty active spending period. Small payments can still add up fast.'
        if non_zero:
            return 'Max: Spending is not happening every day, which is usually a good sign.'
        return 'Max: No spending trend yet. Add expenses and the chart will become useful.'
    if chart_key == 'budget':
        data = budget_chart_rows(user)
        if not data['limit']:
            return 'Max: Set a monthly budget first, then I can compare spending with the limit.'
        if data['raw_percent'] >= 100:
            return 'Max: The monthly budget is already over the limit. Time for boring but useful choices.'
        if data['raw_percent'] >= 80:
            return 'Max: You are close to the monthly limit. Not a disaster, but slow down a little.'
        return 'Max: The monthly budget still looks under control.'
    return 'Max: This chart is generated from your saved data.'


def build_category_svg(user):
    rows = category_chart_rows(user)[:7]
    if not rows:
        body = '<text x="32" y="175" fill="#aeb8d9" font-family="Segoe UI, Arial" font-size="18">No expense data yet.</text>'
        return _svg_shell('Spending by category', 'Current month, generated by Max from saved expenses.', body)

    max_amount = max(_decimal_to_float(row['amount']) for row in rows) or 1
    y = 112
    body_parts = []
    for row in rows:
        amount_float = _decimal_to_float(row['amount'])
        bar_width = int((amount_float / max_amount) * 430)
        label = f"{row['icon']} {row['category']}"
        body_parts.append(f'''
        <text x="32" y="{y + 18}" fill="#f4f6ff" font-family="Segoe UI, Arial" font-size="15" font-weight="600">{escape(label)}</text>
        <rect x="205" y="{y}" width="460" height="24" rx="12" fill="#242a42" />
        <rect x="205" y="{y}" width="{max(8, bar_width)}" height="24" rx="12" fill="url(#pbGrad)" />
        <text x="680" y="{y + 18}" fill="#dbe3ff" font-family="Segoe UI, Arial" font-size="14" text-anchor="end">{escape(_format_zl(row['amount']))}</text>
        <text x="205" y="{y + 42}" fill="#8f9abc" font-family="Segoe UI, Arial" font-size="12">{row['share']}% of monthly spending</text>
        ''')
        y += 58
    return _svg_shell('Spending by category', 'Current month, generated by Max from saved expenses.', ''.join(body_parts), height=max(360, y + 18))


def build_daily_svg(user):
    rows = daily_chart_rows(user)
    values = [_decimal_to_float(row['amount']) for row in rows]
    max_value = max(values) or 1
    chart_x = 54
    chart_y = 112
    chart_w = 650
    chart_h = 170
    points = []
    for index, row in enumerate(rows):
        x = chart_x + (chart_w / max(1, len(rows) - 1)) * index
        y = chart_y + chart_h - ((_decimal_to_float(row['amount']) / max_value) * chart_h)
        points.append((x, y, row))

    path = ' '.join([('M' if i == 0 else 'L') + f'{x:.1f} {y:.1f}' for i, (x, y, _) in enumerate(points)])
    area_path = f'{path} L {chart_x + chart_w} {chart_y + chart_h} L {chart_x} {chart_y + chart_h} Z'
    circles = ''.join([
        f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="#23c4ff"><title>{escape(row["label"])}: {escape(_format_zl(row["amount"]))}</title></circle>'
        for x, y, row in points
    ])
    labels = ''.join([
        f'<text x="{x:.1f}" y="315" fill="#8f9abc" font-family="Segoe UI, Arial" font-size="11" text-anchor="middle">{escape(row["label"].split()[0])}</text>'
        for x, _, row in points[::2]
    ])
    body = f'''
        <line x1="{chart_x}" y1="{chart_y + chart_h}" x2="{chart_x + chart_w}" y2="{chart_y + chart_h}" stroke="#343a55" />
        <line x1="{chart_x}" y1="{chart_y}" x2="{chart_x}" y2="{chart_y + chart_h}" stroke="#343a55" />
        <path d="{area_path}" fill="#23c4ff" opacity="0.12" />
        <path d="{path}" fill="none" stroke="#23c4ff" stroke-width="4" stroke-linecap="round" stroke-linejoin="round" />
        {circles}
        <text x="{chart_x}" y="100" fill="#aeb8d9" font-family="Segoe UI, Arial" font-size="13">Max amount: {escape(_format_zl(Decimal(str(max_value))))}</text>
        {labels}
    '''
    return _svg_shell('Daily spending trend', 'Last 14 days. Max uses it to spot busy spending periods.', body)


def build_budget_svg(user):
    data = budget_chart_rows(user)
    percent = data['percent']
    raw_percent = data['raw_percent']
    spent_label = _format_zl(data['spent'])
    limit_label = _format_zl(data['limit']) if data['limit'] else 'not set'
    left_label = _format_zl(data['left'])
    fill_width = int(600 * (percent / 100))
    status = 'Over limit' if raw_percent >= 100 else 'Close to limit' if raw_percent >= 80 else 'Looks okay'
    body = f'''
        <text x="32" y="128" fill="#f4f6ff" font-family="Segoe UI, Arial" font-size="42" font-weight="800">{raw_percent}%</text>
        <text x="32" y="158" fill="#aeb8d9" font-family="Segoe UI, Arial" font-size="15">{escape(status)}</text>
        <rect x="32" y="190" width="600" height="34" rx="17" fill="#242a42" />
        <rect x="32" y="190" width="{max(8, fill_width)}" height="34" rx="17" fill="url(#pbGrad)" />
        <text x="32" y="266" fill="#f4f6ff" font-family="Segoe UI, Arial" font-size="17" font-weight="700">Spent: {escape(spent_label)}</text>
        <text x="262" y="266" fill="#f4f6ff" font-family="Segoe UI, Arial" font-size="17" font-weight="700">Budget: {escape(limit_label)}</text>
        <text x="502" y="266" fill="#f4f6ff" font-family="Segoe UI, Arial" font-size="17" font-weight="700">Left: {escape(left_label)}</text>
    '''
    return _svg_shell('Budget usage', 'Current month. Max compares spending with your monthly limit.', body)


def build_chart_svg(user, chart_key):
    if chart_key == 'daily':
        return build_daily_svg(user)
    if chart_key == 'budget':
        return build_budget_svg(user)
    return build_category_svg(user)


def charts_context(user):
    charts = [
        {
            'key': 'category',
            'title': 'Spending by category',
            'description': 'A quick look at where the money went this month.',
            'svg': build_category_svg(user),
            'comment': max_chart_comment(user, 'category'),
        },
        {
            'key': 'daily',
            'title': 'Daily spending trend',
            'description': 'Shows if spending is spread out or stacked in a few days.',
            'svg': build_daily_svg(user),
            'comment': max_chart_comment(user, 'daily'),
        },
        {
            'key': 'budget',
            'title': 'Budget usage',
            'description': 'Compares this month’s spending with the monthly budget.',
            'svg': build_budget_svg(user),
            'comment': max_chart_comment(user, 'budget'),
        },
    ]
    return {'charts': charts}


def chart_filename(chart_key, extension):
    names = {
        'category': 'max-spending-by-category',
        'daily': 'max-daily-spending-trend',
        'budget': 'max-budget-usage',
    }
    return f'{names.get(chart_key, "max-chart")}.{extension}'


def csv_for_chart(user, chart_key):
    output = StringIO()
    writer = csv.writer(output)
    if chart_key == 'daily':
        writer.writerow(['date', 'amount_zl'])
        for row in daily_chart_rows(user):
            writer.writerow([row['date'].isoformat(), _money(row['amount'])])
    elif chart_key == 'budget':
        data = budget_chart_rows(user)
        writer.writerow(['spent_zl', 'budget_zl', 'left_zl', 'budget_used_percent'])
        writer.writerow([_money(data['spent']), _money(data['limit']), _money(data['left']), data['raw_percent']])
    else:
        writer.writerow(['category', 'amount_zl', 'share_percent'])
        for row in category_chart_rows(user):
            writer.writerow([row['category'], _money(row['amount']), row['share']])
    return output.getvalue()
