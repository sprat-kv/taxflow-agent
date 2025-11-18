from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tax Processing Agent"
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./tax_app.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

