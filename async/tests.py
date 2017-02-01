from django.test import TestCase, override_settings
from django.db import models

from async.models import AsyncJob
from async.exceptions import HandlerException


class MyAsyncJob(AsyncJob):
    my_field = models.CharField(max_length=128, null=True)


class AnotherAsyncJob(AsyncJob):
    my_field = models.CharField(max_length=128, null=True)


@MyAsyncJob.handler
def my_async_job_handler(task, job):
    if job.pk == 666:
        raise Exception("Number of the beast!")
    job.my_field = 'Test value'
    job.save()
        

class AsyncJobTestCase(TestCase):

    @override_settings(CELERY_ALWAYS_EAGER=False)
    def test_pending_status(self):
        job = MyAsyncJob.objects.create()
        self.assertEquals(job.status, job.STATUS.NEW)
        job.enqueue()
        job.refresh_from_db()
        self.assertEquals(job.status, job.STATUS.PENDING)
        self.assertTrue(job.is_busy)

    def test_task_success(self):
        job = MyAsyncJob.objects.create()
        self.assertEquals(job.status, job.STATUS.NEW)
        job.enqueue()
        job.refresh_from_db()
        self.assertEquals(job.status, job.STATUS.SUCCESS)

    def test_task_wait_time(self):
        job = MyAsyncJob.objects.create()
        self.assertIsNone(job.wait_time())
        job.enqueue()
        job.refresh_from_db()
        self.assertIsNotNone(job.wait_time())

    def test_task_running_time(self):
        job = MyAsyncJob.objects.create()
        self.assertIsNone(job.running_time())
        job.enqueue()
        job.refresh_from_db()
        self.assertIsNotNone(job.running_time())

    def test_task_failure(self):
        job = MyAsyncJob.objects.create(id=666)
        self.assertEquals(job.status, job.STATUS.NEW)
        job.enqueue()
        job.refresh_from_db()
        self.assertEquals(job.status, job.STATUS.FAILURE)
        self.assertEquals(job.error_message, 'Exception: Number of the beast!\n')

    def test_multiple_handlers(self):

        with self.assertRaises(HandlerException):
            @MyAsyncJob.handler
            def another_handler(task, job):
                job.my_field = 'Test value'
                job.save()

    def test_missing_handler(self):
        job = AnotherAsyncJob.objects.create()
        with self.assertRaises(HandlerException):
            job.enqueue()
