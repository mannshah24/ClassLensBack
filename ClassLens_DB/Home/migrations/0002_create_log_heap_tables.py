from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('Home', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE TABLE classlens_normal_log (
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                module VARCHAR(255) NOT NULL,
                action VARCHAR(255) NOT NULL,
                actor_id BIGINT,
                actor_email VARCHAR(255),
                request_path TEXT,
                ip_address VARCHAR(45),
                summary TEXT
            );
            """,
            reverse_sql="DROP TABLE classlens_normal_log;"
        ),
        migrations.RunSQL(
            sql="""
            CREATE TABLE classlens_error_log (
                timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                module VARCHAR(255) NOT NULL,
                error_type VARCHAR(255) NOT NULL,
                error_message TEXT,
                traceback TEXT,
                request_payload JSON,
                actor_id BIGINT
            );
            """,
            reverse_sql="DROP TABLE classlens_error_log;"
        ),
    ]
