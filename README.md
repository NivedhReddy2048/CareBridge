# 🚀 CareBridge — Enterprise Healthcare Platform

CareBridge is a modern, full-stack Django healthcare and telemedicine platform designed to connect patients with healthcare providers. It provides end-to-end workflows for patient registration, appointment scheduling, electronic health records (EHR) management, OCR report parsing, online payment processing, real-time video consultation signaling, and AI-assisted clinical symptom analysis.

Built with a modular Django architecture, CareBridge incorporates asynchronous background processing via Celery and Redis, real-time WebSocket communication through Django Channels and Daphne, and environment-aware security controls for local development and cloud deployment.

---

# 🔴 Live Demo

- **Deployed Application**: [🔴 Live Demo — CareBridge](https://carebridge-ugeq.onrender.com)
- **Enterprise Analytics & Monitoring Portal**: [CareBridge Enterprise Portal](https://carebridge-ugeq.onrender.com/enterprise/)
- **Administrative Portal**: [Admin Portal](https://carebridge-ugeq.onrender.com/admin/)

---

# ✨ Key Features

## 🔐 Authentication & User Management
- **Multi-Role User Accounts**: Dedicated roles for Patients, Doctors, Staff, and Administrators powered by a custom user model (`CustomUser`) with auto-generated patient IDs (e.g., `P-XXXXXX`).
- **Environment-Aware Registration OTP Flow**:
  - **Local Development (`local.py`)**: Enforces email/console OTP verification (`REQUIRE_PATIENT_OTP = True`) prior to account activation.
  - **Production / Render (`production.py`)**: Bypasses registration OTP (`REQUIRE_PATIENT_OTP = False`), activating accounts directly (`is_active = True`) and redirecting immediately to patient login.
- **Staff Password Reset**: Secure OTP-based credential recovery flow for hospital staff.
- **Access Control & Cache Security**: `@never_cache`, `@login_required`, and role-specific permissions protect sensitive user pages.

## 🏥 Patient Features
- **Patient Dashboard**: Central hub displaying upcoming appointments, medical history, and notification alerts.
- **Doctor Discovery & Booking**: Search available doctors, view specialization details, and reserve appointment slots.
- **Health Records Management**: Upload lab reports and medical documents directly to the patient profile.
- **Notification Center**: Real-time in-app alerts and email updates regarding booking statuses and system announcements.

## 👨‍⚕️ Doctor / Staff Features
- **Doctor Dashboard**: Manage daily consultation schedules, view patient profiles, and track appointment statuses.
- **Clinical Review**: Access uploaded patient medical records and lab report extractions during consultations.
- **Staff Portal**: Administrative user creation, appointment oversight, and patient account management.
- **Telemedicine Observability**: Real-time system monitoring dashboard for ongoing video consultation sessions (`/enterprise/telemedicine/`).

## 📅 Appointment & Scheduling System
- **Slot Management**: Prevents double-booking conflicts by validating doctor schedules and time availability.
- **Status Lifecycle Tracking**: Transition appointments through `scheduled`, `completed`, and `cancelled` states.
- **Integrated Billing**: Link appointment reservations to payment order generation.

## 📹 Telemedicine
- **Native WebSocket Signaling**: Real-time video consultation signaling built with Django Channels and ASGI Daphne backend on `ws/telemedicine/<room_id>/`.
- **WebRTC Peer Connection**: Low-latency peer-to-peer signaling for video, audio, and room state exchange.
- **Session Auditing**: Automated creation of consultation session records and audit logs.

## 📄 Medical Records / EHR
- **Document Management**: Secure upload and storage of PDF and image-based medical reports.
- **OCR Text Extraction**: Automated clinical text parsing from scanned reports using Tesseract OCR (`pytesseract`), `pdf2image`, `pdfplumber`, and `pypdfium2`.
- **Flexible File Storage**: Configured for private cloud storage via AWS S3 (`django-storages`, `boto3`) when bucket credentials are supplied, with local `FileSystemStorage` fallback.

## 💳 Billing & Payments
- **Razorpay Integration**: Native integration with the Razorpay Payment Gateway SDK for appointment fees.
- **Payment Verification**: Server-side cryptographic signature validation (`razorpay_signature`) for transaction integrity.
- **Asynchronous Webhooks**: Webhook listener (`RazorpayWebhookView`) to handle out-of-band payment status updates (`pending`, `completed`, `failed`).

## 🔔 Notifications
- **In-App Messaging**: Persistent database notifications rendered across user dashboards.
- **Dual Email Architecture**:
  - **Local Development**: Standard Django SMTP email backend for local testing.
  - **Production**: High-deliverability HTTPS API integration via **Resend** (`resend.Emails.send`).

## 🤖 AI / Intelligent Features
- **AI Symptom Analyzer**: Clinical assistant service integrating Google's Gemini API (`google-generativeai`) to provide preliminary symptom insights.
- **Privacy Anonymizer**: Pre-processes clinical text to redact sensitive patient identifier fields before sending prompts to external AI APIs.
- **Async AI Pipelines**: Offloads LLM inference and heavy analysis to background Celery workers to maintain frontend responsiveness.

> [!IMPORTANT]
> AI features are strictly software-assistive tools designed to assist workflows and do NOT perform medical diagnosis or replace licensed healthcare professionals.

---

# 🏗️ Architecture

```
                                  +------------------------+
                                  |     Client Browser     |
                                  +-----------+------------+
                                              |
                                     HTTP / WebSockets
                                              |
                                              v
                                  +------------------------+
                                  |   Render / Docker      |
                                  |    Daphne (ASGI)       |
                                  +-----------+------------+
                                              |
                     +------------------------+------------------------+
                     |                                                 |
                     v                                                 v
        +-------------------------+                       +-------------------------+
        |   Django Core Web App   |                       |    Django Channels      |
        |  (Accounts, EHR, etc.)  |                       |  (WebSocket Signaling)  |
        +------------+------------+                       +------------+------------+
                     |                                                 |
                     |                                                 |
        +------------+------------+                       +------------+------------+
        |   PostgreSQL Database   |                       |      Redis Broker       |
        +-------------------------+                       +------------+------------+
                                                                       |
                                                          +------------+------------+
                                                          |      Celery Workers     |
                                                          |  (Async Tasks & AI)     |
                                                          +------------+------------+
                                                                       |
                                                    +------------------+------------------+
                                                    |                  |                  |
                                                    v                  v                  v
                                             +--------------+   +--------------+   +--------------+
                                             | Resend Email |   | Razorpay API |   | Gemini AI    |
                                             +--------------+   +--------------+   +--------------+
```

---

# 🛠️ Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Backend Framework** | Django (v6.0 / v4.2), Python 3.11+ |
| **ASGI / WebSockets** | Django Channels, Daphne, Twisted |
| **Database** | PostgreSQL (Production via `dj-database-url`), SQLite3 (Local) |
| **Task Queue & Cache** | Celery, Redis (`channels_redis`) |
| **REST APIs** | Django REST Framework (DRF), SimpleJWT, drf-spectacular (OpenAPI 3.0) |
| **OCR & Document Parsing** | Tesseract OCR (`pytesseract`), `pdf2image`, `pdfplumber`, `pypdfium2`, ReportLab |
| **Payments** | Razorpay SDK |
| **Email Delivery** | Resend API (Production), SMTP Backend (Local) |
| **AI Integration** | Google Gemini API (`google-generativeai`) |
| **Cloud Storage** | AWS S3 (`boto3`, `django-storages`) / Local Media Storage |
| **Containerization & Hosting** | Docker (Multi-stage build), Docker Compose, Render |

---

# 📂 Project Structure

```text
CareBridge/
├── accounts/                  # Authentication, roles, custom user model & registration views
├── ai_engine/                 # AI symptom analyzer views and endpoints
├── ai_orchestration/          # Celery task definitions for asynchronous AI pipelines
├── analytics/                 # Healthcare telemetry and analytics dashboards
├── api/                       # DRF v1 endpoints, JWT authentication & API routing
│   └── v1/                    # Versioned REST APIs and Spectacular OpenAPI schema
├── appointments/              # Appointment scheduling logic, slots, and availability
├── billing/                   # Razorpay payment orders, verification, and webhooks
├── clinical_intelligence/     # AI prompt orchestration and clinical summary engines
├── config/                    # Core Django settings & configuration
│   ├── settings/
│   │   ├── base.py            # Shared settings, apps, and middleware
│   │   ├── local.py           # Local dev settings (DEBUG=True, REQUIRE_PATIENT_OTP=True)
│   │   └── production.py      # Production settings (DEBUG=False, REQUIRE_PATIENT_OTP=False)
│   ├── asgi.py                # ASGI application entrypoint for Channels & Daphne
│   ├── urls.py                # Root URL routing table
│   └── wsgi.py                # WSGI entrypoint
├── core/                      # Shared utility functions and base models
├── dashboard/                 # User dashboard views (Patient, Doctor, Staff)
├── ehr/                       # Electronic Health Records & Tesseract OCR parsing engine
├── enterprise/                # System audit logs and telemedicine observability dashboards
├── intelligence/              # Patient data anonymizer and AI helper services
├── notifications/             # Notification models, services, and inbox views
├── records/                   # Storage backends and media document handlers
├── telemedicine/              # Real-time WebSocket consumers, WebRTC signaling & sessions
├── templates/                 # HTML templates organized by app domain
├── tests/                     # Unit, integration, and reliability test suites
├── .env.example               # Template for environment configuration
├── build.sh                   # Deployment build script for Render
├── Dockerfile                 # Multi-stage production Docker configuration
├── docker-compose.yml         # Local multi-container development configuration
├── entrypoint.sh              # Container startup script (migrations, superuser, static)
├── manage.py                  # Django management script
├── render.yaml                # Infrastructure-as-code specification for Render
└── requirements.txt           # Python dependency specification
```

---

# 🔐 Security & Configuration

CareBridge is built with production security practices in mind:

- **Environment Isolation**: Separate setting modules (`local.py` vs `production.py`) ensure debug features and local fallbacks are never exposed in production.
- **HTTP Security Headers**: Enforces `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_BROWSER_XSS_FILTER`, `SECURE_CONTENT_TYPE_NOSNIFF`, and HSTS in production.
- **Cryptographic Signature Verification**: Validates Razorpay payment webhooks and payment confirmations server-side before updating database state.
- **Privacy Redaction**: Redacts identifiable health information before submitting symptom prompts to third-party AI APIs.

> [!NOTE]
> CareBridge is an educational and portfolio enterprise project designed with healthcare security standards, but it is not formally HIPAA certified.

---

# 🚀 Production Deployment

CareBridge is configured for automated containerized deployment on **Render** via `render.yaml` and `Dockerfile`.

- **Live URL**: [https://carebridge-ugeq.onrender.com](https://carebridge-ugeq.onrender.com)
- **Deployment Platform**: Render (Web Service + Worker + PostgreSQL + Redis)
- **ASGI Web Server**: Daphne serving `config.asgi:application`
- **Container Entrypoint (`entrypoint.sh`)**:
  Automatic execution of migrations, superuser bootstrapping, static file collection, and Daphne web server startup.

---

# 📸 Screenshots

<!-- Add screenshot: docs/screenshots/home-page.png -->
### 🏠 Home Page

<!-- Add screenshot: docs/screenshots/patient-registration.png -->
### 📝 Patient Registration

<!-- Add screenshot: docs/screenshots/patient-dashboard.png -->
### 📊 Patient Dashboard

<!-- Add screenshot: docs/screenshots/doctor-dashboard.png -->
### 👨‍⚕️ Doctor Dashboard

<!-- Add screenshot: docs/screenshots/appointment-booking.png -->
### 📅 Appointment Booking

<!-- Add screenshot: docs/screenshots/telemedicine-call.png -->
### 📹 Telemedicine Video Consultation

<!-- Add screenshot: docs/screenshots/ehr-report-upload.png -->
### 📄 EHR Report & OCR Parsing

<!-- Add screenshot: docs/screenshots/billing-checkout.png -->
### 💳 Billing & Razorpay Payment

---

# 📊 Engineering Highlights

- **Environment-Aware OTP Architecture**: Flexible authentication pipeline that retains secure OTP verification locally while offering frictionless patient onboarding on cloud deployments.
- **Asynchronous Task Offloading**: Heavy LLM processing and email delivery tasks are delegated to Celery workers, preserving low response latencies on web endpoints.
- **Real-Time WebSockets Signaling**: Native Django Channels layer powering low-latency video consultation room creation.
- **OCR Clinical Extraction**: Multi-library document pipeline parsing raw patient PDFs and lab images into structured text.
- **Secure Payment Handling**: End-to-end Razorpay integration with server-side signature validation and webhook reconciliation.

---

# 🧭 Project Evolution

CareBridge evolved through several engineering iterations:

1. **Core Platform Foundation**: Development of modular Django apps (`accounts`, `appointments`, `ehr`, `dashboard`) and custom patient models.
2. **Environment & Security Hardening**: Splitting settings into `local.py` and `production.py`, establishing environment-aware patient registration flows, and adding HTTP security headers.
3. **Telemedicine & Async Architecture**: Integrating Django Channels, Daphne, and WebSockets for real-time consultation signaling, alongside Celery and Redis task orchestration.
4. **EHR OCR & AI Integration**: Implementing Tesseract OCR report extractions and Google Gemini clinical analysis services.
5. **Billing & Production Deployment**: Integrating Razorpay gateway payments, Docker containerization, and automated deployment on Render.

---

# 🔮 Future Improvements

- [ ] **Expanded Test Coverage**: Increasing end-to-end integration test coverage for WebSocket channels and payment webhooks.
- [ ] **Mobile Application**: Developing a native mobile client for Android and iOS patients.
- [ ] **Enhanced Analytics**: Expanding clinical data visualization and doctor schedule analytics.
- [ ] **Multi-Language Support**: Adding localization and multi-language translation for patient interfaces.

---

# 📜 License

This project is currently developed for educational, research, and portfolio purposes.

---

# 👨‍💻 Developer

**Nivedh Reddy**
- **GitHub**: [https://github.com/NivedhReddy2048](https://github.com/NivedhReddy2048)

---

👥 Collaboration Team

<div align="right">

<a href="https://github.com/KailashSatkuri-warangal">

<img src="https://github.com/KailashSatkuri-warangal.png" width="60px" style="border-radius:50%" title="Kailash Satkuri" />

</a>

<a href="https://github.com/SHIVASHANKAR-KODURI">

<img src="https://github.com/SHIVASHANKAR-KODURI.png" width="60px" style="border-radius:50%" title="Koduri Shiva Shankar" />

</a>

<a href="https://github.com/Hrudairaj">

<img src="https://github.com/Hrudairaj.png" width="60px" style="border-radius:50%" title="Gogikar Hrudai" />

</a>

<a href="https://github.com/Siddhartha741">

<img src="https://github.com/Siddhartha741.png" width="60px" style="border-radius:50%" title="Siddhartha Namilikonda" />

</a>

<a href="https://github.com/NivedhReddy2048">

<img src="https://github.com/NivedhReddy2048.png" width="60px" style="border-radius:50%" title="Nivedh Reddy" />

</a>

</div>
