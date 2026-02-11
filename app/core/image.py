"""
Utilidad para optimizar imágenes.
Convierte cualquier formato de imagen a WebP con calidad configurable.
Usa Pillow (pillow==11.0.0).
"""
from PIL import Image
from io import BytesIO
from pathlib import Path

# Tamaño máximo de imagen (ancho, alto)
MAX_IMAGE_SIZE = (1920, 1920)
# Calidad WebP (1-100)
WEBP_QUALITY = 80


def optimize_image(
    input_bytes: bytes,
    max_size: tuple[int, int] = MAX_IMAGE_SIZE,
    quality: int = WEBP_QUALITY,
) -> bytes:
    """
    Optimiza una imagen: la redimensiona si excede max_size y la convierte a WebP.

    Args:
        input_bytes: bytes crudos de la imagen original.
        max_size: tupla (ancho_max, alto_max). Se escala proporcionalmente.
        quality: calidad WebP (1-100).

    Returns:
        bytes de la imagen optimizada en formato WebP.
    """
    img = Image.open(BytesIO(input_bytes))

    # Convertir RGBA/P a RGB para WebP sin transparencia problemática
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background.convert("RGB")
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Redimensionar si excede el tamaño máximo (mantiene proporción)
    img.thumbnail(max_size, Image.Resampling.LANCZOS)

    # Guardar como WebP
    output = BytesIO()
    img.save(output, format="WEBP", quality=quality, optimize=True)
    output.seek(0)
    return output.read()


def save_optimized_image(
    input_bytes: bytes,
    output_path: Path,
    max_size: tuple[int, int] = MAX_IMAGE_SIZE,
    quality: int = WEBP_QUALITY,
) -> Path:
    """
    Optimiza y guarda la imagen en disco como WebP.

    Args:
        input_bytes: bytes crudos de la imagen.
        output_path: ruta destino (se fuerza extensión .webp).
        max_size: tamaño máximo.
        quality: calidad WebP.

    Returns:
        Path final del archivo guardado (con extensión .webp).
    """
    # Forzar extensión .webp
    final_path = output_path.with_suffix(".webp")

    optimized = optimize_image(input_bytes, max_size, quality)

    final_path.parent.mkdir(parents=True, exist_ok=True)
    with final_path.open("wb") as f:
        f.write(optimized)

    return final_path
