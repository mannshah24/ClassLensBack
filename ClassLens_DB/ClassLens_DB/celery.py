import os
from celery import Celery
import environ #type:ignore
from pathlib import Path #type:ignore

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
rabbitmq_url = env('RABBITMQ_URL')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClassLens_DB.settings')

app = Celery('ClassLens_DB')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.update(
    broker_url=rabbitmq_url,
    result_backend='rpc://',
    broker_connection_retry_on_startup=True,
)