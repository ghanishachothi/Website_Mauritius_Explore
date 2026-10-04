from django.db import migrations


class CreateModelIfNotExists(migrations.CreateModel):
    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        model = to_state.apps.get_model(app_label, self.name)
        if not self.allow_migrate_model(schema_editor.connection.alias, model):
            return
        if model._meta.db_table in schema_editor.connection.introspection.table_names():
            return
        schema_editor.create_model(model)
