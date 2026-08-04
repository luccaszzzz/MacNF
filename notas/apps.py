from django.apps import AppConfig


class NotasConfig(AppConfig):
    name = 'notas'

    def ready(self):
        import notas.signals
