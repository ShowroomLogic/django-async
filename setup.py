import os
from setuptools import find_packages, setup

__title__ = 'Django Async'
__version__ = '0.1'
__author__ = 'Chris Brantley'
__author_email__ = 'chris@showroomlogic.com'

# Version synonym
VERSION = __version__

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name='django-async',
    version=__version__,
    description='Asynchronous background tasks in Django with celery',
    url='https://github.com/ShowroomLogic/django-async',
    author=__author__,
    author_email=__author_email__,
    packages=find_packages(),
    install_requires=[
        'celery==3.1.23',
        'iron_celery==0.4.5'
    ],
    zip_safe=False
)
