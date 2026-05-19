# StarClinch — Recipe Sharing Platform API

A backend REST API for a social recipe sharing platform built with Django REST Framework. Supports two user roles — **Sellers** who publish recipes, and **Customers** who browse and rate them. Includes asynchronous image processing via Celery, scheduled email notifications, and weekly data exports to Amazon S3.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Framework | Django 5.2 + Django REST Framework |
| Authentication | JWT (djangorestframework-simplejwt) |
| Async Tasks | Celery 5.6 |
| Message Broker | Redis 7 |
| Task Scheduler | Celery Beat + django-celery-beat |
| Image Processing | Pillow |
| Cloud Storage | Amazon S3 (boto3) |
| Containerization | Docker + Docker Compose |

---

## Features

- **Role-based access control** — Sellers create and manage recipes; Customers view and rate them
- **JWT authentication** — secure token-based auth with access/refresh token flow
- **Rate limiting** — throttling applied globally (100/day anonymous, 1000/day authenticated) and 5/minute for login
- **Async image compression** — recipe images are compressed in the background via Celery without blocking the API response
- **Daily email notifications** — scheduled at 6 AM IST, Monday to Friday only
- **Weekly S3 export** — all user data exported as CSV to Amazon S3 every Monday
- **Optimized queries** — `select_related` and `prefetch_related` used throughout to prevent N+1 queries
- **Dockerized** — entire stack runs with a single command

---

## Project Structure

```
starclinch/
│
├── core/                   # Project config
│   ├── settings.py
│   ├── urls.py
│   └── celery.py           # Celery app initialization
│
├── users/                  # Auth + user management
│   ├── models.py           # CustomUser with role field
│   ├── serializers.py
│   ├── views.py            # Register, Profile
│   ├── urls.py
│   └── permissions.py      # IsSeller, IsCustomer permission classes
│
├── recipes/                # Core domain
│   ├── models.py           # Recipe, Rating models
│   ├── serializers.py
│   ├── views.py
│   ├── urls.py
│   └── tasks.py            # Celery tasks: image compression, email, S3 export
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Getting Started

### Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running

### 1. Clone the repository

```bash
git clone https://github.com/Deepakshandilya/starclinch.git
cd starclinch
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Open `.env` and fill in the values:

```env
SECRET_KEY=your-django-secret-key
DEBUG=True

# Email (for daily notifications)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS S3 (for weekly CSV export)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_S3_REGION_NAME=ap-south-1
AWS_STORAGE_BUCKET_NAME=your-bucket-name
```

### 3. Start the entire stack

```bash
docker compose up --build
```

### 4. Create an admin superuser (optional — for /admin panel)

```bash
docker compose exec django python manage.py createsuperuser
```


This starts 4 containers:

| Container | Role |
|---|---|
| `redis` | Message broker |
| `django` | API server on port 8000 |
| `celery` | Async task worker |
| `celery-beat` | Task scheduler |

The API is available at `http://localhost:8000`

---
## Docker Commands

```bash
# Start the entire stack
docker compose up --build

# Stop all containers
docker compose down

# Start all containers
docker compose up
```

## Manually Triggering Celery Tasks

Useful for testing without waiting for the schedule.

```bash
# Open Django shell inside the container
docker compose exec django python manage.py shell

# Then run:
from recipes.tasks import send_daily_email, export_users_to_s3

# Trigger daily email
send_daily_email.delay()

# Trigger S3 export
export_users_to_s3.delay()
```

You can verify the email arrived in your inbox and check your S3 bucket for the
timestamped CSV file under the `exports/` prefix.


## API Reference

### Authentication

| Method | Endpoint | Access | Description |
|---|---|---|---|
| POST | `/api/auth/register/` | Public | Register as customer or seller |
| POST | `/api/auth/login/` | Public | Get access + refresh tokens |
| POST | `/api/auth/token/refresh/` | Public | Refresh access token |
| GET | `/api/auth/profile/` | Authenticated | Get current user profile |

### Recipes

| Method | Endpoint | Access | Description |
|---|---|---|---|
| GET | `/api/recipes/` | Public | List all recipes with ratings |
| POST | `/api/recipes/` | Seller only | Create a recipe (triggers image compression) |
| GET | `/api/recipes/{id}/` | Public | Get single recipe |
| PATCH | `/api/recipes/{id}/` | Seller (owner) | Update own recipe |
| DELETE | `/api/recipes/{id}/` | Seller (owner) | Delete own recipe |
| POST | `/api/recipes/{id}/rate/` | Customer only | Rate a recipe (1–5, once per recipe) |

---

## Example Requests

### Register a Seller

```json
POST /api/auth/register/
{
  "username": "chef_deepak",
  "email": "deepak@example.com",
  "password": "securepass123",
  "role": "seller"
}
```

### Create a Recipe

```
POST /api/recipes/
Authorization: Bearer <access_token>
Content-Type: multipart/form-data

name: Butter Chicken
description: Classic North Indian curry
image: <file>
```

### Rate a Recipe

```json
POST /api/recipes/1/rate/
Authorization: Bearer <access_token>
{
  "score": 5,
  "review": "Absolutely delicious!"
}
```

---

## Async Tasks

### Image Compression
When a seller uploads a recipe image, the API returns `201` immediately. Celery picks up the compression task in the background using Pillow and updates the stored image — the request cycle is never blocked.

### Daily Email (Mon–Fri, 6 AM IST)
Celery Beat triggers `send_daily_email` on weekdays only. Configured via crontab `hour=6, minute=0, day_of_week='1-5'`.

### Weekly S3 Export (Every Monday)
All user records are streamed from the database in chunks of 500 using `.iterator(chunk_size=500)` — keeping memory flat regardless of user count — then uploaded as a timestamped CSV to S3.

---

## Design Decisions

**Two serializers per resource** — `RecipeSerializer` (read) and `RecipeWriteSerializer` (write) are kept separate to avoid validation conflicts between computed fields and writable fields.

**`.iterator()` for CSV export** — avoids loading the entire users table into memory at once. Scales to millions of rows.

**`select_related` + `prefetch_related`** — all list and detail views use these to eliminate N+1 queries on seller and ratings relationships.

**Healthcheck on Redis** — Django and Celery containers wait for Redis to confirm readiness before starting, preventing connection errors on startup.

---

## Running Without Docker (Local)

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt

# Requires Redis running locally on port 6379
python manage.py migrate
python manage.py runserver

# In separate terminals:
celery -A core worker --loglevel=info
celery -A core beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```
