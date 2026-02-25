# 🧠 ClassLens Backend

ClassLens Backend is the core AI and data layer of the ClassLens ecosystem.  
It powers:

- Face detection & enhancement
- Embedding generation & vector similarity search
- Attendance creation & analytics
- Secure authentication and OTP flows
- APIs for the Flutter app and Next.js admin dashboard

This repository contains the Django project, Celery configuration, and all REST APIs.

---

## 🗂 Project Structure

```bash
ClassLens/
├── requirements.txt
└── ClassLens_DB/
    ├── manage.py
    ├── ClassLens_DB/          # Django project
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── celery.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    ├── DatabaseAdminApp/      # Admin-related APIs (bulk upload, entities)
    │   ├── models.py
    │   ├── serializers.py
    │   ├── views.py
    │   ├── urls.py
    │   └── ...
    └── Home/                  # Core attendance + face recognition APIs
        ├── authentication.py
        ├── models.py
        ├── serializers.py
        ├── tasks.py
        ├── views.py
        ├── urls.py
        └── migrations/
```

---

## 🛠 Tech Stack

- **Backend Framework**: Django, Django REST Framework
- **Task Queue**: Celery
- **Message Broker / Cache**: Redis
- **Database**: PostgreSQL (with `pgvector` extension)
- **Face Pipeline**: DeepFace, RetinaFace, GFPGAN
- **Auth & OTP**: JWT authentication + Email OTP verification
- **Environment**: `.env`-driven configuration

---

## 🚀 Getting Started

### ⭐ Prerequisites

- Python 3.10+
- PostgreSQL 13+ (local or managed, with pgvector installed)
- Redis server
- Virtual environment (recommended)

---

### 📥 Installation

```bash
# clone the repo
git clone https://github.com/ClassLens-A/ClassLens.git
cd ClassLens

# create & activate venv
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

Move into Django project root:

```bash
cd ClassLens_DB
```

---

## 🔐 Environment Variables

Create a `.env` inside `ClassLens_DB/`

```env
# PostgreSQL
DB_NAME=classlens_db
DB_USER=your_user
DB_PASSWORD=your_password
DB_HOST=your_host
DB_PORT=5432

# Redis
REDIS_URL=redis://localhost:6379

# Email Configuration (SMTP)
EMAIL_HOST=smtp.gmail.com  # Use smtp-mail.outlook.com for Outlook
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password  # Use App Password for Gmail

# Optional: model paths
GFPGAN_MODEL_PATH=/path/to/GFPGANv1.4.pth
```

---

## 🗄️ Database Setup

```sql
CREATE DATABASE classlens_db;
-- Ensure pgvector extension is enabled (on the correct DB)
CREATE EXTENSION IF NOT EXISTS vector;
```

If you are using **Azure PostgreSQL**, create DB + enable vector using Azure’s tools / query console.

---

## 🔧 Apply Migrations & Create Superuser

```bash
python manage.py migrate
python manage.py createsuperuser
```

---

## ▶️ Run Server

```bash
python manage.py runserver
```

Backend now runs at:
👉 http://127.0.0.1:8000/

You can now hit the API from:

- Flutter App (ClassLens_App)
- Next.js admin (ClassLens-Frontend)

---

## ⚡ Celery & Redis Setup

Start Redis locally or via Docker:

```bash
redis-server # local OR
docker run -d --name classlens-redis -p 6379:6379 redis
```

Start Celery worker:

```bash
celery -A ClassLens_DB.celery worker -l info -P gevent
```

---

## 🧬 GFPGAN Model Usage

This repo uses **GFPGANv1.4** for recovering/enhancing low-quality faces before embedding extraction.

Because the GFPGAN model file is large, it is not included in this repository.

### To Configure GFPGAN:

1. Download GFPGANv1.4.pth from official repo
2. Place it locally (e.g., `models/GFPGANv1.4.pth`)
3. Set `.env` key:

```
GFPGAN_MODEL_PATH=/absolute/path/GFPGANv1.4.pth
```

Your pipeline can then load it dynamically.

---

## 🔄 Backend Flow

1. Teacher uploads a classroom photo from the mobile app.
2. Backend creates a class session and enqueues a Celery task.
3. Celery Worker:
   - detects all faces
   - optionally enhances crops via GFPGAN
   - generates embeddings (e.g. Facenet512)
   - runs vector similarity search (pgvector)
4. Attendance records are created for matched students.
5. Annotated image + results are sent back to teacher for verification.

---

## 📚 API Overview (Selected Endpoints)

### Onboarding & Authentication

| Method | Endpoint              | Description                                     |
| ------ | --------------------- | ----------------------------------------------- |
| GET    | `/getDepartments/`    | Fetch list of departments for registration form |
| POST   | `/registerNewStudent` | Register a new student with basic details       |
| POST   | `/registerNewTeacher` | Register a new teacher                          |
| POST   | `/sendOtp`            | Send OTP to email via SMTP                      |
| POST   | `/verifyOtp`          | Verify OTP during registration / login          |
| POST   | `/setPassword`        | Set or reset account password                   |
| GET    | `/verifyEmail`        | Verify whether an email is already registered   |
| GET    | `/verifyPRN`          | Verify whether a PRN exists / is valid          |
| GET    | `/validateStudent`    | Validate student credentials / status           |
| GET    | `/validateTeacher`    | Validate teacher credentials / status           |

> **Note:** Most registration / OTP routes are designed to be hit from the Flutter app.

---

### Subjects & Metadata

| Method | Endpoint                            | Description                                |
| ------ | ----------------------------------- | ------------------------------------------ |
| GET    | `/getSubjectDetails`                | Get subject details for a specific student |
| GET    | `/getSubjects/`                     | Get subjects assigned to a teacher         |
| GET    | `/teacherProfile/<int:teacher_id>/` | Fetch teacher profile + summary data       |

---

### Attendance Workflow

| Method | Endpoint                           | Description                                                      |
| ------ | ---------------------------------- | ---------------------------------------------------------------- |
| POST   | `/markAttendance`                  | Upload classroom photo and trigger attendance processing         |
| GET    | `/attendanceStatus/<str:task_id>/` | Poll the status of an attendance processing Celery task          |
| GET    | `/students/attendance/`            | Get attendance details for a given student                       |
| GET    | `/getPresentAbsentList/`           | Fetch present/absent list for a particular session               |
| POST   | `/changeAttendance/`               | Manually change attendance (e.g., correct misclassified student) |

> These endpoints together power the **“upload → process → verify → finalize”** attendance flow from the teacher app and admin dashboard.

---

## 🤝 Contributing

We appreciate contributions via PRs and issues:

1. Fork the repo
2. Create a feature branch
3. Commit changes
4. Open PR with explanation

---
