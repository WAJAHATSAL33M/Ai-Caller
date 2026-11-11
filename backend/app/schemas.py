from pydantic import BaseModel, ConfigDict, Field

class LeadCreate(BaseModel):
    company_name: str = Field(min_length=1, max_length=200)
    contact_name: str | None = None
    phone: str = Field(pattern=r"^\+[1-9]\d{7,14}$", description="E.164 phone number")
    email: str | None = None
    industry: str | None = None
    country: str | None = Field(default=None, min_length=2, max_length=2)
    timezone: str | None = None
    consent_status: str = "unverified"
    consent_source: str | None = None
    do_not_call: bool = False

class LeadRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    company_name: str
    contact_name: str | None
    phone: str
    email: str | None
    industry: str | None
    country: str | None
    timezone: str | None
    consent_status: str
    do_not_call: bool
    status: str
