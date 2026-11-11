import os
from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "DependencyX - Software Dependency Risk Map"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api"

    # Security & Auth
    SECRET_KEY: str = "dependencyx_super_secret_jwt_signing_key_2026_change_in_prod"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 hours

    # Database
    # Default is SQLite for local zero-config execution; seamlessly switch to Azure SQL in production
    DATABASE_URL: str = "sqlite:///./dependencyx.db"

    # Azure Blob Storage (Optional; falls back to local disk storage when blank)
    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER_NAME: str = "dependencyx-manifests"
    LOCAL_STORAGE_DIR: str = "./uploads"

    # OSV API
    OSV_API_URL: str = "https://api.osv.dev/v1/query"
    OSV_BATCH_API_URL: str = "https://api.osv.dev/v1/querybatch"

    # Risk Engine Default Weights
    WEIGHT_SEVERITY: float = 0.45
    WEIGHT_PROPAGATION: float = 0.25
    WEIGHT_DEPTH: float = 0.15
    WEIGHT_CENTRALITY: float = 0.15

    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "*"
    ]

    model_config = {
        "env_file": ".env",
        "extra": "ignore"
    }

settings = Settings()
