from django.apps import AppConfig  # ✅ YOU NEED THIS IMPORT

class ChatappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatapp'