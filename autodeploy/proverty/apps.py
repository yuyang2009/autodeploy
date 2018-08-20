from django.apps import AppConfig


class ProvertyConfig(AppConfig):

    name = 'autodeploy.proverty'
    verbose_name = "Proverty"

    def ready(self):
        try:
            import proverty.signals  # noqa F401
        except ImportError:
            pass
