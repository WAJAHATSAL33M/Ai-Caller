import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Call, Lead
from app.services.live_calls import start_sales_call

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/calls", tags=["calls"])

@router.post("/start/{lead_id}", status_code=202)
async def start_call(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if lead.do_not_call:
        raise HTTPException(status_code=403, detail="Lead is on the do-not-call list")
    if lead.consent_status != "granted" or not lead.consent_source:
        raise HTTPException(status_code=403, detail="Documented calling authorization is required before dialing")
    try:
        result = await start_sales_call(lead)
    except Exception:
        logger.exception("Unable to create Live SIP session for lead_id=%s", lead_id)
        raise HTTPException(status_code=502, detail="Call session could not be created")
    session = result.get("session") or {}
    session_id = session.get("id") or result.get("id")
    call = Call(lead_id=lead.id, provider_session_id=session_id, status="session_created")
    db.add(call)
    lead.status = "call_requested"
    db.commit()
    db.refresh(call)
    return {"call_id": call.id, "session_id": session_id, "status": call.status,
            "note": "Session creation accepted; this does not confirm answer or completion."}
