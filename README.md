# What is this? #
This is a portable Django app that hopefully makes it easier to run asynchronous background tasks with Celery
and track their state throughout the process. We've tried to abstract away as much of the implementation 
details as possible while still keeping things flexible.

## Getting Started ##
There are some things you'll need to do to set up your project.

### Install Celery ###
The only outside dependency is Celery itself. Make sure it's installed.

```
pip install celery
```

### Add configuration to settings.py ###
Add settings to tell celery where it's broker and backend live. Also tell it
how it should serialize data and the timezone to use.

```
BROKER_URL = 'amqp://root:password@rabbitmq//'
CELERY_APP_NAME = 'my_project_name'
CELERY_RESULT_BACKEND = 'cache+memcached://memcached/'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
```

### Create a celery app instance ###
Your Django project and the celery worker need access to a celery app object. To ensure that
it is created when your project starts put it in your main project module's `__init__.py` file.

```
from async.celery import get_celery_app
celery_app = get_celery_app(__name__)
```

## Creating AsyncJob Models ##
Now that you have everything set up you're ready to create models that represent asynchronous jobs. All
you have to do is sub class the abstract `async.models.AsyncJob` class and add any additional fields
required for your specific job.

```
class MyJob(AsyncJob):
    default_queue = 'my_queue'  # This is optional
    my_field = models.IntegerField(blank=True, null=True)
    result = models.CharField(null=True, max_length=128)
```

## Creating the job handler ##
Now you need to define the function that will be called by celery to process your job. This should be
a function that accepts 2 arguments: `task` and `job`. The first argument, `task`, is the celery task object. You can use this object to update the job's progress as it runs. The second argument, `job`, is the model
that represents the current job. Everything the handler needs to process the job should be available in the
`job` object. Also, you can use the The magic is in the 2 decorators that turn the function into both a celery task AND the handler for the given AsyncJob model.

IMPORTANT NOTE: In order for handlers to be automatically discovered by the celery worker you MUST put them
in a module called `handlers` in your apps. This means if you have an app called `foo` your handlers must 
be in `foo.handlers.my_handler`.

```
@MyJob.handler  # This defines the function as a task for the MyJob model.
def process_my_job(task, job):
    job.result = do_some_long_running_task(job.my_field)
    job.save()
```

## Putting a Job on the Queue ##
In order for an AsyncJob to run it has to be created and placed on celery's message queue.

```
job = MyJob.objects.create(my_field=1234)
job.enqueue()
```

## The AsyncJob lifecycle ##
AsyncJobs go through a series of states that roughly mirror the state of the underlying celery task. The abstract AsyncJob class handles transitioning the Job from one state to the next.

#### New ####
The Job has been created but no celery task has been placed on the queue.

#### PENDING ####
A celery task has been placed on the queue but has not yet been picked up by a worker.

#### STARTED ####
The task has been picked up by a worker and is currently being worked on.

#### SUCCESS ####
The task has completed successfully (no exceptions)

#### FAILURE ####
The task encountered an exception during execution. AsyncJob.error_message should contain the value of the
exception.

#### REVOKED ####
The task was canceled by a user.

## Running the celery worker ##
AsyncJobs need a celery worker process to process jobs. You can start a worker from the command line like this:

```
celery -A async worker -l info --queue=my_queue
```

### Queues ###
You can split up tasks into as many named queues as you'd like. When you start a worker you can specify the queue(s) that the worker should listen to. This makes distributing the work across multiple worker clusters and tailoring the workers to the needs of different queues much easier.

### Concurency ###
By default multiprocessing is used to perform concurrent execution of tasks, and defaults to the number of CPUs available on the machine. You can control the concurrency when you start the worker with the `--concurrency` argument.

```
celery -A async worker -l info --queue=my_queue --concurrency=10
```