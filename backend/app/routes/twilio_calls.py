"""Twilio Programmable Voice + OpenAI Realtime audio bridge.

A persistent ASGI host is required (WebSockets are not hosted by the static Vercel UI).
Outbound calling is disabled unless explicitly configured and authorized.
"""
import asyncio
import hmac
import json
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Response, WebSocket
from fastapi.concurrency import run_in_threadpool
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session
from twilio.request_validator import RequestValidator
from twilio.rest import Client
from twilio.twiml.voice_response import Connect, Stream, VoiceResponse
from websockets.asyncio.client import connect

from app.config import settings
from app.database import SessionLocal, get_db
from app.models import Call, Lead

log = logging.getLogger(__name__)
router = APIRouter(prefix="/twilio", tags=["twilio"])
FINAL_STATUSES = {"completed", "busy", "failed", "no-answer", "canceled"}


def public_url(path: str) -> str:
    return settings.public_base_url.rstrip("/") + path


def require_config():
    required = {
        "OPENAI_API_KEY": settings.openai_api_key,
        "TWILIO_ACCOUNT_SID": settings.twilio_account_sid,
        "TWILIO_AUTH_TOKEN": settings.twilio_auth_token,
        "TWILIO_PHONE_NUMBER": settings.twilio_phone_number,
        "PUBLIC_BASE_URL": settings.public_base_url,
        "SALES_ADMIN_KEY": settings.sales_admin_key,
        "APPROVED_SALES_FACTS": settings.approved_sales_facts,
    }
    missing = [key for key, val in required.items() if not val or val == "replace_me"]
    if missing or not settings.public_base_url.startswith("https://"):
        raise HTTPException(503, detail="Voice service not configured: " + ", ".join(missing or ["PUBLIC_BASE_URL must use HTTPS"]))


def validate_twilio(request: Request, params: dict, callback_url: str):
    signature = request.headers.get("X-Twilio-Signature", "")
    if not settings.twilio_auth_token or not RequestValidator(settings.twilio_auth_token).validate(callback_url, params, signature):
        raise HTTPException(403, detail="Invalid Twilio signature")


def signer():
    return URLSafeTimedSerializer(settings.twilio_auth_token, salt="ai-sales-media-v1")


def instructions(lead: Lead) -> str:
    name = lead.contact_name or "the customer"
    return (
        f"You are Alex, an AI sales assistant working for {settings.company_name}. "
        f"You are speaking to {name} at {lead.company_name}. "
        "At the start, disclose you are an AI calling on behalf of the company and "
        "ask whether this is a good time. If not, politely finish promptly. "
        "You are here to listen, learn about their needs, answer clearly, explain "
        "verified benefits, and offer a human sales follow-up when relevant. "
        "Use ONLY these approved company facts, offerings and prices: "
        f"{settings.approved_sales_facts}. "
        "Never invent prices, discounts, guarantees, business hours, availability, "
        "case studies, integration details, or contract terms. "
        "Never request card numbers, passwords, or other sensitive information. "
        "Never pretend a purchase, appointment or signed agreement is completed. "
        "If the customer requests no further calls, invoke mark_do_not_call immediately, "
        "acknowledge their choice, and finish the call. "
        "When the customer explicitly asks to be contacted by sales, call "
        "request_human_followup; do not promise an actual booking. "
        "Speak in short, natural turns. Do not pressure or manipulate the listener."
    )


TOOLS = [
    {
        "type": "function", "name": "request_human_followup",
        "description": "Record that this prospect explicitly agreed to a human sales follow-up. Never book a meeting.",
        "parameters": {"type": "object", "properties": {
            "summary": {"type": "string", "description": "Concise non-sensitive description of the customer's interest"}
        }, "required": ["summary"], "additionalProperties": False},
    },
    {
        "type": "function", "name": "mark_do_not_call",
        "description": "Immediately suppress future calls when the prospect asks to stop or opts out.",
        "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def save_outcome(lead_id: int, call_sid: str, outcome: str, summary: str = ""):
    with SessionLocal() as db:
        lead = db.get(Lead, lead_id)
        if not lead:
            return
        if outcome == "do_not_call":
            lead.do_not_call = True
            lead.status = "do_not_call"
        elif outcome == "human_followup_requested" and not lead.do_not_call:
            lead.status = "followup_requested"
        call = db.query(Call).filter(Call.provider_session_id == call_sid).first()
        if call:
            call.outcome = outcome
            if summary:
                call.summary = summary[:1000]
        db.commit()


@router.post("/call/{lead_id}", status_code=202)
async def dial_one_lead(
    lead_id: int, x_admin_key: str | None = Header(default=None), db: Session = Depends(get_db)
):
    """Single consented call only. No bulk dialer, campaign, or auto-retry."""
    require_config()
    if not settings.enable_outbound_calls:
        raise HTTPException(403, detail="Outbound calls are disabled. Set ENABLE_OUTBOUND_CALLS=true only after compliance review.")
    if not x_admin_key or not hmac.compare_digest(x_admin_key, settings.sales_admin_key):
        raise HTTPException(401, detail="Invalid admin key")
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(404, detail="Lead not found")
    if lead.do_not_call or lead.consent_status != "granted" or not lead.consent_source:
        raise HTTPException(403, detail="Documented calling consent required; lead may be suppressed")
    if not lead.phone.startswith("+"):
        raise HTTPException(422, detail="Lead phone must be E.164")
    last_call = (db.query(Call).filter(Call.lead_id == lead.id)
                 .order_by(Call.created_at.desc()).first())
    if last_call and last_call.created_at:
        recent = last_call.created_at.replace(tzinfo=timezone.utc) if last_call.created_at.tzinfo is None else last_call.created_at
        if datetime.now(timezone.utc) - recent < timedelta(hours=24):
            raise HTTPException(409, detail="One-call-per-lead 24-hour cooldown")

    def place_call():
        return Client(settings.twilio_account_sid, settings.twilio_auth_token).calls.create(
            to=lead.phone, from_=settings.twilio_phone_number,
            url=public_url("/twilio/voice?" + urlencode({"lead_id": lead.id})),
            method="POST",
            status_callback=public_url("/twilio/status"),
            status_callback_method="POST",
            status_callback_event=["initiated", "ringing", "answered", "completed"],
        )

    try:
        result = await run_in_threadpool(place_call)
    except Exception:
        log.exception("Twilio call request failed for lead %s", lead_id)
        raise HTTPException(502, detail="Twilio call request failed; check account, number and permissions")
    call = Call(lead_id=lead.id, provider_session_id=result.sid, status="requested")
    db.add(call)
    lead.status = "call_requested"
    db.commit()
    return {"call_id": call.id, "provider_sid": result.sid, "status": "requested",
            "note": "Twilio accepted a request, not proof the customer answered or purchased."}


@router.post("/voice")
async def twilio_voice(request: Request, lead_id: int, db: Session = Depends(get_db)):
    params = dict(await request.form())
    validate_twilio(request, params, public_url("/twilio/voice?" + urlencode({"lead_id": lead_id})))
    lead = db.get(Lead, lead_id)
    if not lead or lead.do_not_call or lead.consent_status != "granted":
        raise HTTPException(403, detail="Lead is not eligible")
    token = signer().dumps({"lead_id": lead_id})
    twiml = VoiceResponse()
    connection = Connect()
    stream = Stream(url=public_url("/twilio/media").replace("https://", "wss://", 1))
    stream.parameter(name="auth", value=token)
    connection.append(stream)
    twiml.append(connection)
    return Response(str(twiml), media_type="application/xml")


@router.post("/status")
async def twilio_status(request: Request):
    params = dict(await request.form())
    validate_twilio(request, params, public_url("/twilio/status"))
    call_sid, status = params.get("CallSid", ""), params.get("CallStatus", "")
    if call_sid:
        with SessionLocal() as db:
            call = db.query(Call).filter(Call.provider_session_id == call_sid).first()
            if call:
                call.status = status[:40]
                db.commit()
    return Response(status_code=204)


@router.websocket("/media")
async def twilio_media(websocket: WebSocket):
    # Twilio streams send a connected event, then a start event with CustomParameters.
    await websocket.accept()
    if not settings.twilio_auth_token or not settings.openai_api_key or not settings.approved_sales_facts:
        await websocket.close(code=1008)
        return
    try:
        start = None
        for _ in range(4):
            event = await asyncio.wait_for(websocket.receive_json(), timeout=10)
            if event.get("event") == "start":
                start = event
                break
        if not start:
            raise ValueError("Missing stream start")
        token = start.get("start", {}).get("customParameters", {}).get("auth", "")
        signed = signer().loads(token, max_age=900)
        lead_id = int(signed["lead_id"])
        stream_sid = start["start"]["streamSid"]
        call_sid = start["start"].get("callSid", "")
        with SessionLocal() as db:
            lead = db.get(Lead, lead_id)
            if not lead or lead.do_not_call or lead.consent_status != "granted":
                raise ValueError("Lead is not eligible")
            prompt = instructions(lead)
    except (ValueError, KeyError, BadSignature, SignatureExpired, asyncio.TimeoutError):
        await websocket.close(code=1008)
        return

    try:
        async with connect(
            f"wss://api.openai.com/v1/realtime?model={settings.sales_model}",
            additional_headers={"Authorization": "Bearer " + settings.openai_api_key},
            open_timeout=15, max_size=8 * 1024 * 1024,
        ) as ai:
            await ai.send(json.dumps({
                "type": "session.update",
                "session": {
                    "type": "realtime", "instructions": prompt,
                    "audio": {
                        "input": {"format": {"type": "audio/pcmu"},
                                  "turn_detection": {"type": "server_vad", "create_response": True,
                                                     "interrupt_response": True}},
                        "output": {"format": {"type": "audio/pcmu"}, "voice": settings.sales_voice},
                    },
                    "tools": TOOLS,
                },
            }))
            ai_started = asyncio.Event()
            response_active = False

            async def twilio_to_ai():
                await ai_started.wait()
                while True:
                    raw = await websocket.receive_json()
                    kind = raw.get("event")
                    if kind == "stop":
                        return
                    if kind == "media":
                        chunk = raw.get("media", {}).get("payload")
                        if chunk:
                            await ai.send(json.dumps({"type": "input_audio_buffer.append", "audio": chunk}))

            async def ai_to_twilio():
                nonlocal response_active
                async for raw in ai:
                    event = json.loads(raw)
                    kind = event.get("type")
                    if kind == "session.updated":
                        if not ai_started.is_set():
                            ai_started.set()
                            await ai.send(json.dumps({"type": "response.create",
                                "response": {"instructions": "Introduce yourself, disclose you are an AI assistant, and ask permission to continue."}}))
                    elif kind == "response.created":
                        response_active = True
                    elif kind == "response.done":
                        response_active = False
                        for item in event.get("response", {}).get("output", []):
                            if item.get("type") != "function_call":
                                continue
                            outcome = item.get("name", "")
                            try:
                                arguments = json.loads(item.get("arguments") or "{}")
                            except json.JSONDecodeError:
                                arguments = {}
                            if outcome == "mark_do_not_call":
                                save_outcome(lead_id, call_sid, "do_not_call")
                                result = {"ok": True, "suppressed": True}
                            elif outcome == "request_human_followup":
                                save_outcome(lead_id, call_sid, "human_followup_requested",
                                             str(arguments.get("summary", ""))[:1000])
                                result = {"ok": True, "note": "Sales team follow-up requested, not scheduled"}
                            else:
                                result = {"ok": False}
                            await ai.send(json.dumps({"type": "conversation.item.create",
                                "item": {"type": "function_call_output", "call_id": item["call_id"],
                                         "output": json.dumps(result)}}))
                            await ai.send(json.dumps({"type": "response.create"}))
                    elif kind == "response.output_audio.delta" and event.get("delta"):
                        await websocket.send_json({
                            "event": "media", "streamSid": stream_sid,
                            "media": {"payload": event["delta"]},
                        })
                    elif kind == "input_audio_buffer.speech_started" and response_active:
                        # Flush queued AI speech when the customer interrupts.
                        await websocket.send_json({"event": "clear", "streamSid": stream_sid})
                        await ai.send(json.dumps({"type": "response.cancel"}))
                    elif kind == "error":
                        log.warning("Realtime session event error: %s", event.get("error", {}).get("code", "unknown"))

            tasks = [asyncio.create_task(twilio_to_ai()), asyncio.create_task(ai_to_twilio())]
            try:
                done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED, timeout=900)
                for task in done:
                    if task.exception():
                        raise task.exception()
            finally:
                for task in tasks:
                    task.cancel()
                await asyncio.gather(*tasks, return_exceptions=True)
    except Exception:
        log.exception("Two-way audio bridge stopped (call %s)", call_sid)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass
