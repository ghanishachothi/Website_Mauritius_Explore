from django.db import migrations


def ensure_review_title(apps, schema_editor):
    review_model = apps.get_model('experiences', 'Review')
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        columns = {
            column.name
            for column in connection.introspection.get_table_description(
                cursor, review_model._meta.db_table
            )
        }
    if 'title' not in columns:
        schema_editor.add_field(review_model, review_model._meta.get_field('title'))


class Migration(migrations.Migration):

    dependencies = [
        ('experiences', '0010_review_updated_at_alter_category_icon_and_more'),
    ]

    operations = [
        migrations.RunPython(ensure_review_title, migrations.RunPython.noop),
    ]
