import re, numpy as np, hashlib
TOKEN = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]{2,}")
def keywords(text: str, k: int = 60):
    words = [w.lower() for w in TOKEN.findall(text or "")]
    from collections import Counter
    return [w for w,_ in Counter(words).most_common(k)]
def embed(text: str, dim: int = 128)->np.ndarray:
    v = np.zeros(dim, dtype=float)
    for w in set(keywords(text, 512)):
        h = int(hashlib.blake2b(w.encode(), digest_size=8).hexdigest(), 16)
        v[h % dim] += 1.0
    n = np.linalg.norm(v) or 1.0
    return v / n
def cosine(a: np.ndarray, b: np.ndarray)->float:
    return float(np.dot(a,b)/((np.linalg.norm(a) or 1.0)*(np.linalg.norm(b) or 1.0)))
