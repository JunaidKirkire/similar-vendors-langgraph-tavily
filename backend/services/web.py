import httpx
from services.db import db
UA={"User-Agent":"Mozilla/5.0 (SimilarVendors/1.0)"}
async def fetch(url: str, cache: bool = True) -> str:
    if cache:
        doc = await db.web_cache.find_one({"url": url})
        if doc and "html" in doc: return doc["html"]
    async with httpx.AsyncClient(timeout=30, headers=UA) as c:
        r = await c.get(url, follow_redirects=True)
        r.raise_for_status()
        html = r.text
    if cache:
        await db.web_cache.update_one({"url": url},{"$set":{"html":html}}, upsert=True)
    return html
