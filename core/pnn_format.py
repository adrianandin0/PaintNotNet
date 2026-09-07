import os
import re
import json
import zipfile
import hashlib
from datetime import datetime, timezone
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt, QBuffer, QIODevice
from core.i18n import t

CURRENT_FORMAT_VERSION = 1


def _obtener_version_app():
    try:
        base_dir = os.path.dirname(os.path.dirname(__file__))
        v_file = os.path.join(base_dir, "version.txt")
        if os.path.exists(v_file):
            with open(v_file, "r", encoding="utf-8") as f:
                ver = f.read().strip()
                if ver:
                    return ver
    except Exception:
        pass
    return "2.0.0"


def _calcular_checksum(manifest_dict, capas_bytes):
    """
    Calcula la suma de verificación SHA-256 sobre:
    1. El contenido canónico JSON del manifiesto (sin la clave 'checksum', sin espacios y ordenando claves).
    2. Los bytes PNG de todas las capas en orden secuencial.
    """
    hasher = hashlib.sha256()

    manifest_copy = {k: v for k, v in manifest_dict.items() if k != "checksum"}
    canonical_json = json.dumps(manifest_copy, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    hasher.update(canonical_json.encode('utf-8'))

    for b in capas_bytes:
        hasher.update(b)

    return hasher.hexdigest()


def _mostrar_error_carga(canvas, mensaje: str):
    try:
        from PyQt6.QtWidgets import QMessageBox
        parent_widget = canvas.main_window if hasattr(canvas, 'main_window') and canvas.main_window else canvas
        QMessageBox.critical(parent_widget, t("Error de archivo .pnn"), mensaje)
    except Exception:
        pass


def guardar_proyecto_pnn(canvas, ruta_archivo):
    """
    Guarda el proyecto completo de PaintNotNet en formato nativo .pnn (ZIP).
    Contiene:
    - manifest.json: metadatos del proyecto, checksum SHA-256, versionado y lista de capas.
    - layer_0.png, layer_1.png...: imágenes PNG individuales por capa en RGBA32.
    """
    layer_mgr = canvas.layer_mgr
    now_iso = datetime.now(timezone.utc).isoformat()

    created_at = getattr(canvas, 'pnn_created_at', None) or now_iso
    canvas.pnn_created_at = created_at

    dpi_config = getattr(canvas, 'pnn_dpi', {"x": 96, "y": 96})
    if isinstance(dpi_config, list) and len(dpi_config) >= 2:
        dpi_config = {"x": dpi_config[0], "y": dpi_config[1]}

    manifest = {
        "format": "PaintNotNet Project",
        "format_version": CURRENT_FORMAT_VERSION,
        "app_version": _obtener_version_app(),
        "created_at": created_at,
        "modified_at": now_iso,
        "dpi": dpi_config,
        "width": layer_mgr.width,
        "height": layer_mgr.height,
        "active_index": layer_mgr.indice_activo,
        "layers": []
    }

    engine = getattr(canvas, 'selection_engine', None)
    has_floating = bool(engine and engine.floating_image and not engine.floating_image.isNull())

    capas_bytes = []
    layers_metadata = []

    for idx, capa in enumerate(layer_mgr.capas):
        img_filename = f"layer_{idx}.png"
        layer_info = {
            "name": capa.name,
            "visible": getattr(capa, 'visible', True),
            "opacity": getattr(capa, 'opacity', 1.0),
            "filename": img_filename
        }
        layers_metadata.append(layer_info)

        img_to_save = capa.image
        if has_floating and idx == layer_mgr.indice_activo:
            from PyQt6.QtGui import QPainter
            img_to_save = capa.image.copy()
            p = QPainter(img_to_save)
            p.setCompositionMode(QPainter.CompositionMode.CompositionMode_SourceOver)
            p.drawImage(engine.original_image_pos, engine.floating_image)
            p.end()

        # Convertir QImage a bytes PNG
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        img_to_save.save(buffer, "PNG")
        bytes_data = buffer.data().data()
        buffer.close()

        capas_bytes.append((img_filename, bytes_data))

    manifest["layers"] = layers_metadata

    # Calcular Checksum SHA-256 canónico
    manifest["checksum"] = _calcular_checksum(manifest, [b for _, b in capas_bytes])

    # Guardar manifiesto y capas en archivo ZIP
    with zipfile.ZipFile(ruta_archivo, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for fname, bdata in capas_bytes:
            zip_file.writestr(fname, bdata)

        json_data = json.dumps(manifest, indent=2, ensure_ascii=False)
        zip_file.writestr("manifest.json", json_data.encode('utf-8'))

    return True


def cargar_proyecto_pnn(canvas, ruta_archivo):
    """
    Carga un proyecto .pnn desde disco y restaura la lista de capas y estado en canvas.
    Realiza validación estricta de lista blanca ZIP y verificación de Checksum SHA-256.
    """
    if not os.path.exists(ruta_archivo) or not zipfile.is_zipfile(ruta_archivo):
        return False

    try:
        with zipfile.ZipFile(ruta_archivo, 'r') as zip_file:
            namelist = zip_file.namelist()

            # 1. Validación estricta de lista blanca (Whitelist ZIP)
            pattern_layer = re.compile(r"^layer_\d+\.png$")
            for fname in namelist:
                if fname == "manifest.json":
                    continue
                if not pattern_layer.match(fname):
                    print(f"[PNN] Archivo no autorizado o sospechoso en ZIP: {fname}")
                    _mostrar_error_carga(canvas, t("El proyecto contiene archivos no autorizados en su interior (%1).").replace("%1", fname))
                    return False

            if "manifest.json" not in namelist:
                print("[PNN] Falta manifest.json en el archivo ZIP")
                return False

            json_bytes = zip_file.read("manifest.json")
            manifest = json.loads(json_bytes.decode('utf-8'))

            # 2. Validación de Versionado del Formato
            format_ver = manifest.get("format_version", 1)
            if format_ver > CURRENT_FORMAT_VERSION:
                msg = t("El proyecto fue guardado con una versión superior del formato (%1). Por favor actualiza PaintNotNet.").replace("%1", str(format_ver))
                _mostrar_error_carga(canvas, msg)
                return False

            # 3. Verificación del Checksum SHA-256
            expected_checksum = manifest.get("checksum")
            if expected_checksum:
                layers_meta = manifest.get("layers", [])
                capas_bytes_cargadas = []
                for layer_info in layers_meta:
                    fname = layer_info.get("filename", "")
                    if fname in namelist:
                        capas_bytes_cargadas.append(zip_file.read(fname))
                    else:
                        capas_bytes_cargadas.append(b"")

                computed_checksum = _calcular_checksum(manifest, capas_bytes_cargadas)
                if computed_checksum != expected_checksum:
                    print(f"[PNN] Error de integridad SHA-256 en {ruta_archivo}")
                    _mostrar_error_carga(
                        canvas,
                        t("El archivo '%1' está dañado o fue modificado externamente.").replace("%1", os.path.basename(ruta_archivo))
                    )
                    return False

            width = manifest.get("width", 800)
            height = manifest.get("height", 600)
            active_index = manifest.get("active_index", 0)

            # Preservar metadatos creados
            canvas.pnn_created_at = manifest.get("created_at")

            # Preservar DPI (soporte para {"x": 96, "y": 96} y compatibilidad con lista [96, 96])
            dpi_meta = manifest.get("dpi", {"x": 96, "y": 96})
            if isinstance(dpi_meta, list) and len(dpi_meta) >= 2:
                dpi_meta = {"x": dpi_meta[0], "y": dpi_meta[1]}
            canvas.pnn_dpi = dpi_meta

            nuevas_capas = []
            from core.layers import Layer

            for layer_info in manifest.get("layers", []):
                nombre = layer_info.get("name", "Capa")
                visible = layer_info.get("visible", True)
                opacity = layer_info.get("opacity", 1.0)
                img_filename = layer_info.get("filename", "")

                # Sanitización Zip Slip
                clean_name = os.path.basename(img_filename)
                if clean_name != img_filename or ".." in img_filename or img_filename.startswith(("/", "\\")):
                    print(f"[PNN] Ruta sospechosa o invalida en manifest: {img_filename}")
                    return False

                capa = Layer(nombre, width, height, transparent=True)
                capa.visible = visible
                capa.opacity = opacity

                if img_filename in namelist:
                    png_bytes = zip_file.read(img_filename)
                    qimg = QImage()
                    qimg.loadFromData(png_bytes, "PNG")
                    if not qimg.isNull():
                        capa.image = qimg.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)
                    else:
                        print(f"[PNN] Error al decodificar PNG para {img_filename}")
                        return False

                nuevas_capas.append(capa)

            if not nuevas_capas:
                return False

            # Aplicar cambios únicamente tras la carga exitosa completa
            layer_mgr = canvas.layer_mgr
            layer_mgr.width = width
            layer_mgr.height = height
            layer_mgr.capas = nuevas_capas
            layer_mgr.indice_activo = min(max(0, active_index), len(layer_mgr.capas) - 1)

            # Ajustar dimensiones físicas del canvas widget
            canvas._ajustar_tamano_widget(width, height)
            canvas.capa_trazo_temp = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
            canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

            # Reconstruir panel de capas en UI
            if hasattr(canvas, 'main_window') and canvas.main_window and hasattr(canvas.main_window, 'layers_panel'):
                canvas.main_window.layers_panel.reconstruir_lista_capas()

            # Reset de selección
            if hasattr(canvas, 'selection_engine') and canvas.selection_engine:
                canvas.selection_engine.clear_selection()

            # Reset de historial al estado recién cargado
            canvas.history_mgr.history_stack.clear()
            canvas.history_mgr.current_index = -1
            canvas.push_document_state("Cargar borrador .pnn")

            canvas.update()
            return True

    except Exception as e:
        print(f"[PNN] Error al cargar proyecto .pnn: {e}")
        return False
