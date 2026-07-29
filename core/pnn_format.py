import os
import json
import zipfile
from PyQt6.QtGui import QImage
from PyQt6.QtCore import Qt, QBuffer, QIODevice


def guardar_proyecto_pnn(canvas, ruta_archivo):
    """
    Guarda el proyecto completo de PaintNotNet en formato nativo .pnn (ZIP).
    Contiene:
    - manifest.json: metadatos del proyecto y lista de capas.
    - layer_0.png, layer_1.png...: imágenes PNG individuales en RGBA32.
    """
    layer_mgr = canvas.layer_mgr

    manifest = {
        "version": "1.0",
        "format": "PaintNotNet Project",
        "width": layer_mgr.width,
        "height": layer_mgr.height,
        "active_index": layer_mgr.indice_activo,
        "layers": []
    }

    with zipfile.ZipFile(ruta_archivo, 'w', compression=zipfile.ZIP_DEFLATED) as zip_file:
        for idx, capa in enumerate(layer_mgr.capas):
            img_filename = f"layer_{idx}.png"
            layer_info = {
                "name": capa.name,
                "visible": getattr(capa, 'visible', True),
                "opacity": getattr(capa, 'opacity', 1.0),
                "filename": img_filename
            }
            manifest["layers"].append(layer_info)

            # Convertir QImage a bytes PNG
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            capa.image.save(buffer, "PNG")
            bytes_data = buffer.data().data()
            buffer.close()

            zip_file.writestr(img_filename, bytes_data)

        # Guardar manifiesto JSON
        json_data = json.dumps(manifest, indent=2, ensure_ascii=False)
        zip_file.writestr("manifest.json", json_data.encode('utf-8'))

    return True


def cargar_proyecto_pnn(canvas, ruta_archivo):
    """
    Carga un proyecto .pnn desde disco y restaura la lista de capas y estado en canvas.
    """
    if not os.path.exists(ruta_archivo) or not zipfile.is_zipfile(ruta_archivo):
        return False

    with zipfile.ZipFile(ruta_archivo, 'r') as zip_file:
        if "manifest.json" not in zip_file.namelist():
            return False

        json_bytes = zip_file.read("manifest.json")
        manifest = json.loads(json_bytes.decode('utf-8'))

        width = manifest.get("width", 800)
        height = manifest.get("height", 600)
        active_index = manifest.get("active_index", 0)

        layer_mgr = canvas.layer_mgr
        layer_mgr.width = width
        layer_mgr.height = height
        layer_mgr.capas.clear()

        for layer_info in manifest.get("layers", []):
            nombre = layer_info.get("name", "Capa")
            visible = layer_info.get("visible", True)
            opacity = layer_info.get("opacity", 1.0)
            img_filename = layer_info.get("filename", "")

            # Crear objeto capa
            from core.layers import Layer
            capa = Layer(nombre, width, height, transparent=True)
            capa.visible = visible
            capa.opacity = opacity

            if img_filename in zip_file.namelist():
                png_bytes = zip_file.read(img_filename)
                qimg = QImage()
                qimg.loadFromData(png_bytes, "PNG")
                if not qimg.isNull():
                    capa.image = qimg.convertToFormat(QImage.Format.Format_ARGB32_Premultiplied)

            layer_mgr.capas.append(capa)

        layer_mgr.indice_activo = min(max(0, active_index), len(layer_mgr.capas) - 1) if layer_mgr.capas else 0

        # Ajustar dimensiones físicas del canvas widget
        canvas._ajustar_tamano_widget(width, height)
        canvas.capa_trazo_temp = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
        canvas.capa_trazo_temp.fill(Qt.GlobalColor.transparent)

        # Reset de selección
        canvas.selection_engine.clear_selection()

        # Reset de historial al estado recién cargado
        canvas.history_mgr.history_stack.clear()
        canvas.history_mgr.current_index = -1
        canvas.push_document_state("Cargar borrador .pnn")

        canvas.update()
        return True
