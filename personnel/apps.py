from django.apps import AppConfig


class PersonnelConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'personnel'

    def ready(self):
        # import signals to register them
        from . import signals  # noqa
