from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_CONNECTION_STRING: str
    JWT_SECRET: str
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    AGENT_JWT_SECRET: str = ""
    AGENT_JWT_EXPIRE_MINUTES: int = 30
    AGENT_JWT_AUDIENCE: str = "agent-service"
    GOOGLE_OAUTH_CLIENT_ID: str
    GOOGLE_OAUTH_CLIENT_SECRET: str
    GOOGLE_OAUTH_REDIRECT_URI: str
    REFRESH_TOKEN_EXPIRE_DAYS: int = 15
    REFRESH_TOKEN_COOKIE_NAME: str = "refresh_token"
    REFRESH_TOKEN_COOKIE_SECURE: bool = False
    REFRESH_TOKEN_COOKIE_SAMESITE: str = "lax"
    DEMO_REQUEST_TIMEOUT_SECONDS: int = 10
    FRONTEND_APP_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
