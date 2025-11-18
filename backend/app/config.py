from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    ANTHROPIC_API_KEY: str = ""
    CORS_ORIGINS: list[str] = ["http://localhost:5173"]
    SIMULATION_TTL_SECONDS: int = 3600
    MAX_CONCURRENT_SESSIONS: int = 100
    LOG_LEVEL: str = "INFO"
    DATA_DIR: str = "data"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
