from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_COLLECTION: str = "campaigns"
    POSTGRES_URI: str = "postgresql://postgres:postgres@localhost:5432/campaigns"
    OPENAI_API_KEY: str | None = None

    class Config:
        env_file = ".env"
        env_prefix = "CAMPAIGN_AGENT_"

settings = Settings()
