from pydantic import computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    POSTGRES_HOST: str = "db"
    POSTGRES_PORT: int = 5432
    SECRET_KEY: str

    EXPIRE_TIME: int = 60
    INVITE_EXPIRE_TIME: int = 5

    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION_NAME: str
    AWS_SESSION_TOKEN: str
    S3_BUCKET_NAME: str
    S3_EXTERNAL_URL: str

    MINIO_ROOT_USER: str
    MINIO_ROOT_PASSWORD: str

    DEBUG_MODE: bool = True
    LOG_LEVEL: str = "INFO"

    MAX_PROJECT_SIZE_BYTES: int = 50 * 1024 * 1024

    @computed_field
    @property
    def DATABASE_URL(self) -> str:
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    model_config = SettingsConfigDict(env_file=".env")


settings = Settings()
