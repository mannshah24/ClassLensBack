import os
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ClassLens_DB.settings')
try:
    django.setup()
except Exception as e:
    print('Django setup error:', e)
    sys.exit(1)

from django.db import connection

with connection.cursor() as cur:
    cur.execute("SELECT id, app, name FROM django_migrations WHERE app='Home'")
    rows = cur.fetchall()
    print('Home migrations in django_migrations:', rows)
    if rows:
        cur.execute("DELETE FROM django_migrations WHERE app='Home'")
        print('Deleted Home migration entries from django_migrations')
    else:
        print('No Home migration entries found')
