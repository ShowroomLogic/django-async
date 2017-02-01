import sys
import traceback
import uuid

from django.db import models
from django.utils import timezone

from .celery import app as celery_app
from .exceptions import HandlerException


class AsyncJob(models.Model):

    default_queue = None

    class STATUS:
        NEW = 'new'
        PENDING = 'pending'
        STARTED = 'started'
        SUCCESS = 'success'
        FAILURE = 'failure'
        REVOKED = 'revoked'

    STATUS_CHOICES = (
        (STATUS.NEW, STATUS.NEW),
        (STATUS.PENDING, STATUS.PENDING),
        (STATUS.STARTED, STATUS.STARTED),
        (STATUS.SUCCESS, STATUS.SUCCESS),
        (STATUS.FAILURE, STATUS.FAILURE),
        (STATUS.REVOKED, STATUS.REVOKED)
    )

    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS.NEW)
    celery_task_id = models.CharField(max_length=64, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    error_message = models.TextField(null=True)

    @property
    def is_busy(self):
        return self.status in (AsyncJob.STATUS.PENDING, AsyncJob.STATUS.STARTED)

    def wait_time(self):
        """
        Returns the time (in seconds) that the job waited in the queue.
        """
        if self.started_at and self.created_at:
            return (self.started_at - self.created_at).total_seconds()
        else:
            return None

    def running_time(self):
        """
        Returns the time (in seconds) that the job was actively worked on.
        """
        if self.ended_at and self.started_at:
            return (self.ended_at - self.started_at).total_seconds()
        else:
            return None

    @classmethod
    def handler(cls, func):
        """
        Decorator for celery tasks to encapsulate job tracking
        :param cls: current class
        :param func: function being wrapped
        :return:
        """

        def wrapper(*args, **kwargs):

            try:
                task = args[0]
                job = kwargs.get('job') or cls.objects.get(pk=kwargs['job_id'])
                job.status = AsyncJob.STATUS.STARTED
                job.started_at = timezone.now()
                job.save(update_fields=['status', 'started_at'])

                func(task, job=job)
                job.status = AsyncJob.STATUS.SUCCESS
                job.ended_at = timezone.now()
                job.save(update_fields=['status', 'ended_at'])
            except:
                exc_type, exc_value, exc_traceback = sys.exc_info()
                # We need to get the job again from the DB because
                # in some cases we don't have a reference to it anymore
                job = kwargs.get('job') or cls.objects.get(pk=kwargs['job_id'])
                job.status = AsyncJob.STATUS.FAILURE
                job.error_message = "".join(traceback.format_exception_only(exc_type, exc_value))
                job.ended_at = timezone.now()
                job.save(update_fields=['status', 'error_message', 'ended_at'])
                raise

        # save the handler function so we can access it later
        if hasattr(cls, 'handler_function'):
            raise HandlerException("Job handler already registered! Cannot register more than one handler for {}.".format(cls.__name__))
        else:
            task_name = "{}.{}".format(cls.__name__, 'handler')
            cls.handler_function = celery_app.task(wrapper, bind=True, name=task_name)

        return cls.handler_function

    def enqueue(self, *args, **kwargs):
        if not hasattr(self, 'handler_function'):
            raise HandlerException("No handler registered for {}".format(self.__class__.__name__))
        self.celery_task_id = str(uuid.uuid4())
        self.status = AsyncJob.STATUS.PENDING
        self.save(update_fields=['celery_task_id', 'status'])
        kwargs['job_id'] = self.pk
        queue = kwargs.pop('queue', self.default_queue)
        self.handler_function.apply_async(args=args, kwargs=kwargs, task_id=self.celery_task_id, queue=queue)

    class Meta:
        abstract = True
        get_latest_by = 'created_at'
