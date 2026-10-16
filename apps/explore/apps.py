from django.apps import AppConfig


class ExploreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.explore'
    verbose_name = 'Mauritius Explore'

    def ready(self):
        from . import signals  # noqa: F401  (creates a Profile for every new user)
