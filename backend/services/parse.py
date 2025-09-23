from bs4 import BeautifulSoup
import re, tldextract
def clean_text(html: str)->str:
    soup = BeautifulSoup(html or "", "html.parser")
    for s in soup(["script","style","noscript"]): s.decompose()
    return soup.get_text(" ", strip=True)
def title_of(html: str)->str:
    m = re.search(r"<title>(.*?)</title>", html or "", re.I|re.S)
    return m.group(1).strip() if m else ""
def domain_of(url: str)->str:
    parts = tldextract.extract(url)
    return ".".join([p for p in [parts.domain, parts.suffix] if p])
