from pydantic_settings import BaseSettings
from functools import lru_cache

class Settings(BaseSettings):
    groq_api_key: str
    google_application_credentials: str
    google_drive_folder_id: str
    vector_store_path: str = "data/vector_store"
    chunk_size: int = 800
    chunk_overlap: int = 150
    top_k_results: int = 3
    
    class Config:
        env_file = ".env"

@lru_cache()
def get_settings():
    return Settings()