import re
VERTICALS = {
    "cnc_machining": ["cnc", "turning", "milling", "5-axis", "lathe", "machining"],
    "sheet_metal": ["laser cutting", "sheet metal", "bending", "forming", "press brake"],
    "injection_molding": ["injection molding", "mold", "tooling", "overmold", "mould"],
    "3d_printing": ["3d printing", "additive", "sla", "sls", "fdm", "dmls"],
    "pcba": ["pcba", "smt", "ems", "electronics assembly"],
}
CAPABILITY_PATTERNS = [
    r"cnc (?:turning|milling|machining)",
    r"5[- ]axis",
    r"sheet metal (?:fabrication|forming|bending|cutting)",
    r"(?:laser|plasma|waterjet) cutting",
    r"injection molding",
    r"mold (?:design|making|tooling)",
    r"3d printing|additive (?:manufacturing|production)|sla|sls|fdm|dmls",
    r"surface finish|anodiz(?:e|ing)|powder coat(?:ing)?|plating",
    r"heat treatment|hardening|tempering|anneal(?:ing)?",
]
def extract_capabilities(text: str) -> list[str]:
    txt = (text or "").lower()
    found = []
    for pat in CAPABILITY_PATTERNS:
        for m in re.finditer(pat, txt, flags=re.I):
            found.append(m.group(0).lower())
    return list(dict.fromkeys(found))[:40]
def tag_taxonomy(text: str):
    txt = (text or "").lower()
    verticals = [k.replace("_"," ") for k,kws in VERTICALS.items() if any(w in txt for w in kws)]
    return {"verticals": list(dict.fromkeys(verticals))[:6], "capabilities": extract_capabilities(text)}
