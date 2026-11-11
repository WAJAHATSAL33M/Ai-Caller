from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/calls", tags=["calls"])

@router.post("/start/{lead_id}", status_code=410, deprecated=True)
async def legacy_start_call(lead_id: int):
    # Legacy SIP stub did not attach to a real live audio session and was not authenticated.
    # Deliberately disabled. Use the protected Twilio calling path instead.
    raise HTTPException(status_code=410, detail="Legacy SIP starter disabled. Use POST /twilio/call/{lead_id} with X-Admin-Key after configuring Twilio.")
