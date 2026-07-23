import traceback
import json
import logging
from django.conf import settings
import psycopg2

logger = logging.getLogger(__name__)

def get_isolated_db_connection():
    """
    Open a direct, isolated connection to PostgreSQL to bypass Django's thread-local transaction blocks.
    This guarantees that logs are committed even if the main transaction is rolled back.
    """
    db_config = settings.DATABASES['default']
    conn = psycopg2.connect(
        dbname=db_config['NAME'],
        user=db_config['USER'],
        password=db_config['PASSWORD'],
        host=db_config['HOST'],
        port=db_config['PORT']
    )
    conn.autocommit = True
    return conn

def log_normal_sync(module, action, actor_id=None, actor_email=None, request_path="", ip_address=None, summary=""):
    """
    Direct insert into classlens_normal_log on an isolated autocommit connection.
    """
    conn = None
    try:
        conn = get_isolated_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO classlens_normal_log 
                (timestamp, module, action, actor_id, actor_email, request_path, ip_address, summary)
                VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s, %s)
                """,
                [module, action, actor_id, actor_email, request_path, ip_address, summary]
            )
    except Exception as e:
        logger.error(f"Failed to log to classlens_normal_log synchronously: {e}")
    finally:
        if conn:
            conn.close()

def log_error_sync(module, error_type, error_message, traceback_str, request_payload=None, actor_id=None):
    """
    Direct insert into classlens_error_log on an isolated autocommit connection.
    """
    conn = None
    try:
        conn = get_isolated_db_connection()
        with conn.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO classlens_error_log
                (timestamp, module, error_type, error_message, traceback, request_payload, actor_id)
                VALUES (CURRENT_TIMESTAMP, %s, %s, %s, %s, %s, %s)
                """,
                [module, error_type, error_message, traceback_str, json.dumps(request_payload) if request_payload else None, actor_id]
            )
    except Exception as e:
        logger.error(f"Failed to log to classlens_error_log synchronously: {e}")
    finally:
        if conn:
            conn.close()

def log_normal(module, action, actor_id=None, actor_email=None, request_path="", ip_address=None, summary=""):
    """
    Primary log interface. Dispatches to Celery, falls back to isolated sync execution if Celery is down.
    """
    try:
        from Home.tasks import log_normal_task
        log_normal_task.delay(module, action, actor_id, actor_email, request_path, ip_address, summary)
    except Exception as e:
        logger.warning(f"Celery dispatch failed for log_normal; falling back to sync database write. Error: {e}")
        log_normal_sync(module, action, actor_id, actor_email, request_path, ip_address, summary)

def log_error(module, error_type, error_message, traceback_str, request_payload=None, actor_id=None):
    """
    Primary error log interface. Dispatches to Celery, falls back to isolated sync execution if Celery is down.
    """
    try:
        from Home.tasks import log_error_task
        log_error_task.delay(module, error_type, error_message, traceback_str, request_payload, actor_id)
    except Exception as e:
        logger.warning(f"Celery dispatch failed for log_error; falling back to sync database write. Error: {e}")
        log_error_sync(module, error_type, error_message, traceback_str, request_payload, actor_id)


import threading

_request_local = threading.local()

def set_current_request(request):
    _request_local.current_request = request

def get_current_request():
    return getattr(_request_local, 'current_request', None)

def clear_current_request():
    if hasattr(_request_local, 'current_request'):
        del _request_local.current_request

