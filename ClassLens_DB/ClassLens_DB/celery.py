import os
from celery import Celery
import environ #type:ignore
from pathlib import Path #type:ignore
from urllib.parse import quote_plus

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env()
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))
rabbitmq_url = env('RABBITMQ_URL')

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClassLens_DB.settings')

# Build database result backend URL with proper password encoding
db_user = env("DB_USER")
db_password = quote_plus(env("DB_PASSWORD"))
db_host = env("DB_HOST")
db_port = env("DB_PORT")
db_name = env("DB_NAME")
db_result_backend = f'db+postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}'

app = Celery('ClassLens_DB')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
app.conf.update(
    broker_url=rabbitmq_url,
    result_backend=db_result_backend,
    broker_connection_retry_on_startup=True,
)