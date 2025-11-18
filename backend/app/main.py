from fastapi import FastAPI
from app.core.config import settings
from app.db.session import engine, Base
from app.api.endpoints import router as api_router

# Create tables (for dev only, use Alembic for prod)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tax Processing Agent",
    description="AI-powered tax return preparation agent",
    version="0.1.0",
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Tax Processing Agent API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.ENV}
