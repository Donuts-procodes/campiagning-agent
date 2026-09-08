
import redis.asyncio as redis
from pymilvus import MilvusClient

from src.core.config import settings


def get_redis_client() -> redis.Redis:
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_milvus_client() -> MilvusClient:
    return MilvusClient(uri=f"http://{settings.MILVUS_HOST}:{settings.MILVUS_PORT}")

