from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from services import db as db_service
from graph.runner import run_graph
from datetime import datetime, timezone

app = FastAPI(title="Similar Vendors — LangGraph + Tavily + MongoDB Atlas")

class SimilarVendorsRequest(BaseModel):
    url: HttpUrl
    max_candidates: int = Field(25, ge=5, le=50)
    simulate: bool = False
    use_llm: bool = True

@app.on_event("startup")
async def startup():
    await db_service.init_db()

@app.get("/api/health")
async def health():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}

@app.post("/api/similar")
async def similar(req: SimilarVendorsRequest):
    payload = req.model_dump(mode="json")
    try:
        result = await run_graph(payload)
        doc = {"kind":"similar_vendors","input": payload,"output": result,"created_at": datetime.now(timezone.utc).isoformat()}
        if db_service.db is None:
            raise RuntimeError("Database not initialized")
        await db_service.db.runs.insert_one(doc)
        result["_id"] = str(doc.get("_id",""))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runs")
async def list_runs(limit: int = 20):
    out = []
    if db_service.db is None:
        raise RuntimeError("Database not initialized")
    async for r in db_service.db.runs.find({"kind":"similar_vendors"}).sort("_id", -1).limit(limit):
        r["id"] = str(r.pop("_id"))
        out.append(r)
    return out
