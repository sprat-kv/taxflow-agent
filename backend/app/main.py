from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import engine, Base
from app.api.endpoints import router as api_router

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Tax Processing Agent",
    description="AI-powered tax return preparation agent",
    version="0.1.0",
)

# Configure CORS to allow access from anywhere
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=False,  # Must be False when using allow_origins=["*"]
    allow_methods=["*"],  # Allow all methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to the Tax Processing Agent API"}

@app.get("/health")
def health_check():
    return {"status": "ok", "env": settings.ENV}
