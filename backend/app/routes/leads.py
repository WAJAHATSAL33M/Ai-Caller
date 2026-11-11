import hmac
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import Lead
from app.schemas import LeadCreate, LeadRead

def require_admin(x_admin_key: str | None = Header(default=None)):
    # The lead API contains sensitive customer information.
    if not settings.sales_admin_key or not x_admin_key or not hmac.compare_digest(x_admin_key, settings.sales_admin_key):
        raise HTTPException(status_code=401, detail="Admin access required")

router = APIRouter(prefix="/leads", tags=["leads"], dependencies=[Depends(require_admin)])

@router.post("", response_model=LeadRead, status_code=201)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)):
    lead = Lead(**payload.model_dump())
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return lead

@router.get("", response_model=list[LeadRead])
def list_leads(db: Session = Depends(get_db)):
    return db.query(Lead).order_by(Lead.created_at.desc()).limit(500).all()

@router.get("/{lead_id}", response_model=LeadRead)
def get_lead(lead_id: int, db: Session = Depends(get_db)):
    lead = db.get(Lead, lead_id)
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    return lead
