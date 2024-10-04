# In authapp/apps.py
from django.apps import AppConfig

class AuthappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'authapp'

    def ready(self):
        import authapp.signals  # Import signals to register them
