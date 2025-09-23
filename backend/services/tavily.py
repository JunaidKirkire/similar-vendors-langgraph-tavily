import os, httpx
BASE = os.getenv("TAVILY_BASE", "https://api.tavily.com")
KEY = os.getenv("TAVILY_API_KEY")
STUB_SEARCH = [
    {"url":"https://www.xometry.com/","title":"Xometry","snippet":"On-demand manufacturing: CNC, 3D printing, injection molding."},
    {"url":"https://www.protolabs.com/","title":"Protolabs","snippet":"Rapid CNC, injection molding, 3D printing."},
    {"url":"https://www.hubs.com/","title":"Hubs","snippet":"CNC machining, sheet metal, injection molding."},
    {"url":"https://www.fictiv.com/","title":"Fictiv","snippet":"Digital manufacturing ecosystem: CNC, 3D printing, injection molding."}
]
async def tavily(endpoint: str, payload: dict):
    if not KEY:
        if endpoint == "search": return {"results": STUB_SEARCH}
        if endpoint == "map":    return {"links": ["https://example.com/services", "https://example.com/capabilities"]}
        if endpoint == "crawl":  return {"results": [{"url":"https://example.com/services","content":"Services: CNC machining, sheet metal"},
                                                     {"url":"https://example.com/capabilities","content":"Capabilities: 5-axis, injection molding"}]}
        if endpoint == "extract":return {"results": [{"url":"https://example.com","raw_content":"Manufacturing company offering CNC and molding."}]}
        return {}
    async with httpx.AsyncClient(timeout=45, headers={"Authorization": f"Bearer {KEY}"}) as c:
        r = await c.post(f"{BASE}/{endpoint}", json=payload)
        r.raise_for_status()
        return r.json()
async def t_search(queries, max_results: int = 25):
    out = []
    for q in queries:
        data = await tavily("search", {"query": q, "max_results": min(max_results, 10)})
        out.extend(data.get("results", []))
    return out[:max_results]
async def t_map(url: str):
    return await tavily("map", {"url": url, "max_depth": 1})
async def t_crawl(urls):
    return await tavily("crawl", {"urls": urls, "include_raw_content": True})
async def t_extract(urls):
    return await tavily("extract", {"urls": urls, "include_raw_content": True})
