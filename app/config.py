from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    POSTGRES_DB_HOST: str
    POSTGRES_DB_USER: str
    POSTGRES_DB_PASSWORD: str
    POSTGRES_DB_NAME: str
    POSTGRES_DB_PORT: int

    GEMINI_API_KEY: str
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333

    class Config:
        env_file = ".env"

settings = Settings()
