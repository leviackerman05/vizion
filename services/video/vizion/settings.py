from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    app_role: str = "web"
    database_url: str = "sqlite:///./data/vizion.db"
    public_url: str = "http://localhost:8080"
    data_dir: Path = Path("data")
    web_dist: Path = Path("apps/web/dist")
    groq_api_key: str = ""
    groq_model: str = "openai/gpt-oss-120b"
    gemini_api_key: str = ""
    gemini_model: str = "gemini-3.5-flash-lite"
    llm_provider: str = "groq"
    tts_provider: str = "auto"
    piper_model: str = "/opt/piper/en_US-ljspeech-high.onnx"
    s3_endpoint_url: str = ""
    s3_access_key_id: str = ""
    s3_secret_access_key: str = ""
    s3_bucket: str = ""
    s3_region: str = "auto"
    s3_addressing_style: str = "virtual"
    daily_project_limit: int = 5
    daily_render_limit: int = 10
    global_daily_render_limit: int = 30
    max_pending_jobs: int = 12
    render_height: int = 720
    render_fps: int = 24
    session_days: int = 30
    lease_seconds: int = 180
    poll_seconds: float = 2
    embedded_worker: bool = False
    allow_example_projects: bool = True

    @property
    def production(self) -> bool:
        return self.environment == "production"

    @property
    def cookie_name(self) -> str:
        return "__Host-vizion_session" if self.production else "vizion_session"

    @property
    def sql_url(self) -> str:
        if self.database_url.startswith(("postgres://", "postgresql://")):
            return self.database_url.replace(self.database_url.split(":")[0], "postgresql+psycopg", 1)
        return self.database_url

    def validate_runtime(self):
        self.data_dir.mkdir(parents=True, exist_ok=True)
        if self.production and not self.public_url.startswith("https://"):
            raise ValueError("PUBLIC_URL must be an HTTPS URL in production")
        if self.production and self.database_url.startswith("sqlite"):
            raise ValueError("Production requires a persistent Postgres DATABASE_URL")
        if self.production and not all(
            (self.s3_endpoint_url, self.s3_bucket, self.s3_access_key_id, self.s3_secret_access_key)
        ):
            raise ValueError(
                "Production requires private S3 storage credentials; ephemeral storage is disabled"
            )
        if self.production and self.app_role == "worker":
            key = self.groq_api_key if self.llm_provider == "groq" else self.gemini_api_key
            if not key:
                raise ValueError("Configure the worker's model API key before starting it")
            if self.tts_provider == "piper" and not Path(self.piper_model).is_file():
                raise ValueError("The Piper narration voice is missing from the worker image")


settings = Settings()
