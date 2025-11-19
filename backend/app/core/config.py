from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "Tax Processing Agent"
    ENV: str = "dev"
    DATABASE_URL: str = "sqlite:///./tax_app.db"
    
    AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT: str
    AZURE_DOCUMENT_INTELLIGENCE_KEY: str
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

