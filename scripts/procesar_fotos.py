"""
procesar_fotos.py — Pipeline de imágenes escalable para Tienda Inteligente
===========================================================================
Procesa en lotes todos los productos con imagen_url vacía o null.

Cascada de fuentes (en orden):
  1. Open Food Facts API  — búsqueda por nombre
  2. Walmart México       — Playwright headless (walmart.com.mx)
  3. Bodega Aurrera       — Playwright headless (bodegas-aurrera.com.mx)
  4. Si ninguno funciona  → imagen_url queda NULL (muestra emoji en tienda)

Para cada imagen encontrada:
  → Descargar
  → rembg → quitar fondo
  → Pillow → fondo blanco + padding + resize 800×800px
  → Supabase Storage (bucket "productos") → subir PNG
  → UPDATE catalogo_productos SET imagen_url = url_pública

Ejecutar:
  cd C:/Users/USER/Desktop/Agencia_IA
  venv\\Scripts\\activate
  cd Modulo_Tienda_Abarrotes/scripts
  python procesar_fotos.py
"""

import io
import logging
import re
import sys
import time
import unicodedata
from urllib.parse import quote_plus

# Fix encoding para terminales Windows (cp1252 no soporta emojis)
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

SUPABASE_URL = "https://dqrhqzdfzhkqpgawgjga.supabase.co"
SUPABASE_KEY = "sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ"

BATCH_SIZE            = 20    # productos por lote
PAUSA_ENTRE_PRODUCTOS = 2     # segundos entre productos (dentro del lote)
PAUSA_ENTRE_LOTES     = 10    # segundos entre lotes
TIMEOUT_FUENTE        = 10    # segundos máx por request HTTP (OFF, Unsplash)
TIMEOUT_PLAYWRIGHT    = 15000 # ms máx por búsqueda con Playwright

IMG_SIZE       = 800   # px — canvas final cuadrado
IMG_PADDING    = 20    # px — margen interior en cada lado
STORAGE_BUCKET = "productos"

# ══════════════════════════════════════════════════════════════
# LOGGING — consola + archivo
# ══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("procesar_fotos.log", encoding="utf-8"),
    ],
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# SETUP rembg
# ══════════════════════════════════════════════════════════════

def _init_rembg():
    """Inicializa rembg; detecta GPU pero no aborta si falta CUDA."""
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
# PLAYWRIGHT — singleton de browser (reutilizado entre búsquedas)
# ══════════════════════════════════════════════════════════════

_pw_instance = None
_pw_browser  = None


def _get_pw_browser():
    """
    Inicializa Playwright/Chromium headless la primera vez que se llama.
    Retorna el browser, o None si Playwright no está disponible.
    """
    global _pw_instance, _pw_browser
    if _pw_browser is not None:
        return _pw_browser
    try:
        from playwright.sync_api import sync_playwright
        _pw_instance = sync_playwright().__enter__()
        _pw_browser  = _pw_instance.chromium.launch(headless=True)
        log.info("Playwright/Chromium iniciado (headless)")
    except Exception as e:
        log.warning("Playwright no disponible: %s — fuentes 2 y 3 deshabilitadas", e)
        _pw_browser = None
    return _pw_browser


def _close_pw_browser():
    """Cierra el browser y la instancia de Playwright."""
    global _pw_instance, _pw_browser
    if _pw_browser:
        try:
            _pw_browser.close()
        except Exception:
            pass
    if _pw_instance:
        try:
            _pw_instance.__exit__(None, None, None)
        except Exception:
            pass
    _pw_browser  = None
    _pw_instance = None


def _scrape_con_playwright(url_busqueda: str) -> str | None:
    """
    Abre url_busqueda con Playwright, espera la primera imagen del CDN de
    Walmart (compartido por Walmart MX y Bodega Aurrera) y devuelve su src.

    Estrategia:
      1. Navegar a la página de búsqueda (domcontentloaded)
      2. Esperar selector `img[src*="walmartimages.com"]` visible
      3. Preferir resolución alta: intercambiar /thumbnail/ → /large/
    """
    browser = _get_pw_browser()
    if not browser:
        return None

    page = None
    try:
        page = browser.new_page()
        page.set_extra_http_headers({"Accept-Language": "es-MX,es;q=0.9"})
        # User-Agent de Chrome real para evitar bloqueos
        page.set_extra_http_headers({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "es-MX,es;q=0.9",
        })

        page.goto(url_busqueda, wait_until="domcontentloaded", timeout=TIMEOUT_PLAYWRIGHT)

        # Esperar primera imagen del CDN de Walmart (ambos sitios lo comparten)
        img_elem = page.wait_for_selector(
            'img[src*="walmartimages.com"]',
            state="visible",
            timeout=TIMEOUT_PLAYWRIGHT,
        )
        if not img_elem:
            return None

        src = img_elem.get_attribute("src") or ""

        # Walmart a veces sirve thumbnails en la búsqueda; intentar versión grande
        if "/thumbnail/" in src:
            src = src.replace("/thumbnail/", "/large/")
        elif "_thumbnail." in src:
            src = re.sub(r"_thumbnail(\.\w+)$", r"\1", src)

        return src if src.startswith("http") else None

    except Exception as e:
        log.debug("Playwright '%s': %s", url_busqueda[:80], e)
        return None
    finally:
        if page:
            try:
                page.close()
            except Exception:
                pass

# ══════════════════════════════════════════════════════════════
# UTILIDADES
# ══════════════════════════════════════════════════════════════

def slugify(texto: str) -> str:
    texto = unicodedata.normalize("NFD", texto)
    texto = texto.encode("ascii", "ignore").decode("ascii")
    texto = re.sub(r"[^\w\s]", "", texto.lower())
    texto = re.sub(r"\s+", "_", texto.strip())
    return texto[:60]


def limpiar_nombre(nombre: str) -> str:
    """'Leche Santa Clara 1L' → 'Leche Santa Clara'"""
    limpio = re.sub(
        r"\s+\d+(\.\d+)?\s*(kg|g|lt?|ml|pzas?|doc|paq|c\/u|r)\.?$",
        "", nombre, flags=re.IGNORECASE,
    ).strip()
    return limpio or nombre


def descargar_imagen(url: str) -> bytes | None:
    try:
        resp = requests.get(
            url,
            headers={"User-Agent": "TiendaInteligente/2.0 (contacto@agencia.ia)"},
            timeout=TIMEOUT_FUENTE,
        )
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

def buscar_en_off(nombre: str) -> str | None:
    """Fuente 1 — Open Food Facts API."""
    termino = limpiar_nombre(nombre)
    try:
        resp = requests.get(
            "https://world.openfoodfacts.org/cgi/search.pl",
            params={
                "search_terms": termino,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 5,
                "fields": "product_name,image_front_url,image_url",
                "lc": "es",
            },
            timeout=TIMEOUT_FUENTE,
        )
        resp.raise_for_status()
        for p in resp.json().get("products", []):
            img = p.get("image_front_url") or p.get("image_url")
            if img and img.startswith("http"):
                return img
    except Exception as e:
        log.debug("OFF '%s': %s", termino, e)
    return None


def buscar_en_walmart(nombre: str) -> str | None:
    """Fuente 2 — Walmart México con Playwright (headless Chromium)."""
    termino = limpiar_nombre(nombre)
    url = f"https://www.walmart.com.mx/buscar?q={quote_plus(termino)}"
    return _scrape_con_playwright(url)


def buscar_en_aurrera(nombre: str) -> str | None:
    """Fuente 3 — Bodega Aurrera con Playwright (headless Chromium)."""
    termino = limpiar_nombre(nombre)
    url = f"https://www.bodegas-aurrera.com.mx/buscar?q={quote_plus(termino)}"
    return _scrape_con_playwright(url)


# Cascada ordenada: (nombre_fuente, función)
FUENTES: list[tuple[str, callable]] = [
    ("Open Food Facts", buscar_en_off),
    ("Walmart MX",      buscar_en_walmart),
    ("Bodega Aurrera",  buscar_en_aurrera),
]


def buscar_imagen(nombre: str) -> tuple[str, str] | tuple[None, None]:
    """
    Prueba cada fuente en orden.
    Retorna (url_imagen, nombre_fuente) o (None, None) si todas fallan.
    """
    for nombre_fuente, fn in FUENTES:
        try:
            url = fn(nombre)
            if url:
                return url, nombre_fuente
        except Exception as e:
            log.debug("[%s] excepción inesperada: %s", nombre_fuente, e)
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
# SUPABASE — Storage y UPDATE
# ══════════════════════════════════════════════════════════════

def subir_a_storage(
    supabase_client, producto_id: int, nombre: str, img_bytes: bytes
) -> str | None:
    filename = f"{producto_id}_{slugify(nombre)}.png"
    try:
        supabase_client.storage.from_(STORAGE_BUCKET).upload(
            path=filename,
            file=img_bytes,
            file_options={"content-type": "image/png", "upsert": "true"},
        )
        return supabase_client.storage.from_(STORAGE_BUCKET).get_public_url(filename)
    except Exception as e:
        log.error("  Error subiendo a Storage: %s", e)
        return None


def actualizar_imagen_url(supabase_client, producto_id: int, url: str) -> bool:
    try:
        supabase_client.table("catalogo_productos") \
            .update({"imagen_url": url}) \
            .eq("id", producto_id) \
            .execute()
        return True
    except Exception as e:
        log.error("  Error actualizando DB: %s", e)
        return False

# ══════════════════════════════════════════════════════════════
# PROCESAMIENTO POR PRODUCTO
# ══════════════════════════════════════════════════════════════

def procesar_producto(supabase_client, producto: dict) -> tuple[str, str | None]:
    """
    Ejecuta el pipeline completo para un producto.
    Retorna: ('ok'|'skip'|'error', fuente_usada|None)
    Nunca lanza excepción — todos los errores son capturados internamente.
    """
    pid    = producto["id"]
    nombre = producto["nombre"]

    # 1. Buscar imagen en cascada
    img_url_origen, fuente = buscar_imagen(nombre)
    if not img_url_origen:
        log.info("  ⏭  Sin imagen en ninguna fuente")
        return "skip", None

    log.info("  📷 Fuente: %s", fuente)

    # 2. Descargar
    img_bytes_orig = descargar_imagen(img_url_origen)
    if not img_bytes_orig:
        log.warning("  ⚠  No se pudo descargar la imagen")
        return "error", fuente

    # 3. Procesar (rembg + Pillow)
    try:
        img_final = procesar_imagen(img_bytes_orig)
        log.info("  🔧 Procesada: %d KB", len(img_final) // 1024)
    except Exception as e:
        log.error("  Error en procesamiento: %s", e)
        return "error", fuente

    # 4. Subir a Supabase Storage
    url_publica = subir_a_storage(supabase_client, pid, nombre, img_final)
    if not url_publica:
        return "error", fuente

    # 5. Actualizar DB
    if not actualizar_imagen_url(supabase_client, pid, url_publica):
        return "error", fuente

    log.info("  ✅ Listo → %s...", url_publica[:80])
    return "ok", fuente

# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    SEP = "=" * 65

    log.info(SEP)
    log.info("  TIENDA INTELIGENTE — Pipeline de Imágenes v2")
    log.info("  Batch: %d | Pausa prod: %ds | Pausa lote: %ds | PW timeout: %dms",
             BATCH_SIZE, PAUSA_ENTRE_PRODUCTOS, PAUSA_ENTRE_LOTES, TIMEOUT_PLAYWRIGHT)
    log.info(SEP)

    # Conectar a Supabase
    log.info("Conectando a Supabase...")
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    log.info("Conexion establecida.")

    # Obtener productos sin imagen (idempotente)
    log.info("Buscando productos sin imagen...")
    try:
        resp = (
            supabase.table("catalogo_productos")
            .select("id, nombre, categoria")
            .or_('imagen_url.is.null,imagen_url.eq.""')
            .order("id")
            .execute()
        )
        productos = resp.data
    except Exception as e:
        log.error("Error consultando Supabase: %s", e)
        sys.exit(1)

    if not productos:
        log.info("Todos los productos ya tienen imagen. Nada que procesar.")
        return

    total   = len(productos)
    n_lotes = (total + BATCH_SIZE - 1) // BATCH_SIZE
    log.info("%d producto(s) sin imagen — %d lote(s) de hasta %d",
             total, n_lotes, BATCH_SIZE)
    log.info("IDs pendientes: %s\n", [p["id"] for p in productos])

    # Contadores globales
    ok_total   = 0
    skip_total = 0
    err_total  = 0
    fuentes_usadas: dict[str, int] = {}

    try:
        # ── Procesar en lotes ─────────────────────────────────
        for lote_idx in range(n_lotes):
            inicio = lote_idx * BATCH_SIZE
            lote   = productos[inicio: inicio + BATCH_SIZE]

            log.info("\n%s", "─" * 65)
            log.info("  LOTE %d/%d — productos %d-%d de %d",
                     lote_idx + 1, n_lotes,
                     inicio + 1, inicio + len(lote), total)
            log.info("%s", "─" * 65)

            for i, producto in enumerate(lote, start=1):
                pid    = producto["id"]
                nombre = producto["nombre"]
                cat    = producto.get("categoria", "—")
                global_idx = inicio + i

                log.info("\n[%d/%d] %s (ID %d, %s)", global_idx, total, nombre, pid, cat)

                resultado, fuente = procesar_producto(supabase, producto)

                if resultado == "ok":
                    ok_total += 1
                    fuentes_usadas[fuente] = fuentes_usadas.get(fuente, 0) + 1
                elif resultado == "skip":
                    skip_total += 1
                else:
                    err_total += 1

                # Pausa entre productos (excepto el último del lote)
                if i < len(lote):
                    time.sleep(PAUSA_ENTRE_PRODUCTOS)

            # Pausa entre lotes (excepto el último)
            if lote_idx < n_lotes - 1:
                log.info(
                    "\n  Lote %d/%d completado. Pausa de %ds...",
                    lote_idx + 1, n_lotes, PAUSA_ENTRE_LOTES,
                )
                time.sleep(PAUSA_ENTRE_LOTES)

    finally:
        # Siempre cerrar Playwright aunque el pipeline falle
        _close_pw_browser()

    # ── Resumen final ─────────────────────────────────────────
    log.info("\n%s", SEP)
    log.info("  RESUMEN FINAL")
    log.info("  Procesados correctamente : %d", ok_total)
    log.info("  Sin fuente de imagen     : %d", skip_total)
    log.info("  Errores                  : %d", err_total)
    log.info("  Total productos          : %d", total)

    if fuentes_usadas:
        log.info("\n  Fuentes utilizadas:")
        for fuente, count in sorted(fuentes_usadas.items(), key=lambda x: -x[1]):
            log.info("    %-20s %d imagen(es)", fuente, count)

    log.info(SEP)

    if ok_total > 0:
        log.info("\nListo. Log completo en: procesar_fotos.log")


if __name__ == "__main__":
    main()
