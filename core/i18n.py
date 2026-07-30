import os
import json
import sys
from PyQt6.QtCore import QSettings

class I18nManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(I18nManager, cls).__new__(cls)
            cls._instance._init_manager()
        return cls._instance

    def _init_manager(self):
        self.translations = {}
        self.current_language = "Español"
        self.cargar_idioma_configurado()

    def _obtener_ruta_locales(self):
        if getattr(sys, 'frozen', False):
            base_dir = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        return os.path.join(base_dir, "locales")

    def cargar_idioma_configurado(self):
        settings = QSettings("PaintNotNet", "PaintNotNet")
        lang = settings.value("language", "Español")
        self.establecer_idioma(str(lang))

    def establecer_idioma(self, nombre_idioma):
        self.current_language = nombre_idioma
        lang_lower = str(nombre_idioma).lower()
        if "english" in lang_lower or "inglés" in lang_lower or "ingles" in lang_lower:
            codigo = "en"
        elif "português" in lang_lower or "portugues" in lang_lower:
            codigo = "pt"
        elif "中文" in lang_lower or "chino" in lang_lower or "chinese" in lang_lower:
            codigo = "zh"
        elif "deutsch" in lang_lower or "alemán" in lang_lower or "aleman" in lang_lower:
            codigo = "de"
        else:
            codigo = "es"

        locales_dir = self._obtener_ruta_locales()
        archivo_json = os.path.join(locales_dir, f"{codigo}.json")

        if os.path.exists(archivo_json):
            try:
                with open(archivo_json, "r", encoding="utf-8") as f:
                    self.translations = json.load(f)
            except Exception as e:
                print(f"[i18n] Error al cargar {archivo_json}: {e}")
                self.translations = {}
        else:
            self.translations = {}

    def t(self, key, default=None):
        if not key:
            return ""
        if default is None:
            default = key
        return self.translations.get(key, default)


def t(key, default=None):
    return I18nManager().t(key, default)
