from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    PROJECT_NAME: str = "Tax Processing Agent"
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./tax_app.db"
    
    DOCUMENTINTELLIGENCE_ENDPOINT: str
    DOCUMENTINTELLIGENCE_API_KEY: str
    
    OPENAI_API_KEY: str
    OPENAI_MODEL: str = "gpt-5-mini"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

