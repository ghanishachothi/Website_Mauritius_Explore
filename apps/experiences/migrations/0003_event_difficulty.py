from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0002_category_icon'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='difficulty',
            field=models.CharField(
                blank=True,
                choices=[
                    ('easy', 'Easy'),
                    ('moderate', 'Moderate'),
                    ('challenging', 'Challenging'),
                ],
                max_length=12,
            ),
        ),
    ]
