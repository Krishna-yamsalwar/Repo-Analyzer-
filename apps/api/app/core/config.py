from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # App
    APP_NAME: str = "RepoPilot AI"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"
    
    # Database
    DATABASE_URL: str = "sqlite+aiosqlite:///./repopilot.db"
    
    # JWT
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Groq
    GROQ_API_KEY: Optional[str] = None
    GROQ_MODEL: str = "llama-3.3-70b-versatile"  # Updated from deprecated 3.1
    
    # ChromaDB (Local Vector Store)
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    CHROMA_COLLECTION_NAME: str = "repopilot"
    
    # Embedding
    EMBEDDING_MODEL: str = "BAAI/bge-small-en-v1.5"
    EMBEDDING_DIMENSION: int = 384
    
    # Repository
    MAX_FILE_SIZE_MB: int = 10
    SUPPORTED_EXTENSIONS: list[str] = [
        ".py", ".js", ".ts", ".tsx", ".jsx", ".go", ".rs", 
        ".java", ".cpp", ".c", ".h", ".md", ".json", ".yaml", ".yml"
    ]
    
    # Git Clone Settings
    CLONE_BASE_DIR: str = "./cloned_repos"
    
    # Neo4j (Graph Database)
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "repopilot123"
    NEO4J_ENABLED: bool = False  # Set to True when Neo4j is running
    
    # Architecture Analysis
    ENABLE_CALL_GRAPH: bool = True
    ENABLE_ENDPOINT_EXTRACTION: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"
    )


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
