"""
Application Settings
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    """Application settings"""
    
    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_ADMIN_ID: int
    
    # MongoDB
    MONGODB_URL: str = "mongodb://localhost:27017"
    MONGODB_DB_NAME: str = "educational_platform"
    
    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    
    # Admin
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str
    ADMIN_EMAIL: str
    
    # Payment
    SHAP_CASH_NUMBER: str
    HARAM_NUMBER: str
    
    # App
    DEBUG: bool = False
    HOST: str = "0.0.0.0"
    PORT: int = 8080
    
    # URLs
    BOT_WEBHOOK_URL: Optional[str] = None
    DASHBOARD_URL: str = "http://localhost:8080"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
