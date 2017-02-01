from celery import Celery
import iron_celery

from django.conf import settings

app = Celery(settings.CELERY_APP_NAME)
app.config_from_object('django.conf:settings')
