"""
core/pexels.py — Búsqueda de imágenes en Internet con soporte multinegocio (Bing, Google, DuckDuckGo, Wikimedia, Unsplash).
"""
import json
import re
import ssl
import html
import http.cookiejar
import urllib.request
import urllib.parse

# Intentar importar la librería oficial duckduckgo_search / ddgs
HAS_DDGS_PKG = False
try:
    from duckduckgo_search import DDGS
    HAS_DDGS_PKG = True
except ImportError:
    try:
        from ddgs import DDGS
        HAS_DDGS_PKG = True
    except ImportError:
        HAS_DDGS_PKG = False


def _get_ssl_context():
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except Exception:
        return None


class PexelsAPIClient:
    """Cliente de búsqueda de imágenes desde Internet con múltiples motores y paginación."""

    @staticmethod
    def search_photos(query: str, source: str = "Todas", is_transparent: bool = False, page: int = 1, per_page: int = 40) -> list:
        if not query or not query.strip():
            return []

        search_q = query.strip()
        photos = []

        source_clean = source.lower() if source else "todas"

        engines = []
        if "bing" in source_clean:
            engines = ["bing", "google", "ddg", "wikimedia", "unsplash"]
        elif "google" in source_clean:
            engines = ["google", "bing", "ddg", "wikimedia", "unsplash"]
        elif "duckduckgo" in source_clean or "ddg" in source_clean:
            engines = ["ddg", "bing", "google", "wikimedia", "unsplash"]
        elif "wikimedia" in source_clean:
            engines = ["wikimedia", "bing", "google", "unsplash"]
        elif "unsplash" in source_clean:
            engines = ["unsplash", "bing", "google", "wikimedia"]
        else: # "todas" o automático: probar Bing primero (rápido y estable), luego Google, DDG, etc.
            engines = ["bing", "google", "ddg", "wikimedia", "unsplash"]

        for engine in engines:
            try:
                if engine == "bing":
                    photos = PexelsAPIClient._search_bing(search_q, is_transparent, page, per_page)
                elif engine == "google":
                    photos = PexelsAPIClient._search_google(search_q, is_transparent, page, per_page)
                elif engine == "ddg":
                    if HAS_DDGS_PKG:
                        photos = PexelsAPIClient._search_ddgs_pkg(search_q, is_transparent, page, per_page)
                    if not photos:
                        photos = PexelsAPIClient._search_ddg_embedded(search_q, is_transparent, page, per_page)
                elif engine == "wikimedia":
                    photos = PexelsAPIClient._search_wikimedia(search_q, is_transparent, page, per_page)
                elif engine == "unsplash":
                    photos = PexelsAPIClient._search_unsplash_public(search_q, is_transparent, page, per_page)

                if photos:
                    break
            except Exception:
                pass

        return photos

    @staticmethod
    def _search_bing(query: str, is_transparent: bool, page: int, per_page: int) -> list:
        search_q = f"{query} transparent png" if is_transparent else query
        encoded_q = urllib.parse.quote(search_q)
        first = (page - 1) * per_page + 1
        url = f"https://www.bing.com/images/async?q={encoded_q}&first={first}&count={per_page}"
        if is_transparent:
            url += "&qft=+filterui:photo-transparent"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers=headers)
        photos = []
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                if resp.status == 200:
                    html_text = resp.read().decode("utf-8", errors="ignore")
                    chunks = html_text.split('class="iusc"')
                    for chunk in chunks[1:]:
                        m_match = re.search(r'm="([^"]+)"', chunk)
                        if not m_match:
                            continue
                        try:
                            clean_json = html.unescape(m_match.group(1))
                            data = json.loads(clean_json)
                            murl = data.get("murl")
                            turl = data.get("turl") or murl
                            if not murl:
                                continue
                            w, h = 0, 0
                            try:
                                w = int(data.get("ow") or data.get("w") or 0)
                                h = int(data.get("oh") or data.get("h") or 0)
                            except Exception:
                                pass

                            dim_match = re.search(r'expw=(\d+)&amp;exph=(\d+)|exph=(\d+)&amp;expw=(\d+)|<span class="nowrap">(\d+)&#215;(\d+)</span>', chunk)
                            if dim_match:
                                g = dim_match.groups()
                                if g[0] and g[1]:
                                    w, h = int(g[0]), int(g[1])
                                elif g[2] and g[3]:
                                    h, w = int(g[2]), int(g[3])
                                elif g[4] and g[5]:
                                    w, h = int(g[4]), int(g[5])

                            photos.append({
                                "id": murl,
                                "preview_url": turl,
                                "download_url": murl,
                                "width": w,
                                "height": h
                            })
                        except Exception:
                            pass
                        if len(photos) >= per_page:
                            break
        except Exception:
            pass
        return photos

    @staticmethod
    def _search_google(query: str, is_transparent: bool, page: int, per_page: int) -> list:
        search_q = f"{query} transparent png" if is_transparent else query
        encoded_q = urllib.parse.quote(search_q)
        start = (page - 1) * per_page
        url = f"https://www.google.com/search?q={encoded_q}&tbm=isch&start={start}"
        if is_transparent:
            url += "&tbs=ic:trans"

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers=headers)
        photos = []
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                if resp.status == 200:
                    html_text = resp.read().decode("utf-8", errors="ignore")
                    matches = re.findall(r'\["(https://[^"]+\.(?:jpg|jpeg|png|webp|gif)[^"]*)",\s*(\d+),\s*(\d+)\]', html_text)
                    for u, h_str, w_str in matches:
                        if u not in [p["download_url"] for p in photos]:
                            try:
                                h_val = int(h_str)
                                w_val = int(w_str)
                            except Exception:
                                h_val, w_val = 0, 0
                            photos.append({
                                "id": u,
                                "preview_url": u,
                                "download_url": u,
                                "width": w_val,
                                "height": h_val
                            })
                        if len(photos) >= per_page:
                            break
        except Exception:
            pass
        return photos

    @staticmethod
    def _search_ddgs_pkg(query: str, is_transparent: bool, page: int, per_page: int) -> list:
        photos = []
        try:
            type_filter = "transparent" if is_transparent else None
            with DDGS() as ddgs:
                try:
                    results = list(ddgs.images(
                        query=query,
                        region="wt-wt",
                        safesearch="moderate",
                        page=page,
                        max_results=per_page,
                        type_image=type_filter
                    ))
                except TypeError:
                    results = list(ddgs.images(
                        keywords=query,
                        region="wt-wt",
                        safesearch="moderate",
                        page=page,
                        max_results=per_page,
                        type_image=type_filter
                    ))
                for r in results:
                    thumb = r.get("thumbnail") or r.get("image")
                    large = r.get("image") or thumb
                    if thumb and large:
                        photos.append({
                            "id": large,
                            "preview_url": thumb,
                            "download_url": large,
                            "width": r.get("width") or 0,
                            "height": r.get("height") or 0
                        })
        except Exception:
            pass
        return photos

    @staticmethod
    def _search_ddg_embedded(query: str, is_transparent: bool, page: int, per_page: int) -> list:
        cj = http.cookiejar.CookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

        vqd_url = f"https://duckduckgo.com/?q={urllib.parse.quote(query)}"
        req1 = urllib.request.Request(vqd_url, headers=headers)
        vqd = ""

        try:
            with opener.open(req1, timeout=8) as resp:
                html_text = resp.read().decode("utf-8", errors="ignore")
                patterns = [
                    r'vqd=[\"\']?([^\"\'&\s]+)',
                    r'vqd\s*[:=]\s*[\"\']?([0-9-]+)',
                    r'"vqd"\s*:\s*"([0-9-]+)"',
                    r'vqd=([0-9-]+)'
                ]
                for pat in patterns:
                    m = re.search(pat, html_text)
                    if m:
                        candidate = m.group(1)
                        if "-" in candidate:
                            vqd = candidate
                            break
                        elif not vqd:
                            vqd = candidate
        except Exception:
            pass  # Silenciar errores VQD para evitar spam en consola

        photos = []
        if vqd:
            f_param = "type:transparent" if is_transparent else ""
            img_url = f"https://duckduckgo.com/i.js?l=wt-wt&o=json&q={urllib.parse.quote(query)}&vqd={vqd}&f={f_param}&p={page}"

            img_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "Accept-Language": "es-ES,es;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": f"https://duckduckgo.com/?q={urllib.parse.quote(query)}",
                "X-Requested-With": "XMLHttpRequest",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin"
            }

            req2 = urllib.request.Request(img_url, headers=img_headers)
            try:
                with opener.open(req2, timeout=8) as resp:
                    if resp.status == 200:
                        data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                        for res in data.get("results", [])[:per_page]:
                            thumb = res.get("thumbnail")
                            large = res.get("image")
                            if thumb and large:
                                photos.append({
                                    "id": large,
                                    "preview_url": thumb,
                                    "download_url": large,
                                    "width": res.get("width") or 0,
                                    "height": res.get("height") or 0
                                })
            except Exception:
                pass  # Silenciar errores i.js HTTP 403

        return photos

    @staticmethod
    def _search_wikimedia(query: str, is_transparent: bool, page: int, per_page: int) -> list:
        search_term = f"{query} png" if is_transparent else query
        encoded_q = urllib.parse.quote(search_term)
        offset = (page - 1) * per_page
        url = (
            "https://commons.wikimedia.org/w/api.php?"
            f"action=query&generator=search&gsrsearch={encoded_q}&gsrnamespace=6&gsrlimit={per_page}&gsroffset={offset}"
            "&prop=imageinfo&iiprop=url|size&format=json"
        )
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers=headers)

        photos = []
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    pages = data.get("query", {}).get("pages", {})
                    for page_id, page_info in pages.items():
                        imageinfo = page_info.get("imageinfo", [])
                        if imageinfo:
                            img_url = imageinfo[0].get("url")
                            if img_url:
                                photos.append({
                                    "id": f"wm_{page_id}",
                                    "preview_url": img_url,
                                    "download_url": img_url,
                                    "width": imageinfo[0].get("width") or 0,
                                    "height": imageinfo[0].get("height") or 0
                                })
        except Exception:
            pass

        return photos

    @staticmethod
    def _search_unsplash_public(query: str, is_transparent: bool = False, page: int = 1, per_page: int = 40) -> list:
        clean_q = urllib.parse.quote(query.strip())
        url = f"https://unsplash.com/napi/search/photos?query={clean_q}&page={page}&per_page={per_page}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers=headers)
        photos = []
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    for item in data.get("results", []):
                        urls = item.get("urls", {})
                        small = urls.get("small") or urls.get("thumb")
                        full = urls.get("full") or urls.get("regular") or small
                        if small and full:
                            photos.append({
                                "id": item.get("id", full),
                                "preview_url": small,
                                "download_url": full,
                                "width": item.get("width") or 0,
                                "height": item.get("height") or 0
                            })
        except Exception:
            pass
        return photos

    @staticmethod
    def download_bytes(url: str) -> bytes | None:
        if not url:
            return None
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "Referer": "https://www.google.com/"
        }
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                if response.status == 200:
                    return response.read()
        except Exception:
            pass
        return None
