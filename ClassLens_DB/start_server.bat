@echo off
cd C:\Users\Admin\Desktop\ClassLens\ClassLens_DB
call C:\Users\Admin\Desktop\ClassLens\venv\Scripts\activate.bat
waitress-serve --threads=32 --host=127.0.0.1 --port=8000 ClassLens_DB.wsgi:application
pause