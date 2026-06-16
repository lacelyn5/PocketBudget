from django.db import migrations


DEFAULT_CATEGORIES = [
    ('Food', 'food', '🍔', '#ff7f6b'),
    ('Transport', 'transport', '🚌', '#23c4ff'),
    ('Rent', 'rent', '🏠', '#7c5cff'),
    ('Entertainment', 'entertainment', '🎮', '#ffd166'),
    ('Education', 'education', '📚', '#4cc38a'),
    ('Shopping', 'shopping', '🛍️', '#f783ac'),
    ('Health', 'health', '💊', '#69db7c'),
    ('Bills', 'bills', '🧾', '#4dabf7'),
    ('Other', 'other', '💸', '#aeb8d9'),
]


def create_default_categories(apps, schema_editor):
    Category = apps.get_model('budget', 'Category')
    for name, slug, icon, color in DEFAULT_CATEGORIES:
        Category.objects.update_or_create(
            slug=slug,
            defaults={
                'name': name,
                'icon': icon,
                'color': color,
                'is_default': True,
            },
        )


def remove_default_categories(apps, schema_editor):
    Category = apps.get_model('budget', 'Category')
    Category.objects.filter(slug__in=[item[1] for item in DEFAULT_CATEGORIES]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('budget', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_default_categories, remove_default_categories),
    ]
