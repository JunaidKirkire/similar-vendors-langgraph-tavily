import os
from typing import List
from openai import OpenAI
def plan_queries(seed_name: str, domain: str, text: str, manufacturing: bool = True) -> List[str]:
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        base = [f"competitors of {seed_name}", f"alternatives to {seed_name}", f"{domain} competitors"]
        if manufacturing:
            base += ["cnc machining suppliers", "manufacturing marketplace competitors", f"contract manufacturers similar to {seed_name}"]
        return base
    client = OpenAI()
    sys = "You are a research planner. Return 6 short web search queries (no numbering) to find competitors and close alternatives for the given company. Include 2 queries that target manufacturing-specific phrases if relevant."
    prompt = f"Company: {seed_name} ({domain})\nWebsite text (first 500 chars): {text[:500]}\nReturn 6 queries, one per line."
    r = client.chat.completions.create(model=os.getenv("OPENAI_MODEL","gpt-4o-mini"),
        messages=[{"role":"system","content":sys},{"role":"user","content":prompt}], temperature=0.2)
    lines = [l.strip("-* •\t ") for l in (r.choices[0].message.content or "").splitlines() if l.strip()]
    return lines[:6] or [f"competitors of {seed_name}", f"{domain} competitors", f"alternatives to {seed_name}"]
