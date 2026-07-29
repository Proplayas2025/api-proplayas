"""Persistencia de archivos subidos (imágenes y documentos).

Centraliza la construcción de rutas bajo `settings.UPLOAD_DIR` para que los
services no manipulen el sistema de archivos directamente.
"""
import shutil
from pathlib import Path
from typing import BinaryIO

from core.config import settings
from core.image import save_optimized_image

PROFILES_DIR = "profiles"
COVERS_DIR = "covers"
DOCS_DIR = "docs"


def _upload_dir(subdir: str) -> Path:
    path = Path(settings.UPLOAD_DIR) / subdir
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_image(image_bytes: bytes, subdir: str, name: str) -> str:
    """Optimiza la imagen a WebP y la guarda. Devuelve solo el nombre del archivo.

    El frontend construye la URL completa a partir del nombre (`/storage/uploads/...`).
    """
    output_path = _upload_dir(subdir) / name
    return save_optimized_image(image_bytes, output_path).name


def save_document(file: BinaryIO, subdir: str, filename: str) -> str:
    """Guarda un documento tal cual. Devuelve solo el nombre del archivo."""
    destination = _upload_dir(subdir) / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file, buffer)
    return filename


def extension_of(filename: str | None, default: str = "") -> str:
    """Extensión de un nombre de archivo, sin el punto."""
    if filename and "." in filename:
        return filename.rsplit(".", 1)[-1]
    return default
