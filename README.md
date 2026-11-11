# AI Sales Caller

A React + Vite frontend and FastAPI backend for an opt-in AI sales-calling starter.

## What works, and what does not yet

- **Browser demo (Vercel):** Text-scripted presentation with speech synthesis. It is **not** a live customer conversation.
- **Twilio Realtime backend (new):** Source code for **one consented outbound call**, Twilio Media Streams, two-way audio bridged to OpenAI Realtime, a spoken AI disclosure, opt-out suppression and human follow-up requests.
- **Not yet live-tested:** No Twilio account, phone number, OpenAI API key, persistent backend deployment, or end-to-end customer phone test has been configured in this repository's hosting environment. Do **not** claim this can autonomously close sales today.
- **No automated contract or payment execution:** The assistant can explain verified offerings and qualify interest. A human confirms pricing, contracts, scheduling and payment through approved systems.

## Architecture

```text
Vercel static React dashboard (scripted demo; no API credentials)
                       |
                   (separate)
                       |
Authorized operator -> FastAPI POST /twilio/call/{lead_id} (X-Admin-Key)
                       |
               Twilio Programmable Voice
                       |
                 POST /twilio/voice
                       |
               <Connect><Stream> WSS
                       |
      Persistent FastAPI WebSocket /twilio/media
                       |
         OpenAI Realtime API speech-to-speech
                       |
  request_human_followup / mark_do_not_call -> PostgreSQL
```

The Twilio WebSocket endpoint needs a **persistent, HTTPS/WSS-capable backend host** (for example, Render or Railway). The frontend-only Vercel deployment is not sufficient for live calls. Use a managed database; do not run a disposable local SQLite database in production.

## 1. Get accounts and verified credentials

1. Sign up for [Twilio Programmable Voice](https://www.twilio.com/docs/voice). Purchase/configure a voice-enabled number. Check supported calling destinations, verified caller ID, geo permissions, usage pricing and any trial restrictions **before** attempting international calls.
2. Create an OpenAI API key with permission, billing and capacity for a supported Realtime model. Review [Realtime WebSockets](https://developers.openai.com/api/docs/guides/realtime-conversations).
3. Deploy the `backend/` Dockerfile to a **persistent** backend hosting service with public HTTPS/WSS access and PostgreSQL. Use the platform's secret environment-variable settings; never commit credentials.
4. Set `PUBLIC_BASE_URL=https://your-backend-host` (no trailing slash) and the Twilio credentials from `.env.example`. Set a strong random `SALES_ADMIN_KEY`.
5. Set `APPROVED_SALES_FACTS` to **verified** service descriptions, allowed claims and approved prices. Empty values disable calls.
6. Start with `ENABLE_OUTBOUND_CALLS=false`. After confirming legal authorization for every destination, consent records, calling windows, AI disclosure and opt-out process, enable it for a **single test lead** only.

**Critical:** The old `POST /calls/start/{lead_id}` SIP starter has been disabled; it never confirmed an actual conversation. Use the Twilio endpoint below.

## 2. Local backend

```bash
cp .env.example .env
# Set credentials and approved facts directly in .env; do not commit it.
docker compose up --build
curl http://localhost:8000/health
```

For a real Twilio call, `PUBLIC_BASE_URL` must point to a publicly reachable HTTPS backend that can also handle WSS; `localhost` isn't sufficient. The development backend reads `DATABASE_URL` and creates starter tables at launch; use Alembic migrations in production.

## 3. Add one consented lead and request one call

Only set consent to `granted` if you actually have lawful, documented authorization. Imported phone numbers are not consent.

```bash
# Run these against your backend's HTTPS base URL.
curl -X POST "https://YOUR_BACKEND/leads" \
  -H "X-Admin-Key: YOUR_PRIVATE_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"company_name":"Authorized Test Business","contact_name":"Test Customer","phone":"+15551234567","consent_status":"granted","consent_source":"Documented explicit test opt-in"}'

# Use the real lead ID returned above.
curl -X POST "https://YOUR_BACKEND/twilio/call/1" \
  -H "X-Admin-Key: YOUR_PRIVATE_ADMIN_KEY"
```

**Never place an admin key in React client-side code or Vercel `VITE_*` variables.** Store it only on the trusted server or in a private operator workflow. Do not use the placeholder number above for an actual call.

The endpoint supports **single-lead calls only**, checks recorded consent and suppression, imposes a 24-hour per-lead cooldown, and is **disabled by default**. A 202 response means Twilio accepted the dialing request; it is not proof of a connected call, sale or appointment. `/twilio/status` updates call status. The media stream is authorized with a short-lived signed token; Twilio HTTP webhooks validate `X-Twilio-Signature`.

The Realtime agent is instructed to disclose it's AI, use only approved claims, avoid binding promises, respect stop requests and offer human follow-up. A model tool call can update `do_not_call` or `followup_requested` in the database. Voice/model/API compatibility and telephony interruptions need real-world testing before release.

## Frontend demo

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL, choose **Live demo** and **Start demo conversation**, with **Speak conversation aloud** enabled for browser-generated voice. This is a prewritten text demonstration, not a live AI call.

## Safety and production checklist

- Explicitly review country/channel-specific calling rules, registration, consent, call windows and recording/transcription disclosures.
- Confirm opt-out suppression works in practice and audit all outcomes.
- Add rate limits, authenticated role-based management, worker monitoring, idempotency and real-time error alerts before any production campaign.
- Add production database migrations, secure admin UI, tests with a real trial call, sales-team follow-up scheduling and a verified CRM.
- Do not allow the AI to process cards, enter contracts or invent discounts; use explicit human approval and verified integrations for closing.
- Monitor call spending and latency. Automatic bulk calling or scheduled autodialing is intentionally **not** implemented.
