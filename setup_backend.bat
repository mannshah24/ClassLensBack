@echo off
REM ClassLens Backend Setup Script

cd /d "m:\ClassLens\classLenseBackend\ClassLens\ClassLens_DB"

echo.
echo ========================================
echo ClassLens Backend Setup & Migration
echo ========================================
echo.

REM Activate virtual environment
echo [1/5] Activating Python virtual environment...
call .\.venv\Scripts\activate.bat

if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Make migrations
echo.
echo [2/5] Creating database migrations...
python manage.py makemigrations Home
if %ERRORLEVEL% NEQ 0 echo WARNING: makemigrations for Home had issues

python manage.py makemigrations DatabaseAdminApp
if %ERRORLEVEL% NEQ 0 echo WARNING: makemigrations for DatabaseAdminApp had issues

REM Run migrations
echo.
echo [3/5] Running database migrations...
python manage.py migrate
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Migration failed
    echo Please check your database configuration in .env
    pause
    exit /b 1
)

REM Create default admin user
echo.
echo [4/5] Creating default admin user...
python manage.py shell << EOF
from Home.models import AdminUser
import os

username = "admin"
password = "admin@123456"

# Check if admin user already exists
if not AdminUser.objects.filter(username=username).exists():
    admin = AdminUser(username=username, is_active=True)
    admin.set_password(password)
    admin.save()
    print(f"✓ Admin user created: {username}")
    print(f"  Password: {password}")
else:
    print(f"✓ Admin user '{username}' already exists")
EOF

REM Check Django setup
echo.
echo [5/5] Checking Django setup...
python manage.py check
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Django check reported issues
)

echo.
echo ========================================
echo Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Ensure PostgreSQL is running
echo 2. Ensure Redis is running (for Celery results)
echo 3. Optionally start RabbitMQ (if not running, Celery will queue locally)
echo 4. Run: python manage.py runserver
echo 5. Login at http://localhost:8000/api/admin/login/
echo    Username: admin
echo    Password: admin@123456
echo.
pause
