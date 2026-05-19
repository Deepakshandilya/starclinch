from .celery import app as celery_app

# This makes sure Celery loads when Django starts.
__all__ = ('celery_app',)