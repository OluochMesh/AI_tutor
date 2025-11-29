# AI Tutor

AI Tutor is a lightweight Flask backend for an educational tutoring service that uses AI to analyze learner explanations, return actionable feedback, track learning progress, and manage premium subscriptions. The project integrates AI assistance (via Hugging Face inference), M-Pesa payment processing (Daraja), user authentication (JWT), and a simple PostgreSQL / SQLite backed data model.

This README documents getting started, running locally, important environment variables and example API use.

---

## 🚀 Features

- Submit a learner explanation and receive AI-generated feedback and an understanding score
- Personalized study tips and learning recommendations
- Track learning history and progress per user and topic
- User authentication and JWT tokens
- Subscription plans (free, monthly, yearly) with M-Pesa STK Push payment flow and server-side callback handling
- Database models with Flask-Migrate for migrations

---

## 🧭 Quick start (development)

Prerequisites
- Python 3.11+ (runtime.txt lists Python 3.13) — use the version you prefer
- Git

From the repository root, open a PowerShell terminal and run:

```powershell
# enter the backend folder
cd ai_tutor_backend

# create a virtual environment
python -m venv .venv

# activate (PowerShell)
. .\.venv\Scripts\Activate.ps1

# upgrade pip and install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# run the app (dev server)
python app.py

# Alternatively run with gunicorn (production-like):
# gunicorn app:app -b 0.0.0.0:5000
```

If you prefer to use Flask CLI and migrations you can export FLASK_APP to point to the package entry:

```powershell
$env:FLASK_APP = "app:create_app"
$env:FLASK_DEBUG = "1"
flask db upgrade
flask run -h 0.0.0.0 -p 5000
```

---

## 🔧 Environment variables

Create a `.env` file (in `ai_tutor_backend` or export variables) with values appropriate for your environment. The app falls back to SQLite if `DATABASE_URL` is not set.

Required/Important environment variables:

- SECRET_KEY (recommended — used by Flask)
- JWT_SECRET_KEY (defaults to SECRET_KEY)
- DATABASE_URL (optional; SQLite used if not provided)

M-Pesa (Daraja) configuration (if running payments):
- MPESA_ENVIRONMENT (sandbox or production)
- MPESA_CONSUMER_KEY
- MPESA_CONSUMER_SECRET
- MPESA_SHORTCODE
- MPESA_PASSKEY
- MPESA_CALLBACK_URL

AI / Inference key (optional — falls back to unauthenticated inference):
- HUGGINGFACE_API_KEY

Stripe (optional / present in DB model fields if you want to connect stripe later):
- STRIPE_SECRET_KEY
- STRIPE_PUBLISHABLE_KEY

Example .env (do NOT add real secrets here):

```env
SECRET_KEY=change-me
JWT_SECRET_KEY=change-me
DATABASE_URL=sqlite:///instance/ai_tutor.db

# M-Pesa (sandbox)
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY=your_sandbox_key
MPESA_CONSUMER_SECRET=your_sandbox_secret
MPESA_SHORTCODE=174379
MPESA_PASSKEY=your_passkey
MPESA_CALLBACK_URL=https://your-public-callback-url/api/subscription/mpesa-callback

# Hugging Face (optional)
HUGGINGFACE_API_KEY=hf_...
```

---

## 🗂️ Project structure (overview)

Key folders and files:

- ai_tutor_backend/
	- app/       — application package (models, routes, services, templates)
	- app.py     — simple dev / production entrypoint
	- requirements.txt
	- migrations/ — Alembic DB migrations
	- tests/      — unit/functional tests

---

## 📡 API highlights

Auth endpoints (/api/auth)
- POST /api/auth/register — register new user
- POST /api/auth/login — obtain JWT access and refresh tokens
- POST /api/auth/refresh — exchange refresh token for a new access token
- GET /api/auth/me — fetch current user

Tutor endpoints (/api/tutor)
- POST /api/tutor/explain — submit explanation for AI feedback (requires Authorization: Bearer <access_token>)
- GET /api/tutor/history — learning history per user
- GET /api/tutor/progress — progress summaries
- GET /api/tutor/recommendations — study tips and weak-topic recommendations

Subscription & payments (/api/subscription)
- GET /api/subscription/plans — get available plans
- POST /api/subscription/initiate-mpesa — start M-Pesa STK Push
- POST /api/subscription/check-payment — check M-Pesa payment status
- POST /api/subscription/mpesa-callback — endpoint Safaricom calls (server-to-server)

Example: register + submit an explanation (curl)

```bash
# Register
curl -s -X POST http://localhost:5000/api/auth/register \
	-H "Content-Type: application/json" \
	-d '{"email":"test@example.com","name":"Test","password":"password123"}'

# Login and use token
# Then POST explanation using the returned access_token:
curl -s -X POST http://localhost:5000/api/tutor/explain \
	-H "Authorization: Bearer <ACCESS_TOKEN>" \
	-H "Content-Type: application/json" \
	-d '{"concept":"Photosynthesis", "explanation":"Plants convert sunlight to energy by ..."}'
```

---

## 🧪 Testing

Run the test suite with pytest from the `ai_tutor_backend` folder:

```powershell
cd ai_tutor_backend
pytest -q
```

There is also a `test_mpesa_integration.py` helper script that checks M-Pesa configuration and simulates STK Push behavior — use it as a diagnostics tool (requires MPESA env vars).

---

## 📦 Database & migrations

By default the app uses SQLite for local development and PostgreSQL if `DATABASE_URL` is provided.

Create & run migrations (Flask-Migrate / Alembic):

```powershell
$env:FLASK_APP = "app:create_app"
flask db migrate -m "Create models"
flask db upgrade
```

---

## 🧩 Deployment notes

- Use a production-grade WSGI server such as gunicorn or uWSGI
- Ensure DATABASE_URL points to a managed Postgres instance in production
- Protect and rotate API keys and secrets using your cloud provider's secret store
- Expose `MPESA_CALLBACK_URL` as a publicly reachable HTTPS URL for Daraja callbacks (ngrok or proper domain)

---

