# CareBridge Enterprise Healthcare Platform

CareBridge is a fully modernized, distributed asynchronous Django healthcare platform. Over 12 distinct engineering phases, CareBridge evolved from a monolithic MVP into a scalable, real-time, AI-driven telemedicine SaaS platform.

## 🚀 Key Enterprise Features

### 1. Real-Time Telemedicine (WebRTC & WebSockets)
- **Live Consultations**: Patients and Doctors can join secure video rooms.
- **WebSocket Signaling**: Native Daphne/ASGI channels implementation powered by a Redis Pub/Sub backend.
- **Event-Driven Architecture**: Chat and custom signaling events are seamlessly broadcast across authenticated channel layers.

### 2. Distributed AI Orchestration
- **Gemini Clinical Intelligence**: Live consultation transcripts are asynchronously fed into Google's Gemini Pro LLM.
- **Celery & Redis Pipelines**: Heavy AI inference tasks are detached from the WebSocket loop, preventing latency spikes. 
- **Retry-Safe Orchestration**: Task pipelines incorporate exponential backoffs and graceful failure modes to handle third-party AI downtime without interrupting patient care.

### 3. Enterprise Observability & Monitoring
- **Real-Time Dashboards**: Granular metrics across Celery Workers, Active WebSockets, AI Tokens consumed, and Redis Queues.
- **Audit Trails**: Extensive logging of every clinical action, AI fallback, and system error to ensure HIPAA-level traceability.

### 4. Zero-Trust Storage Architecture
- **Presigned Cloud Storage**: Medical reports and EHR payloads are never statically hosted. Files reside in secure, private Amazon S3 buckets, accessed only via short-lived, encrypted, pre-signed AWS URLs.
- **File Validation**: Strict MIME-type validations and basic malware scanning hooks exist to prevent arbitrary uploads.

## 🏗️ Technology Stack
- **Core Engine**: Django 4.2+, Python 3.14+
- **APIs**: Django REST Framework (DRF), JWT Authentication
- **Real-Time Layer**: Django Channels, Daphne, WebSockets
- **Async Workers**: Celery
- **In-Memory Store/Message Broker**: Redis
- **Database**: PostgreSQL
- **Cloud Infrastructure**: AWS S3, Render (Deployment target)
- **AI Core**: Google DeepMind Gemini (`google.generativeai`)

## ⚙️ Deployment Overview
This system is designed to be fully containerized. Please refer to `DEPLOYMENT_GUIDE.md` and `ARCHITECTURE_OVERVIEW.md` for specific instructions regarding environment variables (`.env.example`), scaling Celery workers, and managing Daphne WS concurrency.

## 👥 Collaboration Team
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