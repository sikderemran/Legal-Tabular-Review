from pydantic_settings import BaseSettings
from typing import List
from pathlib import Path

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Legal Tabular Review"
    
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    DEBUG: bool = True
    
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000"
    ]
    
    MAX_UPLOAD_SIZE: int = 50 * 1024 * 1024  
    UPLOAD_DIR: Path = Path("./uploads")
    ALLOWED_EXTENSIONS: List[str] = [".pdf", ".docx", ".txt"]
    

    DEFAULT_FIELDS: List[str] = [
        "effective_date",
        "parties",
        "termination",
        "jurisdiction",
        "payment_terms",
        "governing_law",
        "confidentiality",
        "indemnification",
        "warranties",
        "liability"
    ]
    
    CONFIDENCE_THRESHOLD: float = 0.6
    MIN_CONFIDENCE: float = 0.3
    
    DATABASE_URL: str = "sqlite:///./legal_review.db"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()