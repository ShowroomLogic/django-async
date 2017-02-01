from django.apps import AppConfig
from django.conf import settings

from .celery import app as celery_app


class AsyncAppConfig(AppConfig):

    name = 'async'

    def ready(self):
        # ensure that all handlers are auto-loaded
        celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, 'handlers', force=True)
        celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, 'tasks', force=True)

default_app_config = 'async.AsyncAppConfig'
