# Skillexa API - Django REST Framework

Skillexa is an e-learning platform API built using Django REST Framework (DRF). It provides a robust and scalable backend for managing user authentication, OTP verification, social logins, course management, shopping, payments, and other core functionalities.

## Table of Contents

- [Features](#features)
- [Database Schema](#database-schema)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
  - [Running the API](#running-the-api)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Celery Configuration](#celery-configuration)
- [Rate Limiting](#rate-limiting)
- [Django Admin](#django-admin)
- [Authentication](#authentication)
- [Email Configuration](#email-configuration)
- [Google Sign-in](#google-sign-in)
- [Contributing](#contributing)
- [License](#license)

## Features

- **User Authentication:**
  - Credential-based login.
  - Google Sign-in with ID token verification using `google-auth`.
  - JWT authentication using `rest_framework_simplejwt`.
- **OTP Verification:**
  - OTP generation and storage.
  - Asynchronous OTP email sending using Celery.
  - OTP verification endpoint.
  - OTP resend endpoint.
- **Social Profiles:**
  - Management of user social profiles.
- **Course Management:**
  - Creation, editing, and publishing of courses.
  - Course sections and lessons management.
  - Quizzes and question management.
- **Enrollments and Student Progress:**
  - Student enrollment tracking.
  - Tracking student progress through lessons and quizzes.
- **Shopping and Payments:**
  - Shopping cart and wishlist management.
  - Payment processing and order management.
  - Wallet system for user balances.
  - Coupon system with various discount types.
- **API Rate Limiting:**
  - Global rate limiting for authenticated (2000 requests/day) and anonymous users (200 requests/hour).
  - Endpoint-specific rate limiting for OTP requests (10 requests/hour) and login attempts (10 requests/10 minutes).
- **Django Admin:**
  - Registered models (`SocialProfile`, `OtpVerification`) for easy management through the Django admin panel.
- **Asynchronous Tasks:**
  - Background email sending using Celery.
- **Unit and Integration Testing:**
  - Comprehensive test suites for all API endpoints.
- **CORS Support:**
  - CORS enabled for all origins for development (ensure proper configuration for production).

## Database Schema

The database schema is designed to support the e-learning platform's functionalities. You can view the full schema diagram [here](https://dbdiagram.io/d/skillexa-2-67ac964f263d6cf9a0e7513a).

## Getting Started

### Prerequisites

- Python (3.13+)
- pip
- Virtualenv (recommended)
- PostgreSQL
- Redis
- Google Cloud Platform Account (for Google Sign-in)

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/vaisakhpv033/SKILLEXA
   cd skillexa
   ```

2. Create a Virtual Environment (Recommended):

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Linux/macOS
   venv\Scripts\activate  # On Windows
   ```

3. Install Dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Configuration

### Environment Variables

Create a `.env` file in the project root and add your environment variables:

```env
SECRET_KEY=<your_secret_key>
DEBUG=True/False
DB_NAME=<your_db_name>
DB_USER=<your_db_user>
DB_PASSWORD=<your_db_password>
DB_HOST=<your_db_host>
CELERY_BROKER_URL=redis://<redis_host>:<redis_port>/0
GOOGLE_CLIENT_ID=<your_google_client_id>
GOOGLE_CLIENT_SECRET=<your_google_client_secret>
EMAIL_HOST=<your_email_host>
EMAIL_PORT=<your_email_port>
EMAIL_HOST_USER=<your_email_user>
EMAIL_HOST_PASSWORD=<your_email_password>
DEFAULT_FROM_EMAIL=<your_default_from_email>
```

## Running the API

### Start the Django Development Server

```bash
python manage.py runserver
```

### Start the Celery Worker

#### On Linux/macOS
```bash
celery -A skillexa worker -l info
```

#### On Windows
```bash
celery -A skillexa worker --loglevel=info -P solo
```

### Start the Celery Beat Scheduler (if needed)

```bash
celery -A skillexa beat -l info
```

## API Endpoints

### User Authentication

- **User Registration:** `POST /api/register/`
- **User Login:** `POST /api/login/`
- **Google Sign-in:** `POST /api/google-signin/`
- **OTP Verification:** `POST /api/verify-otp/`
- **Resend OTP:** `POST /api/resend-otp/`
- **User Profile:** `GET /api/profile/` (Requires JWT authentication)

## Testing

### Run Unit and Integration Tests

```bash
python manage.py test
```

### Run Specific Tests

```bash
python manage.py test <app_name>.tests.<ClassName>
```

### Run Specific Test Method

```bash
python manage.py test <app_name>.tests.<ClassName>.<test_method>
```

## Celery Configuration

- Ensure Redis is running and properly configured in `.env`.
- Start the Celery worker and beat scheduler as described in the "Running the API" section.

## Rate Limiting

- Global rate limits are configured in `settings.py`.
- Endpoint-specific rate limits are defined in `accounts/throttling.py`.

## Django Admin

- Access the Django Admin Panel at `/admin/`.
- Log in with your superuser credentials.
- Manage users, social profiles, and OTP verifications.

## Authentication

- JWT authentication is used for API endpoints requiring user authentication.
- JWT settings are configured in `settings.py` using `rest_framework_simplejwt`.

## Email Configuration

- Configure email settings in `.env`.
- Ensure email service is properly set up for OTP email sending.

## Google Sign-in

- Configure Google Client ID and Secret in `.env`.
- Ensure Google Cloud Platform project is set up for OAuth 2.0.

## Contributing

1. Fork the repository.
2. Create a new branch for your feature or bug fix.
3. Commit your changes.
4. Push to your branch.
5. Create a pull request.

## License

This project is licensed under the MIT License.

