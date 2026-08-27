"""
core/pexels.py — Búsqueda de imágenes en Internet basada en DuckDuckGo (DDGS) con soporte de paginación (40 por página).
"""
import json
import re
import ssl
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
    """Cliente de búsqueda de imágenes desde Internet basado en DuckDuckGo con paginación."""

    @staticmethod
    def search_photos(query: str, source: str = "DuckDuckGo", is_transparent: bool = False, page: int = 1, per_page: int = 40) -> list:
        if not query or not query.strip():
            return []

        search_q = query.strip()
        type_filter = "transparent" if is_transparent else None
        photos = []

        # 1. Usar paquete duckduckgo_search / ddgs si está instalado en el entorno Python
        if HAS_DDGS_PKG:
            try:
                with DDGS() as ddgs:
                    try:
                        results = list(ddgs.images(
                            query=search_q,
                            region="wt-wt",
                            safesearch="moderate",
                            page=page,
                            max_results=per_page,
                            type_image=type_filter
                        ))
                    except TypeError:
                        results = list(ddgs.images(
                            keywords=search_q,
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
                                "width": r.get("width", 800),
                                "height": r.get("height", 600)
                            })
            except Exception as e:
                print(f"[DDGS Package Error]: {e}")

        # 2. Fallback de DuckDuckGo embebido con soporte de página
        if not photos:
            photos = PexelsAPIClient._search_ddg_embedded(search_q, is_transparent, page, per_page)

        # 3. Fallback adicional a Wikimedia Commons
        if not photos:
            photos = PexelsAPIClient._search_wikimedia(search_q, is_transparent, page, per_page)

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
        except Exception as e:
            print(f"[DDG Embedded] VQD error: {e}")

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
                                    "width": res.get("width", 800),
                                    "height": res.get("height", 600)
                                })
            except Exception as e:
                print(f"[DDG Embedded] i.js error: {e}")

        return photos

    @staticmethod
    def _search_wikimedia(query: str, is_transparent: bool, page: int, per_page: int) -> list:
        search_term = f"{query} png" if is_transparent else query
        encoded_q = urllib.parse.quote(search_term)
        offset = (page - 1) * per_page
        url = (
            "https://commons.wikimedia.org/w/api.php?"
            f"action=query&generator=search&gsrsearch={encoded_q}&gsrlimit={per_page}&gsroffset={offset}"
            "&prop=imageinfo&iiprop=url|size&format=json"
        )
        headers = {"User-Agent": "PaintNotNet/1.0 (https://paintnotnet.org)"}
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
                                    "width": imageinfo[0].get("width", 800),
                                    "height": imageinfo[0].get("height", 600)
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
            "Referer": "https://duckduckgo.com/"
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
