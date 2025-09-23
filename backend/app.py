from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, HttpUrl, Field
from services.db import init_db, db
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
    await init_db()

@app.get("/api/health")
async def health():
    return {"ok": True, "ts": datetime.now(timezone.utc).isoformat()}

@app.post("/api/similar")
async def similar(req: SimilarVendorsRequest):
    try:
        result = await run_graph(req.dict())
        doc = {"kind":"similar_vendors","input": req.dict(),"output": result,"created_at": datetime.now(timezone.utc).isoformat()}
        await db.runs.insert_one(doc)
        result["_id"] = str(doc.get("_id",""))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/runs")
async def list_runs(limit: int = 20):
    out = []
    async for r in db.runs.find({"kind":"similar_vendors"}).sort("_id", -1).limit(limit):
        r["id"] = str(r.pop("_id"))
        out.append(r)
    return out
