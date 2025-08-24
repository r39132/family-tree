from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = Field(default="Family Tree API", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    debug: bool = Field(default=True, alias="DEBUG")

    google_cloud_project: str = Field(..., alias="GOOGLE_CLOUD_PROJECT")
    firestore_database: str = Field(default="(default)", alias="FIRESTORE_DATABASE")

    jwt_secret: str = Field(..., alias="JWT_SECRET")
    jwt_alg: str = Field(default="HS256", alias="JWT_ALG")
    access_token_expire_minutes: int = Field(default=60, alias="ACCESS_TOKEN_EXPIRE_MINUTES")

    smtp_host: str = Field(default="", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str = Field(default="", alias="SMTP_USER")
    smtp_password: str = Field(default="", alias="SMTP_PASSWORD")
    email_from: str = Field(default="noreply@familytree.local", alias="EMAIL_FROM")
    email_from_name: str = Field(default="Family Tree", alias="EMAIL_FROM_NAME")
    use_email_in_dev: bool = Field(default=True, alias="USE_EMAIL_IN_DEV")

    require_invite: bool = Field(default=True, alias="REQUIRE_INVITE")

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
