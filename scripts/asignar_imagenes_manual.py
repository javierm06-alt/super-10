"""
asignar_imagenes_manual.py — Asignación manual vía barcode + cascada de fuentes
=================================================================================
Recibe un diccionario id → url_pagina_producto (Bodega Aurrera / Walmart MX).
Extrae el código de barras UPC de la URL y lo usa para buscar imagen sin scraping.

Cascada de fuentes:
  1. Open Food Facts API por barcode  → directa, sin scraping ni CAPTCHA
  2. Open Food Facts API por nombre   → búsqueda textual
  3. Si ninguno funciona              → imagen_url queda NULL (muestra emoji)

El nombre real del producto se actualiza si OFF lo tiene indexado.

Para cada imagen encontrada:
  → Descargar
  → rembg → quitar fondo
  → Pillow → fondo blanco + padding + resize 800×800px
  → Supabase Storage (bucket "productos")
  → UPDATE catalogo_productos SET imagen_url = ..., nombre = ... WHERE id = {id}

Uso:
  python asignar_imagenes_manual.py
"""

import io
import logging
import re
import sys
import unicodedata

# Fix encoding para terminales Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests
from PIL import Image
from supabase import create_client

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

SUPABASE_URL   = "https://dqrhqzdfzhkqpgawgjga.supabase.co"
SUPABASE_KEY   = "sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ"
STORAGE_BUCKET = "productos"

IMG_SIZE    = 800
IMG_PADDING = 20
TIMEOUT     = 15   # segundos por request HTTP

# ══════════════════════════════════════════════════════════════
# LOGGING
# ══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("asignar_imagenes_manual.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# SETUP rembg
# ══════════════════════════════════════════════════════════════

def _init_rembg():
    try:
        import onnxruntime as ort
        gpu = "CUDAExecutionProvider" in ort.get_available_providers()
    except ImportError:
        gpu = False
    try:
        from rembg import new_session, remove as _remove
        session = new_session("u2net")
        log.info("rembg listo (%s)", "GPU/CUDA" if gpu else "CPU")
        return _remove, session
    except Exception as e:
        log.error("No se pudo inicializar rembg: %s", e)
        sys.exit(1)

rembg_remove, rembg_session = _init_rembg()

# ══════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════

def slugify(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^\w\s]", "", texto.lower())
    texto = re.sub(r"\s+", "_", texto.strip())
    return texto[:60]


def extraer_barcode(url: str) -> str | None:
    """
    Extrae el código de barras del último segmento de la URL.
    Ej: /ip/nombre-del-producto/00750105242043 → '00750105242043'
    """
    segmento = url.rstrip("/").split("/")[-1]
    if re.fullmatch(r"\d{8,14}", segmento):
        return segmento
    return None


def descargar_imagen(url: str) -> bytes | None:
    try:
        headers = {"User-Agent": "TiendaInteligente/2.0 (contacto@agencia.ia)"}
        resp = requests.get(url, headers=headers, timeout=TIMEOUT)
        resp.raise_for_status()
        if "image" not in resp.headers.get("content-type", ""):
            return None
        return resp.content
    except Exception as e:
        log.debug("Error descargando %s: %s", url[:80], e)
        return None

# ══════════════════════════════════════════════════════════════
# FUENTES DE IMAGEN
# ══════════════════════════════════════════════════════════════

_OFF_HEADERS = {"User-Agent": "TiendaInteligente/2.0 (contacto@agencia.ia)"}


def off_por_barcode(barcode: str) -> tuple[str | None, str | None]:
    """
    Consulta Open Food Facts por código de barras.
    Retorna (img_url, nombre_producto) o (None, None).
    """
    # Probar con y sin ceros iniciales
    variantes = [barcode, barcode.lstrip("0")]
    for code in variantes:
        try:
            resp = requests.get(
                f"https://world.openfoodfacts.org/api/v0/product/{code}.json",
                headers=_OFF_HEADERS,
                timeout=TIMEOUT,
            )
            resp.raise_for_status()
            data = resp.json()
            if data.get("status") != 1:
                continue
            p = data.get("product", {})
            img = p.get("image_front_url") or p.get("image_url")
            nombre = p.get("product_name") or p.get("product_name_es") or ""
            nombre = nombre.strip() or None
            if img and img.startswith("http"):
                return img, nombre
        except Exception as e:
            log.debug("OFF barcode %s: %s", code, e)
    return None, None


def off_por_nombre(nombre: str) -> str | None:
    """Búsqueda textual en Open Food Facts."""
    try:
        resp = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={
                "search_terms": nombre,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5,
                "fields": "product_name,image_front_url,image_url",
                "lc": "es",
            },
            headers=_OFF_HEADERS,
            timeout=TIMEOUT,
        )
        resp.raise_for_status()
        for p in resp.json().get("products", []):
            img = p.get("image_front_url") or p.get("image_url")
            if img and img.startswith("http"):
                return img
    except Exception as e:
        log.debug("OFF nombre '%s': %s", nombre, e)
    return None


def buscar_imagen(
    barcode: str | None,
    nombre_db: str,
) -> tuple[str | None, str | None]:
    """
    Cascada: OFF por barcode → OFF por nombre.
    Retorna (img_url, nombre_off|None), o (None, None) si ninguna fuente responde.
    """
    # 1. OFF por barcode (más preciso, puede devolver nombre real)
    if barcode:
        img, nombre_off = off_por_barcode(barcode)
        if img:
            log.info("  📷 Fuente: Open Food Facts (barcode %s)", barcode)
            return img, nombre_off

    # 2. OFF por nombre
    img = off_por_nombre(nombre_db)
    if img:
        log.info("  📷 Fuente: Open Food Facts (búsqueda '%s')", nombre_db)
        return img, None

    return None, None

# ══════════════════════════════════════════════════════════════
# PROCESAMIENTO DE IMAGEN
# ══════════════════════════════════════════════════════════════

def procesar_imagen(img_bytes: bytes) -> bytes:
    """rembg → fondo blanco 800×800 → PNG optimizado."""
    sin_fondo = rembg_remove(img_bytes, session=rembg_session)
    img = Image.open(io.BytesIO(sin_fondo)).convert("RGBA")
    max_inner = IMG_SIZE - (IMG_PADDING * 2)
    img.thumbnail((max_inner, max_inner), Image.LANCZOS)
    canvas = Image.new("RGBA", (IMG_SIZE, IMG_SIZE), (255, 255, 255, 255))
    x = (IMG_SIZE - img.width) // 2
    y = (IMG_SIZE - img.height) // 2
    canvas.paste(img, (x, y), mask=img)
    buf = io.BytesIO()
    canvas.convert("RGB").save(buf, format="PNG", optimize=True)
    buf.seek(0)
    return buf.read()

# ══════════════════════════════════════════════════════════════
# SUPABASE
# ══════════════════════════════════════════════════════════════

def subir_a_storage(supabase_client, producto_id: int, nombre: str, img_bytes: bytes) -> str | None:
    filename = f"{producto_id}_{slugify(nombre)}.png"
    try:
        supabase_client.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=img_bytes,
            file_options={"content-type": "image/png", "upsert": "true"},
        )
        url = supabase_client.storage.from_(STORAGE_BUCKET).get_public_url(filename)
        log.info("  ☁  Storage: %s", filename)
        return url
    except Exception as e:
        log.error("  Error subiendo a Storage: %s", e)
        return None


def actualizar_producto(supabase_client, producto_id: int, imagen_url: str, nombre: str | None) -> bool:
    """UPDATE imagen_url y nombre (si se obtuvo de OFF) en catalogo_productos."""
    campos: dict = {"imagen_url": imagen_url}
    if nombre:
        campos["nombre"] = nombre
    try:
        supabase_client.table("catalogo_productos") \
            .update(campos) \
            .eq("id", producto_id) \
            .execute()
        log.info("  ✅ DB actualizada (%s)", ", ".join(campos.keys()))
        return True
    except Exception as e:
        log.error("  Error actualizando DB: %s", e)
        return False

# ══════════════════════════════════════════════════════════════
# FUNCIÓN PRINCIPAL EXPORTABLE
# ══════════════════════════════════════════════════════════════

def procesar_paginas(paginas: dict[int, str]) -> dict:
    """
    Procesa {producto_id: url_pagina_producto}.
    Extrae barcode de la URL → cascada OFF/Unsplash → rembg → Storage → UPDATE.
    Retorna {"ok": [...], "error": [...]}
    """
    SEP = "=" * 65
    log.info(SEP)
    log.info("  ASIGNACIÓN MANUAL — Barcode + Open Food Facts + Unsplash")
    log.info("  %d producto(s): %s", len(paginas), list(paginas.keys()))
    log.info(SEP)

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    ids = list(paginas.keys())
    try:
        resp = supabase.table("catalogo_productos") \
            .select("id, nombre, categoria") \
            .in_("id", ids) \
            .execute()
        info_actual = {p["id"]: p for p in resp.data}
    except Exception as e:
        log.error("Error consultando Supabase: %s", e)
        sys.exit(1)

    resultado = {"ok": [], "error": []}
    total = len(paginas)

    for idx, (pid, url_pagina) in enumerate(paginas.items(), start=1):
        info      = info_actual.get(pid, {})
        nombre_db = info.get("nombre", f"producto_{pid}")
        cat       = info.get("categoria", "—")

        barcode = extraer_barcode(url_pagina)

        log.info("\n[%d/%d] ID %d — %s (%s)", idx, total, pid, nombre_db, cat)
        log.info("  Barcode: %s", barcode or "no detectado")

        # 1. Buscar imagen en cascada OFF barcode → OFF nombre
        img_url, nombre_off = buscar_imagen(barcode, nombre_db)
        if not img_url:
            log.warning("  ⏭  Sin imagen en ninguna fuente")
            resultado["error"].append(pid)
            continue

        if nombre_off and nombre_off != nombre_db:
            log.info("  📝 Nombre OFF: '%s'", nombre_off)

        # 2. Descargar
        img_bytes_orig = descargar_imagen(img_url)
        if not img_bytes_orig:
            resultado["error"].append(pid)
            continue
        log.info("  ⬇  Descargada: %d KB", len(img_bytes_orig) // 1024)

        # 3. rembg + Pillow
        try:
            log.info("  🔧 Procesando con rembg...")
            img_final = procesar_imagen(img_bytes_orig)
            log.info("  ✔  Procesada: %d KB", len(img_final) // 1024)
        except Exception as e:
            log.error("  Error procesando imagen: %s", e)
            resultado["error"].append(pid)
            continue

        # 4. Storage
        nombre_para_slug = nombre_off or nombre_db
        url_publica = subir_a_storage(supabase, pid, nombre_para_slug, img_final)
        if not url_publica:
            resultado["error"].append(pid)
            continue

        # 5. UPDATE (nombre_off solo si OFF lo devolvió)
        if not actualizar_producto(supabase, pid, url_publica, nombre_off):
            resultado["error"].append(pid)
            continue

        resultado["ok"].append(pid)

    log.info("\n%s", SEP)
    log.info("  RESUMEN")
    log.info("  OK     : %d — IDs %s", len(resultado["ok"]),    resultado["ok"])
    log.info("  ERROR  : %d — IDs %s", len(resultado["error"]), resultado["error"])
    log.info(SEP)
    log.info("Log completo en: asignar_imagenes_manual.log")
    return resultado

# ══════════════════════════════════════════════════════════════
# PÁGINAS DE PRODUCTO (editar aquí para cada uso)
# ══════════════════════════════════════════════════════════════

PAGINAS: dict[int, str] = {
    6:  "https://despensa.bodegaaurrera.com.mx/ip/frijoles-bayos-la-sierra-refritos-580-g/00750105242043",
    12: "https://despensa.bodegaaurrera.com.mx/ip/azucar-morena-zulka-2-kg/00066144000005",
}

if __name__ == "__main__":
    procesar_paginas(PAGINAS)
