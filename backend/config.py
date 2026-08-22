import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "AI Code Sandbox"
    APP_SUBTITLE: str = "AI-Powered Code Execution & Autonomous Debugging"
    VERSION: str = "1.0.0"
    
    # AI Config
    AI_API_KEY: str = os.getenv("AI_API_KEY", os.getenv("GEMINI_API_KEY", ""))
    AI_MODEL: str = os.getenv("AI_MODEL", "gemini-2.5-flash")
    
    # Sandbox Config
    SANDBOX_TIMEOUT: int = int(os.getenv("SANDBOX_TIMEOUT", "10"))
    MAX_DEBUG_ATTEMPTS: int = int(os.getenv("MAX_DEBUG_ATTEMPTS", "3"))
    
    # Database Config
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./sandbox.db")
    
    # CORS Config
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        "*"
    ]

settings = Settings()
