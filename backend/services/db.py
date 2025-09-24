import os

import certifi
from motor.motor_asyncio import AsyncIOMotorClient


MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "sv_langgraph")
client = None
db = None


def _requires_tls_ca(uri: str) -> bool:
    """Return True when the connection string implies TLS is required."""

    uri_lower = uri.lower()
    if uri_lower.startswith("mongodb+srv://"):
        return True

    tls_indicators = ("tls=true", "tls=1", "ssl=true", "ssl=1")
    return any(indicator in uri_lower for indicator in tls_indicators)


async def init_db():
    global client, db

    client_kwargs = {}
    if _requires_tls_ca(MONGO_URI):
        client_kwargs["tlsCAFile"] = certifi.where()

    client = AsyncIOMotorClient(MONGO_URI, **client_kwargs)
    db = client[DB_NAME]
    await db.runs.create_index([("kind", 1), ("_id", -1)])
    await db.web_cache.create_index([("url", 1)], unique=True)
