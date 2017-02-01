from django.apps import AppConfig
from django.conf import settings

from .celery import app as celery_app

__title__ = 'Django Async'
__version__ = '0.1'
__author__ = 'Chris Brantley'
__author_email__ = 'chris@showroomlogic.com'

# Version synonym
VERSION = __version__


class AsyncAppConfig(AppConfig):

    name = 'async'

    def ready(self):
        # ensure that all handlers are auto-loaded
        celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, 'handlers', force=True)
        celery_app.autodiscover_tasks(lambda: settings.INSTALLED_APPS, 'tasks', force=True)

default_app_config = 'async.AsyncAppConfig'
