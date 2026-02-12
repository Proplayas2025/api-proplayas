from pydantic_settings import BaseSettings
from typing import List
import os

class Settings(BaseSettings):
    PROJECT_NAME: str = "Proplayas API"
    VERSION: str = "1.0.0"
    API_V1_STR: str = "/api"
    
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "postgresql://proplayas:proplayas@localhost:5432/proplayas_db"
    )
    DATABASE_ECHO: bool = os.getenv("DATABASE_ECHO", "False") == "True"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8080",
        "http://proplayas.org",
        "https://proplayas.org"
    ]
    
    # Email configuration
    SMTP_HOST: str = os.getenv("SMTP_HOST", "mailhog")  # mailhog service in docker, localhost for local dev
    SMTP_PORT: int = int(os.getenv("SMTP_PORT", "1025"))  # 1025 for MailHog, 587 for production
    SMTP_USER: str = os.getenv("SMTP_USER", "")  # Empty for MailHog
    SMTP_PASSWORD: str = os.getenv("SMTP_PASSWORD", "")  # Empty for MailHog
    FROM_EMAIL: str = os.getenv("FROM_EMAIL", "noreply@proplayas.org")
    FROM_NAME: str = os.getenv("FROM_NAME", "Proplayas")
    
    # Frontend URL for email links
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    # Environment detection
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")  # development, staging, production
    
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "storage/uploads")
    
    class Config:
        case_sensitive = True

settings = Settings()
