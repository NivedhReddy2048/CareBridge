# CareBridge Architecture Overview

CareBridge is a monolithic enterprise healthcare platform designed for high availability, security, and scalability.

## 1. Request Handling (Daphne/ASGI)
All incoming traffic is processed by Daphne, an ASGI compliant web server. 
- **HTTP/REST Requests**: Routed to Django's standard HTTP pipeline. The API is powered by Django REST Framework (DRF) serving JSON payloads.
- **WebSocket Connections**: Routed through `ProtocolTypeRouter` to Django Channels. JWT authentication is enforced via custom middleware.

## 2. Real-Time Telemedicine & WebSockets
Telemedicine consultations use WebRTC signaling over WebSockets.
- Real-time `CHAT` and `SIGNAL` events are broadcast instantly via a Redis-backed channel layer.
- Long-running inference operations are completely detached from this layer.

## 3. AI Orchestration Pipeline
Instead of blocking the realtime loop, the `ai_orchestration` layer pushes AI aggregation tasks into Celery.
- **Workers**: Asynchronous Celery workers pick up `TRANSCRIPT_SUMMARY` tasks.
- **LLM Engine**: Workers interface with Google Gemini to generate structured clinical intelligence.
- **Event Callbacks**: Completed insights are pushed back to the client natively over the same WebSocket room connection using Redis Pub/Sub.

## 4. Storage & EHR Security
- File payloads and medical records are synchronized to Amazon S3 via `boto3`.
- The storage configuration enforces Private Media Storage policies. All links generated are pre-signed with short expiration windows.

## 5. Deployment Ecosystem
The application is pre-configured with a Render deployment blueprint (`render.yaml`) orchestrating a managed PostgreSQL instance, a Redis cluster, Web services, and background Celery workers natively.
