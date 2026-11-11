from fastapi import FastAPI
from app.database import Base, engine
from app.routes import calls, leads

app = FastAPI(title="AI Sales Caller API", version="0.1.0")

@app.on_event("startup")
def startup():
    # Local bootstrap only; use Alembic migrations in production.
    Base.metadata.create_all(bind=engine)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

app.include_router(leads.router)
app.include_router(calls.router)
