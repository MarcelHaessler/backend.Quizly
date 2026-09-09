from django.apps import AppConfig


class QuizAppConfig(AppConfig):
    """Quiz storage plus the YouTube-to-quiz generation pipeline."""

    default_auto_field = 'django.db.models.BigAutoField'
    name = 'quiz_app'
