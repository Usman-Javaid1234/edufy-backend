# Edufy Backend — Setup Guide

## Prerequisites
- Python 3.11+
- PostgreSQL running locally

## 1. Create the database
```sql
-- In psql:
CREATE DATABASE edufy_db;
```

## 2. Clone and set up the environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

pip install -r requirements.txt
```

## 3. Configure environment variables
```bash
cp .env.example .env
# Edit .env and set your DB_PASSWORD
```

## 4. Run migrations
```bash
python manage.py migrate
```

## 5. Seed test users
```bash
python manage.py seed_users
```
This creates:
| Email                    | Password   | Role    |
|--------------------------|------------|---------|
| student@nust.edu.pk      | Test@1234  | Student |
| faculty@nust.edu.pk      | Test@1234  | Faculty |
| admin@nust.edu.pk        | Test@1234  | Admin   |
| maria@nust.edu.pk        | Test@1234  | Student |
| bilal@nust.edu.pk        | Test@1234  | Student |
| zara@nust.edu.pk (inactive) | Test@1234 | Student |

## 6. Run the server
```bash
python manage.py runserver
```
API runs at: http://localhost:8000

## 7. Django Admin
Visit: http://localhost:8000/admin/
Login with: admin@nust.edu.pk / Test@1234

## API Endpoints (Step 1)
| Method | URL                    | Description           |
|--------|------------------------|-----------------------|
| POST   | /api/auth/login/       | Login, returns JWT    |
| POST   | /api/auth/refresh/     | Refresh access token  |
| GET    | /api/auth/me/          | Current user info     |
| GET    | /api/auth/users/       | List all users (admin)|
| POST   | /api/auth/users/       | Create user (admin)   |
| PATCH  | /api/auth/users/{id}/  | Update user (admin)   |
| DELETE | /api/auth/users/{id}/  | Deactivate user       |
