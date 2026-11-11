from fastapi import FastAPI
from app.database import Base, engine
from app.routes import calls, leads, twilio_calls

app = FastAPI(title="AI Sales Caller API", version="0.2.0")

@app.on_event("startup")
def startup():
    # Local starter only. Production deployments need Alembic migrations.
    Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

app.include_router(leads.router)
app.include_router(calls.router)
app.include_router(twilio_calls.router)
