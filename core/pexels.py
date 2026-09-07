"""
core/pexels.py — Búsqueda de imágenes en Internet mediante APIs Oficiales (Wikimedia Commons, Pexels, Unsplash, Pixabay).
Sin scraping web ni vulneración de SSL/ToS.
"""
import json
import ssl
import urllib.request
import urllib.parse
from PyQt6.QtCore import QSettings


def _get_ssl_context():
    """Retorna un contexto SSL seguro estándar con verificación estricta de certificados."""
    try:
        return ssl.create_default_context()
    except Exception:
        return None


class PexelsAPIClient:
    """Cliente oficial de búsqueda de imágenes desde Internet usando claves de API locales."""

    @staticmethod
    def get_search_status() -> dict:
        """Devuelve el estado de la configuración de búsqueda online."""
        settings = QSettings("PaintNotNet", "PaintNotNet")
        enabled = settings.value("online_search_enabled", False, type=bool)
        free_only = settings.value("online_search_free_only", False, type=bool)
        key_pexels = bool(str(settings.value("api_key_pexels", "")).strip())
        key_unsplash = bool(str(settings.value("api_key_unsplash", "")).strip())
        key_pixabay = bool(str(settings.value("api_key_pixabay", "")).strip())

        active_sources = []
        if enabled:
            active_sources.append("Wikimedia Commons")
            if not free_only:
                if key_pexels:
                    active_sources.append("Pexels")
                if key_unsplash:
                    active_sources.append("Unsplash")
                if key_pixabay:
                    active_sources.append("Pixabay")

        return {
            "enabled": enabled,
            "free_only": free_only,
            "has_pexels": key_pexels,
            "has_unsplash": key_unsplash,
            "has_pixabay": key_pixabay,
            "active_sources": active_sources
        }

    @staticmethod
    def search_photos(query: str, source: str = "Todas", is_transparent: bool = False, page: int = 1, per_page: int = 40) -> list:
        if not query or not query.strip():
            return []

        status = PexelsAPIClient.get_search_status()
        if not status["enabled"]:
            return []

        search_q = query.strip()
        photos = []
        source_clean = source.lower() if source else "todas"

        settings = QSettings("PaintNotNet", "PaintNotNet")
        key_pexels = str(settings.value("api_key_pexels", "")).strip()
        key_unsplash = str(settings.value("api_key_unsplash", "")).strip()
        key_pixabay = str(settings.value("api_key_pixabay", "")).strip()
        free_only = status["free_only"]

        # Determinar motores a consultar según la fuente elegida y las claves disponibles
        engines = []
        if "wikimedia" in source_clean:
            engines = ["wikimedia"]
        elif "pexels" in source_clean and key_pexels and not free_only:
            engines = ["pexels"]
        elif "unsplash" in source_clean and key_unsplash and not free_only:
            engines = ["unsplash"]
        elif "pixabay" in source_clean and key_pixabay and not free_only:
            engines = ["pixabay"]
        else:  # "Todas las fuentes"
            if not free_only:
                if key_pexels:
                    engines.append("pexels")
                if key_unsplash:
                    engines.append("unsplash")
                if key_pixabay:
                    engines.append("pixabay")
            engines.append("wikimedia")  # Wikimedia siempre disponible como fuente libre

        for engine in engines:
            try:
                if engine == "wikimedia":
                    photos = PexelsAPIClient._search_wikimedia(search_q, is_transparent, page, per_page)
                elif engine == "pexels":
                    photos = PexelsAPIClient._search_pexels_api(search_q, key_pexels, is_transparent, page, per_page)
                elif engine == "unsplash":
                    photos = PexelsAPIClient._search_unsplash_api(search_q, key_unsplash, is_transparent, page, per_page)
                elif engine == "pixabay":
                    photos = PexelsAPIClient._search_pixabay_api(search_q, key_pixabay, is_transparent, page, per_page)

                if photos:
                    break
            except Exception:
                pass

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
        headers = {"User-Agent": "PaintNotNet/2.0 (https://github.com/adrianandin0/PaintNotNet)"}
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
                                    "height": imageinfo[0].get("height") or 0,
                                    "source": "Wikimedia"
                                })
        except Exception:
            pass

        return photos

    @staticmethod
    def _search_pexels_api(query: str, api_key: str, is_transparent: bool, page: int, per_page: int) -> list:
        if not api_key:
            return []
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.pexels.com/v1/search?query={encoded_q}&page={page}&per_page={per_page}"
        headers = {
            "Authorization": api_key,
            "User-Agent": "PaintNotNet/2.0"
        }
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers=headers)
        photos = []
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    for item in data.get("photos", []):
                        src = item.get("src", {})
                        preview = src.get("medium") or src.get("small") or src.get("tiny")
                        download = src.get("original") or src.get("large2x") or src.get("large") or preview
                        if preview and download:
                            photos.append({
                                "id": str(item.get("id")),
                                "preview_url": preview,
                                "download_url": download,
                                "width": item.get("width") or 0,
                                "height": item.get("height") or 0,
                                "source": "Pexels"
                            })
        except Exception:
            pass
        return photos

    @staticmethod
    def _search_unsplash_api(query: str, api_key: str, is_transparent: bool, page: int, per_page: int) -> list:
        if not api_key:
            return []
        encoded_q = urllib.parse.quote(query)
        url = f"https://api.unsplash.com/search/photos?query={encoded_q}&page={page}&per_page={per_page}"
        headers = {
            "Authorization": f"Client-ID {api_key}",
            "User-Agent": "PaintNotNet/2.0"
        }
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
                        full = urls.get("full") or urls.get("regular") or urls.get("raw") or small
                        if small and full:
                            photos.append({
                                "id": str(item.get("id")),
                                "preview_url": small,
                                "download_url": full,
                                "width": item.get("width") or 0,
                                "height": item.get("height") or 0,
                                "source": "Unsplash"
                            })
        except Exception:
            pass
        return photos

    @staticmethod
    def _search_pixabay_api(query: str, api_key: str, is_transparent: bool, page: int, per_page: int) -> list:
        if not api_key:
            return []
        encoded_q = urllib.parse.quote(query)
        url = f"https://pixabay.com/api/?key={api_key}&q={encoded_q}&page={page}&per_page={per_page}"
        headers = {"User-Agent": "PaintNotNet/2.0"}
        ctx = _get_ssl_context()
        req = urllib.request.Request(url, headers=headers)
        photos = []
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=8) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8", errors="ignore"))
                    for item in data.get("hits", []):
                        preview = item.get("webformatURL") or item.get("previewURL")
                        download = item.get("largeImageURL") or preview
                        if preview and download:
                            photos.append({
                                "id": str(item.get("id")),
                                "preview_url": preview,
                                "download_url": download,
                                "width": item.get("imageWidth") or 0,
                                "height": item.get("imageHeight") or 0,
                                "source": "Pixabay"
                            })
        except Exception:
            pass
        return photos

    @staticmethod
    def download_bytes(url: str) -> bytes | None:
        if not url:
            return None
        headers = {
            "User-Agent": "PaintNotNet/2.0 (https://github.com/adrianandin0/PaintNotNet)"
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
