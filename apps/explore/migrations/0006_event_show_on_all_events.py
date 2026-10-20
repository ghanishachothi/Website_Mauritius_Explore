from django.db import migrations, models


def keep_current_all_events(apps, schema_editor):
    # The page used to list events that are not on the calendar. Tick those
    # so the page looks the same right after this change.
    Event = apps.get_model('explore', 'Event')
    Event.objects.filter(show_on_calendar=False).update(show_on_all_events=True)


class Migration(migrations.Migration):

    dependencies = [
        ('explore', '0005_event_show_on_explore_board'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='show_on_all_events',
            field=models.BooleanField(default=False, help_text='Show this event on the All Events & Activities page'),
        ),
        migrations.RunPython(keep_current_all_events, migrations.RunPython.noop),
    ]
