"""
apps/document_converter/i18n.py
───────────────────────────────
Gestor de internacionalización ligero para MediaHub-DocumentConverter.
"""

import os
import sys
import json
import locale

_CURRENT_LANG = None

STRINGS = {
    "es": {
        "app_title": "Convertidor de Documentos y PDF Studio — Media Hub",
        "tab_convert": "Conversor Universal",
        "tab_merge": "Unir PDFs (Merge)",
        "tab_split": "Dividir / Extraer (Split)",
        "btn_convert": "Convertir Documento",
        "btn_add_pdfs": "Agregar PDFs",
        "btn_delete": "Eliminar",
        "btn_merge_save": "Unir y Guardar PDF",
        "btn_split_run": "Ejecutar División",
        "btn_exit": "Salir",
        "no_pdf_selected": "Ningún archivo PDF seleccionado",
        "prompt_select_first": "Selecciona o arrastra un archivo para ver los formatos disponibles",
        "status_done": "Conversión completada exitosamente",
        "status_error": "Error al convertir documento",
    },
    "en": {
        "app_title": "Document Converter & PDF Studio — Media Hub",
        "tab_convert": "Universal Converter",
        "tab_merge": "Merge PDFs",
        "tab_split": "Split / Extract",
        "btn_convert": "Convert Document",
        "btn_add_pdfs": "Add PDFs",
        "btn_delete": "Delete",
        "btn_merge_save": "Merge & Save PDF",
        "btn_split_run": "Run Split",
        "btn_exit": "Exit",
        "no_pdf_selected": "No PDF file selected",
        "prompt_select_first": "Select or drag a file to see available formats",
        "status_done": "Conversion completed successfully",
        "status_error": "Error converting document",
    }
}


def get_current_language() -> str:
    global _CURRENT_LANG
    if _CURRENT_LANG:
        return _CURRENT_LANG

    # 1. CLI argument
    for arg in sys.argv[1:]:
        if arg.startswith("--lang="):
            val = arg.split("=", 1)[1].strip().lower()
            if val in ("es", "en"):
                _CURRENT_LANG = val
                return _CURRENT_LANG

    # 2. Environment variables
    for env_var in ("MEDIAHUB_APP_LANG", "MEDIAHUB_LANG", "LANG"):
        val = os.environ.get(env_var, "").lower()
        if val.startswith("es"):
            _CURRENT_LANG = "es"
            return "es"
        elif val.startswith("en"):
            _CURRENT_LANG = "en"
            return "en"

    # 3. Local config_lang.json
    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))
    for cfg in [os.path.join(base_dir, "config_lang.json"), os.path.join(base_dir, "..", "config_lang.json")]:
        if os.path.isfile(cfg):
            try:
                with open(cfg, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    val = data.get("language")
                    if val in ("es", "en"):
                        _CURRENT_LANG = val
                        return _CURRENT_LANG
            except Exception:
                pass

    # 4. Fallback sistema
    try:
        lang, _ = locale.getdefaultlocale()
        if lang and lang.lower().startswith("es"):
            _CURRENT_LANG = "es"
            return "es"
    except Exception:
        pass

    _CURRENT_LANG = "es"
    return "es"


def t(key: str, **kwargs) -> str:
    lang = get_current_language()
    text = STRINGS.get(lang, STRINGS["es"]).get(key, STRINGS["es"].get(key, key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except Exception:
            return text
    return text
