from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    ENVIRONMENT: str = "development"

    PASSWORD_RESET_REQUESTS_PER_HOUR: int = 3
    LOGIN_ATTEMPTS_PER_HOUR: int = 10
    
    PASSWORD_RESET_TOKEN_EXPIRE_MINUTES: int = 30
    # FRONTEND_URL: list[str] = ["http://localhost:3000","https://funding-frontend-orcin.vercel.app"]
    FRONTEND_URL: str = "https://funding-frontend-orcin.vercel.app"

    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    SENTRY_DSN: str = ""
    # Enable expiry cleanup
    ENABLE_EXPIRY_CLEANUP: bool = False


    class Config:
        env_file = ".env"

settings = Settings()

