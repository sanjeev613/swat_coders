import os
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

class Settings:
    PROJECT_NAME: str = "AgroSense"
    PROJECT_VERSION: str = "1.0.0"
    SECRET_KEY: str = os.getenv("SECRET_KEY", "agrosense_super_secret_jwt_key_development_2026_change_in_production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    
    # Defaults to local SQLite database, or uses PostgreSQL / Supabase if DATABASE_URL is set
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./agrosense.db")

settings = Settings()
