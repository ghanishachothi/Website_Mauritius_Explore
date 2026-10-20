from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('explore', '0004_event_show_on_explore_your_way'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='show_on_explore_board',
            field=models.BooleanField(default=False, help_text='Show this event in Recommended for you on the Explore Board page'),
        ),
    ]
