import os
from motor.motor_asyncio import AsyncIOMotorClient
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "sv_langgraph")
client = None
db = None
async def init_db():
    global client, db
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    await db.runs.create_index([("kind",1),("_id",-1)])
    await db.web_cache.create_index([("url",1)], unique=True)
