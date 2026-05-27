from django.apps import AppConfig

class EhrConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ehr'

    def ready(self):
        # TEMPORARILY DISABLED FOR REGISTRATION/OCR DEBUGGING
        # import ehr.signals # noqa
        pass
