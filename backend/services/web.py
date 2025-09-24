import httpx
from services import db as db_service
UA={"User-Agent":"Mozilla/5.0 (SimilarVendors/1.0)"}
async def fetch(url: str, cache: bool = True) -> str:
    db_instance = db_service.db
    use_cache = cache and db_instance is not None
    if use_cache:
        doc = await db_instance.web_cache.find_one({"url": url})
        if doc and "html" in doc: return doc["html"]
    async with httpx.AsyncClient(timeout=30, headers=UA) as c:
        r = await c.get(url, follow_redirects=True)
        r.raise_for_status()
        html = r.text
    if use_cache:
        await db_instance.web_cache.update_one({"url": url},{"$set":{"html":html}}, upsert=True)
    return html
