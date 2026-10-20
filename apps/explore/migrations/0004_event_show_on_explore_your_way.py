from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explore', '0003_guide_about'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='show_on_explore_your_way',
            field=models.BooleanField(default=False, help_text='Show this event on the Explore Your Way page'),
        ),
    ]
