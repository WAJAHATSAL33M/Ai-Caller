# AI Sales Caller

Starter foundation for an AI voice business-development agent that introduces your call-center services, discovers prospect needs, qualifies interest, and routes prospects to a human sales representative.

## Project status

**Development starter only — not production-ready or yet validated with a live call.** Includes a FastAPI API, PostgreSQL models, guarded single-lead outbound-call request via OpenAI Live SIP, and a small React lead dashboard.

A successful API response means the session request was accepted; it does not prove a person answered or a sales conversation completed. Before live use, implement and test the Live session sideband WebSocket: attach to each session, process ringing/answered/failed/closed events, execute approved tools, persist outcomes, and handle hangup/transfer.

## Stack

- Python 3.12, FastAPI, SQLAlchemy 2, PostgreSQL
- OpenAI Live API over SIP
- React + Vite dashboard
- Docker Compose

## Quick start

1. Copy `.env.example` to `.env` and fill in valid credentials. Never commit `.env`.
2. Configure a SIP trunk that supports TLS and SRTP and is authorized for your intended destinations.
3. Run `docker compose up --build`.
4. API docs: http://localhost:8000/docs
5. Dashboard: http://localhost:5173

The API creates tables at startup for local development. Use Alembic migrations before production.

## API

- `GET /health`
- `POST /leads`
- `GET /leads`
- `POST /calls/start/{lead_id}`

A lead must have `consent_status="granted"`, a non-empty `consent_source`, and `do_not_call=false` before the call endpoint proceeds. Only set these fields after verifying lawful authorization for the relevant country and channel. An imported phone number is not consent.

## Production checklist

- Implement and test the OpenAI Live session sideband WebSocket and server-side tool execution.
- Add idempotency, retries, rate limits, audit logs, monitoring, authentication, and authorization.
- Add country-specific legal review: consent/lawful basis, do-not-call registries, caller-ID rules, AI disclosure, recording/transcription notices, local calling windows, and data retention/transfer.
- Add CRM integration, human handoff, appointment-calendar integration, and a tested opt-out/suppression workflow.
- Add Alembic migrations and automated tests.
- Verify every service claim, price, case study, and capacity statement before allowing the agent to use it.

## Safety defaults

The agent must disclose it is an AI assistant, respect requests to stop, avoid unsupported claims, and never accept payment details or make binding commitments. Do not enable bulk calling until compliance and event-handling controls are reviewed.

## Local development without Docker

Backend: `cd backend && pip install -r requirements.txt && uvicorn app.main:app --reload` (set `DATABASE_URL` and other environment variables first).

Frontend: `cd frontend && npm install && npm run dev`.


## Client presentation demo

The React dashboard includes a browser-based sample conversation. Start the frontend with `cd frontend && npm install && npm run dev`, then open the Vite URL shown in the terminal. Select **Live demo** and click **Start demo conversation**. You can edit the sample prospect profile and replay or stop the scripted conversation.

This presentation mode is simulated: it does not dial a phone, use a microphone, contact a prospect, create a CRM record, or book a meeting. It is intended to demonstrate the proposed conversation flow while the production voice integration is completed and tested.
