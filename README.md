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

**Key Tables:**

- `users`: Stores user information and merged profile details.
- `social_profiles`: Manages user social media profiles.
- `topics`: Hierarchical structure for course topics.
- `courses`: Stores course information.
- `enrollments`: Tracks student enrollments in courses.
- `sections` and `lessons`: Manages course content structure.
- `quizzes` and related tables: Handles quiz creation and student attempts.
- `cart` and `wishlist`: Manages shopping cart and wishlist items.
- `payments` and `orders`: Handles payment and order processing.
- `wallets` and `wallet_transactions`: Manages user wallets and transactions.
- `coupons` and related tables: Handles coupon creation and usage.

**Enums:**

- `user_role`: Defines user roles (student, instructor, admin, super_admin).
- `course_level`: Defines course difficulty levels.
- `payment_status`, `order_status`: Defines payment and order statuses.
- `wallet_transaction_type`: Defines wallet transaction types.
- `course_detail_type`: Defines course detail types.
- `coupon_type`, `coupon_status`: Defines coupon types and statuses.

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
