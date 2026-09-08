from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    POSTGRES_DSN: str = "postgresql://campaign:campaign_secret@localhost:5432/campaign_db"
    API_KEY: str = "default_dev_key"
    REDIS_URL: str = "redis://localhost:6379/0"
    MILVUS_HOST: str = "localhost"
    MILVUS_PORT: int = 19530
    MILVUS_COLLECTION_NAME: str = "historical_campaigns"
    COUCHDB_URL: str = "http://admin:admin_secret@localhost:5984"

    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    LLM_PROVIDER: str = "openai"  # 'openai', 'anthropic', or 'gemini'
    LLM_MODEL_NAME: str = "gpt-4o"

    # Meta Ads
    META_ACCESS_TOKEN: str = ""
    META_AD_ACCOUNT_ID: str = ""

    # Google Ads
    GOOGLE_ADS_DEVELOPER_TOKEN: str = ""
    GOOGLE_ADS_CLIENT_ID: str = ""
    GOOGLE_ADS_CLIENT_SECRET: str = ""
    GOOGLE_ADS_REFRESH_TOKEN: str = ""
    GOOGLE_ADS_CUSTOMER_ID: str = ""

    # SendGrid (Email Marketing)
    SENDGRID_API_KEY: str = ""
    CAMPAIGN_FROM_EMAIL: str = ""

    # Klaviyo (Lifecycle / Retention)
    KLAVIYO_API_KEY: str = ""

    # Google Custom Search (Dynamic Web Research)
    GOOGLE_SEARCH_API_KEY: str = ""
    GOOGLE_SEARCH_ENGINE_ID: str = ""

    SUFFICIENCY_THRESHOLD: float = 0.75


settings = Settings()
