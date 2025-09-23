from typing import TypedDict, List, Dict, Any
from langgraph.graph import StateGraph, END
from services.web import fetch
from services.parse import clean_text, title_of, domain_of
from services.nlp import keywords, embed, cosine
from services.tavily import t_search, t_extract, t_map, t_crawl
from services.taxonomy import tag_taxonomy, extract_capabilities
from services.openai_llm import plan_queries

class State(TypedDict, total=False):
    input: Dict[str, Any]
    seed: Dict[str, Any]
    queries: List[str]
    raw_candidates: List[Dict[str, Any]]
    evidence: Dict[str, List[Dict[str, Any]]]
    ranked: List[Dict[str, Any]]
    trace: List[Dict[str, Any]]

def add_trace(state: State, step: str, detail: Dict[str, Any]):
    state.setdefault("trace", []).append({"step": step, "detail": detail})

async def seed_analyzer(state: State) -> State:
    url = state["input"]["url"]
    html = await fetch(url)
    text = clean_text(html)
    seed = {"url": url,"domain": domain_of(url),"name": title_of(html) or domain_of(url),"summary": text[:900],"keywords": keywords(text, 60)}
    seed |= tag_taxonomy(text)
    add_trace(state, "seed_analyzer", {"seed_name": seed["name"], "domain": seed["domain"], "verticals": seed.get("verticals", [])})
    state["seed"] = seed
    return state

async def planner(state: State) -> State:
    seed = state["seed"]
    use_llm = state["input"].get("use_llm", True)
    qs = plan_queries(seed.get("name",""), seed["domain"], seed.get("summary",""), manufacturing=True) if use_llm else [
        f"competitors of {seed['name']}", f"alternatives to {seed['name']}", f"{seed['domain']} competitors",
        f"{', '.join(seed.get('capabilities', [])[:2])} manufacturers"
    ]
    state["queries"] = qs
    add_trace(state, "planner", {"queries": qs})
    return state

async def discovery(state: State) -> State:
    qs = state["queries"]
    maxc = int(state["input"].get("max_candidates", 25))
    results = await t_search(qs, max_results=maxc)
    seen = set([state["seed"]["domain"]])
    cands = []
    for r in results:
        d = domain_of(r.get("url",""))
        if not d or d in seen: continue
        seen.add(d)
        cands.append({"url": r["url"], "domain": d, "title": r.get("title",""), "snippet": r.get("snippet",""), "source": "tavily.search"})
    state["raw_candidates"] = cands
    add_trace(state, "discovery", {"num_candidates": len(cands)})
    return state

async def enrichment(state: State) -> State:
    urls = []
    for c in state["raw_candidates"][:state["input"].get("max_candidates",25)]:
        urls.append(c["url"])
        try:
            mp = await t_map(c["url"])
            urls.extend(mp.get("links", [])[:3])
        except Exception:
            pass
    urls = urls[:50]
    ex = await t_extract(urls)
    cr = await t_crawl(urls[:20])
    evidence = {}
    for b in (ex.get("results", []) + cr.get("results", [])):
        d = domain_of(b.get("url",""))
        evidence.setdefault(d, []).append({"url": b.get("url",""),"title": b.get("title",""),"text": (b.get("content") or b.get("raw_content") or "")[:800]})
    state["evidence"] = evidence
    add_trace(state, "enrichment", {"domains_with_evidence": len(evidence)})
    return state

async def scoring(state: State) -> State:
    seed = state["seed"]
    v_seed = embed(" ".join([seed.get("summary",""), " ".join(seed.get("keywords",[])), " ".join(seed.get("capabilities",[]))]))
    seed_caps = set([s.lower() for s in seed.get("capabilities", [])])
    ranked = []
    for c in state["raw_candidates"]:
        ev = state["evidence"].get(c["domain"], [])
        text = " ".join([e.get("title","")+" "+e.get("text","") for e in ev]) or (c.get("title","")+" "+c.get("snippet",""))
        v_c = embed(text)
        sim = cosine(v_seed, v_c)
        caps = set([s.lower() for s in extract_capabilities(text)])
        cap_overlap = len(seed_caps & caps) / (len(seed_caps | caps) or 1)
        from services.nlp import keywords as kw
        kw_overlap = len(set(seed.get("keywords",[])[:60]) & set(kw(text,60))) / (len(set(seed.get("keywords",[])[:60]) | set(kw(text,60))) or 1)
        score = 0.5*sim + 0.3*cap_overlap + 0.2*kw_overlap
        ranked.append({**c, "score": round(float(score),4), "capability_overlap": round(float(cap_overlap),4), "evidence": ev[:3]})
    ranked.sort(key=lambda x: x["score"], reverse=True)
    state["ranked"] = ranked
    add_trace(state, "scoring", {"top_score": ranked[0]["score"] if ranked else 0.0})
    return state

def build_graph():
    g = StateGraph(State)
    g.add_node("seed_analyzer", seed_analyzer)
    g.add_node("planner", planner)
    g.add_node("discovery", discovery)
    g.add_node("enrichment", enrichment)
    g.add_node("scoring", scoring)
    g.set_entry_point("seed_analyzer")
    g.add_edge("seed_analyzer","planner")
    g.add_edge("planner","discovery")
    g.add_edge("discovery","enrichment")
    g.add_edge("enrichment","scoring")
    g.add_edge("scoring", END)
    return g.compile()

graph = build_graph()
async def run_graph(input_dict: dict):
    state = {"input": input_dict}
    result = await graph.ainvoke(state)
    return {"seed": result.get("seed", {}), "results": result.get("ranked", []), "trace": result.get("trace", [])}
