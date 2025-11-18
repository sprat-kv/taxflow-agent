from fastapi import FastAPI
from app.core.config import settings

app = FastAPI(
    title="Tax Processing Agent",
    description="AI-powered tax return preparation agent",
    version="0.1.0",
)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Tax Processing Agent API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.ENV}

