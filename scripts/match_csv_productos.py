"""
match_csv_productos.py — Matching difuso de CSV contra catálogo Supabase
=========================================================================
Lee un CSV de inventario de tienda (capturado a mano) y lo cruza contra
el catálogo existente en Supabase usando fuzzy matching.

Genera 3 categorías:
  ✅ Match automático   (score >= 85%)  → se asigna imagen directo
  🟡 Match sugerido     (score 60-84%) → tú confirmas
  ❌ Sin match          (score < 60%)   → se queda para revisión manual

Ejecutar:
  cd C:/Users/USER/Desktop/Agencia_IA
  venv\\Scripts\\activate
  cd Modulo_Tienda_Abarrotes/scripts
  python match_csv_productos.py inventario_tienda.csv

Salida:
  - Reporte en consola con resumen
  - CSV de resultados: match_resultados_YYYYMMDD.csv
  - Log detallado: match_csv.log
"""

import csv
import io
import logging
import os
import re
import sys
import unicodedata
from datetime import datetime
from difflib import SequenceMatcher

# Fix encoding Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import requests

# ══════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ══════════════════════════════════════════════════════════════

SUPABASE_URL = "https://dqrhqzdfzhkqpgawgjga.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRxcmhxemRmemhrcXBnYXdnamdhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEzMTcyMTUsImV4cCI6MjA2Njg5MzIxNX0.sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ"

# Umbrales de confianza
UMBRAL_AUTO = 85       # >= 85% → match automático
UMBRAL_SUGERIDO = 60   # >= 60% → match sugerido (confirmar)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("match_csv.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

# ══════════════════════════════════════════════════════════════
# ABREVIATURAS COMUNES EN TIENDAS MEXICANAS
# ══════════════════════════════════════════════════════════════

ABREVIATURAS = {
    # Unidades
    "gr": "g", "grs": "g", "grms": "g", "gramos": "g",
    "kg": "kg", "kgs": "kg", "kilos": "kg", "kilogramos": "kg",
    "lt": "l", "lts": "l", "litro": "l", "litros": "l",
    "ml": "ml", "mls": "ml", "mililitros": "ml",
    "pz": "pz", "pzs": "pz", "pzas": "pz", "pieza": "pz", "piezas": "pz",
    "rollo": "r", "rollos": "r",
    "paq": "paq", "paquete": "paq", "paquetes": "paq", "pk": "paq", "pack": "paq",
    # Productos comunes
    "adob": "adobadas", "adob.": "adobadas",
    "choc": "chocolate", "choc.": "chocolate",
    "desc": "descremada", "desc.": "descremada",
    "nat": "natural", "nat.": "natural",
    "orig": "original", "orig.": "original",
    "torc": "torciditos", "torc.": "torciditos",
    "flam": "flamin", "flam.": "flamin",
    "enchil": "enchiladas", "enchil.": "enchiladas",
    # Marcas con variantes de escritura
    "chettos": "cheetos",
    "rufles": "ruffles",
    "sabritas": "sabritas",
    "lala": "lala",
    "bimbo": "bimbo",
    "nescafe": "nescafe",
    "coca": "coca cola",
    "coca-cola": "coca cola",
    "cocacola": "coca cola",
    "pep": "pepsi",
}

# ══════════════════════════════════════════════════════════════
# FUNCIONES DE NORMALIZACIÓN
# ══════════════════════════════════════════════════════════════

def quitar_acentos(texto: str) -> str:
    """Remueve acentos/diacríticos: á→a, ñ→n, ü→u"""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_nombre(nombre: str) -> str:
    """
    Normalización agresiva para matching:
    - Minúsculas, sin acentos
    - Expande abreviaturas comunes
    - Limpia caracteres especiales
    - Normaliza espacios
    """
    if not nombre:
        return ""

    texto = nombre.strip().lower()
    texto = quitar_acentos(texto)

    # Quitar caracteres especiales excepto letras, números, espacios y puntos
    texto = re.sub(r"[^\w\s.]", " ", texto)

    # Separar números pegados a letras: "42g" → "42 g", "1l" → "1 l"
    texto = re.sub(r"(\d+)\s*([a-z])", r"\1 \2", texto)
    texto = re.sub(r"([a-z])\s*(\d+)", r"\1 \2", texto)

    # Expandir abreviaturas
    palabras = texto.split()
    expandidas = []
    for p in palabras:
        p_limpia = p.rstrip(".")
        if p_limpia in ABREVIATURAS:
            expandidas.append(ABREVIATURAS[p_limpia])
        elif p in ABREVIATURAS:
            expandidas.append(ABREVIATURAS[p])
        else:
            expandidas.append(p)

    texto = " ".join(expandidas)

    # Normalizar espacios múltiples
    texto = re.sub(r"\s+", " ", texto).strip()

    return texto


def extraer_gramaje(nombre: str) -> str:
    """Extrae el gramaje/volumen normalizado: '42g', '1l', '500ml', etc."""
    nombre_norm = quitar_acentos(nombre.lower())
    # Buscar patrones como "42g", "1.5l", "500ml", "1kg", "12pz"
    match = re.search(r"(\d+\.?\d*)\s*(g|kg|l|ml|pz|r|paq)\b", nombre_norm)
    if match:
        return f"{match.group(1)}{match.group(2)}"
    return ""


def extraer_tokens_clave(nombre_normalizado: str) -> set:
    """Extrae tokens significativos (ignora stopwords y unidades)."""
    stopwords = {"de", "del", "la", "el", "las", "los", "en", "con", "para",
                 "y", "o", "a", "un", "una", "su", "al", "por", "mas", "x"}
    unidades = {"g", "kg", "l", "ml", "pz", "r", "paq"}

    tokens = set()
    for palabra in nombre_normalizado.split():
        # Ignorar stopwords, unidades sueltas y números solos
        if palabra in stopwords or palabra in unidades or palabra.isdigit():
            continue
        if len(palabra) >= 2:  # Ignorar tokens de 1 caracter
            tokens.add(palabra)
    return tokens


# ══════════════════════════════════════════════════════════════
# ALGORITMOS DE MATCHING
# ══════════════════════════════════════════════════════════════

def score_secuencia(a: str, b: str) -> float:
    """SequenceMatcher ratio (0-100)."""
    return SequenceMatcher(None, a, b).ratio() * 100


def score_tokens(tokens_a: set, tokens_b: set) -> float:
    """Jaccard similarity de tokens (0-100)."""
    if not tokens_a or not tokens_b:
        return 0.0
    interseccion = tokens_a & tokens_b
    union = tokens_a | tokens_b
    return (len(interseccion) / len(union)) * 100


def score_gramaje(gram_a: str, gram_b: str) -> float:
    """100 si coincide gramaje, 0 si no, 50 si alguno está vacío."""
    if not gram_a or not gram_b:
        return 50  # No penalizar si falta el dato
    return 100 if gram_a == gram_b else 0


def calcular_score_total(nombre_csv: str, nombre_catalogo: str) -> dict:
    """
    Score compuesto ponderado:
      - 40% similitud de secuencia (captura orden de palabras)
      - 35% similitud de tokens (captura palabras clave sin importar orden)
      - 25% match de gramaje (tamaño correcto del producto)
    """
    norm_csv = normalizar_nombre(nombre_csv)
    norm_cat = normalizar_nombre(nombre_catalogo)

    tokens_csv = extraer_tokens_clave(norm_csv)
    tokens_cat = extraer_tokens_clave(norm_cat)

    gram_csv = extraer_gramaje(nombre_csv)
    gram_cat = extraer_gramaje(nombre_catalogo)

    s_seq = score_secuencia(norm_csv, norm_cat)
    s_tok = score_tokens(tokens_csv, tokens_cat)
    s_gram = score_gramaje(gram_csv, gram_cat)

    total = (s_seq * 0.40) + (s_tok * 0.35) + (s_gram * 0.25)

    return {
        "score_total": round(total, 1),
        "score_secuencia": round(s_seq, 1),
        "score_tokens": round(s_tok, 1),
        "score_gramaje": round(s_gram, 1),
        "nombre_csv_norm": norm_csv,
        "nombre_cat_norm": norm_cat,
        "gramaje_csv": gram_csv,
        "gramaje_cat": gram_cat,
        "tokens_csv": tokens_csv,
        "tokens_cat": tokens_cat,
    }


def encontrar_mejor_match(nombre_csv: str, catalogo: list) -> dict:
    """
    Compara un nombre de CSV contra todo el catálogo.
    Retorna el mejor match con su score y detalles.
    """
    mejor = None
    for producto in catalogo:
        resultado = calcular_score_total(nombre_csv, producto["nombre"])
        resultado["producto_catalogo"] = producto

        if mejor is None or resultado["score_total"] > mejor["score_total"]:
            mejor = resultado

    return mejor


# ══════════════════════════════════════════════════════════════
# LECTURA DE CSV
# ══════════════════════════════════════════════════════════════

def leer_csv(ruta: str) -> list:
    """
    Lee un CSV de inventario. Intenta detectar automáticamente
    la columna del nombre del producto.
    Soporta: nombre, producto, descripcion, articulo como header.
    """
    productos = []

    # Detectar encoding
    for enc in ["utf-8-sig", "utf-8", "latin-1", "cp1252"]:
        try:
            with open(ruta, "r", encoding=enc) as f:
                f.read()
            break
        except (UnicodeDecodeError, UnicodeError):
            continue

    with open(ruta, "r", encoding=enc) as f:
        # Detectar delimitador
        muestra = f.read(2048)
        f.seek(0)
        sniffer = csv.Sniffer()
        try:
            dialect = sniffer.sniff(muestra, delimiters=",;\t|")
        except csv.Error:
            dialect = csv.excel  # fallback a coma

        reader = csv.DictReader(f, dialect=dialect)

        # Encontrar la columna del nombre del producto
        headers = [h.strip().lower() for h in reader.fieldnames] if reader.fieldnames else []
        col_nombre = None
        col_precio = None
        col_codigo = None
        col_categoria = None

        for h_orig, h_lower in zip(reader.fieldnames or [], headers):
            if h_lower in ("nombre", "producto", "descripcion", "articulo", "item", "name"):
                col_nombre = h_orig
            elif h_lower in ("precio", "price", "costo", "valor", "p.v.", "pv"):
                col_precio = h_orig
            elif h_lower in ("codigo", "code", "ean", "upc", "barcode", "sku", "clave"):
                col_codigo = h_orig
            elif h_lower in ("categoria", "category", "depto", "departamento", "tipo"):
                col_categoria = h_orig

        if not col_nombre:
            log.error(f"No se encontró columna de nombre de producto en: {headers}")
            log.error("Headers esperados: nombre, producto, descripcion, articulo")
            sys.exit(1)

        log.info(f"Columna de nombre: '{col_nombre}'")
        if col_precio:
            log.info(f"Columna de precio: '{col_precio}'")
        if col_codigo:
            log.info(f"Columna de código: '{col_codigo}'")

        for row in reader:
            nombre = row.get(col_nombre, "").strip()
            if not nombre:
                continue

            producto = {
                "nombre_original": nombre,
                "precio": row.get(col_precio, "").strip() if col_precio else "",
                "codigo": row.get(col_codigo, "").strip() if col_codigo else "",
                "categoria": row.get(col_categoria, "").strip() if col_categoria else "",
            }
            productos.append(producto)

    log.info(f"Leídos {len(productos)} productos del CSV")
    return productos


# ══════════════════════════════════════════════════════════════
# CATÁLOGO DESDE SUPABASE
# ══════════════════════════════════════════════════════════════

def obtener_catalogo() -> list:
    """Descarga todo el catálogo de Supabase."""
    url = f"{SUPABASE_URL}/rest/v1/catalogo_productos?select=id,nombre,categoria,precio,unidad,imagen_url"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
    }

    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        log.error(f"Error al obtener catálogo: {resp.status_code} {resp.text}")
        sys.exit(1)

    catalogo = resp.json()
    con_imagen = sum(1 for p in catalogo if p.get("imagen_url"))
    log.info(f"Catálogo: {len(catalogo)} productos ({con_imagen} con imagen)")
    return catalogo


# ══════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════

def main():
    if len(sys.argv) < 2:
        print("Uso: python match_csv_productos.py <archivo.csv>")
        print("")
        print("Ejemplo:")
        print("  python match_csv_productos.py inventario_super10.csv")
        sys.exit(1)

    ruta_csv = sys.argv[1]
    if not os.path.exists(ruta_csv):
        log.error(f"Archivo no encontrado: {ruta_csv}")
        sys.exit(1)

    log.info("=" * 60)
    log.info("MATCHING DIFUSO: CSV vs CATÁLOGO SUPABASE")
    log.info("=" * 60)

    # 1. Leer CSV
    productos_csv = leer_csv(ruta_csv)

    # 2. Obtener catálogo
    catalogo = obtener_catalogo()

    # 3. Matching
    automaticos = []
    sugeridos = []
    sin_match = []

    for i, prod_csv in enumerate(productos_csv, 1):
        nombre = prod_csv["nombre_original"]
        resultado = encontrar_mejor_match(nombre, catalogo)

        match_info = {
            "csv_nombre": nombre,
            "csv_precio": prod_csv["precio"],
            "csv_codigo": prod_csv["codigo"],
            "csv_categoria": prod_csv["categoria"],
            "cat_id": resultado["producto_catalogo"]["id"],
            "cat_nombre": resultado["producto_catalogo"]["nombre"],
            "cat_precio": resultado["producto_catalogo"].get("precio", ""),
            "cat_imagen": resultado["producto_catalogo"].get("imagen_url", ""),
            "score": resultado["score_total"],
            "score_seq": resultado["score_secuencia"],
            "score_tok": resultado["score_tokens"],
            "score_gram": resultado["score_gramaje"],
        }

        if resultado["score_total"] >= UMBRAL_AUTO:
            match_info["estado"] = "AUTO"
            automaticos.append(match_info)
            emoji = "✅"
        elif resultado["score_total"] >= UMBRAL_SUGERIDO:
            match_info["estado"] = "SUGERIDO"
            sugeridos.append(match_info)
            emoji = "🟡"
        else:
            match_info["estado"] = "SIN_MATCH"
            sin_match.append(match_info)
            emoji = "❌"

        log.info(
            f"  [{i}/{len(productos_csv)}] {emoji} {nombre}"
            f" → {resultado['producto_catalogo']['nombre']}"
            f" ({resultado['score_total']}%)"
        )

    # 4. Reporte
    print("\n" + "=" * 60)
    print("RESUMEN DE MATCHING")
    print("=" * 60)
    print(f"  Total productos CSV:    {len(productos_csv)}")
    print(f"  ✅ Match automático:     {len(automaticos)}  (>= {UMBRAL_AUTO}%)")
    print(f"  🟡 Match sugerido:       {len(sugeridos)}  ({UMBRAL_SUGERIDO}-{UMBRAL_AUTO-1}%)")
    print(f"  ❌ Sin match:            {len(sin_match)}  (< {UMBRAL_SUGERIDO}%)")
    print("=" * 60)

    if automaticos:
        print(f"\n✅ MATCHES AUTOMÁTICOS ({len(automaticos)}):")
        for m in automaticos:
            tiene_img = "📷" if m["cat_imagen"] else "🚫"
            print(f"  {tiene_img} {m['csv_nombre']}")
            print(f"     → ID {m['cat_id']}: {m['cat_nombre']} ({m['score']}%)")

    if sugeridos:
        print(f"\n🟡 MATCHES SUGERIDOS — REQUIEREN CONFIRMACIÓN ({len(sugeridos)}):")
        for m in sugeridos:
            tiene_img = "📷" if m["cat_imagen"] else "🚫"
            print(f"  {tiene_img} {m['csv_nombre']}")
            print(f"     → ID {m['cat_id']}: {m['cat_nombre']} ({m['score']}%)")

    if sin_match:
        print(f"\n❌ SIN MATCH — REVISIÓN MANUAL ({len(sin_match)}):")
        for m in sin_match:
            print(f"  {m['csv_nombre']}")
            print(f"     Mejor candidato: {m['cat_nombre']} ({m['score']}%)")

    # 5. Exportar CSV de resultados
    fecha = datetime.now().strftime("%Y%m%d_%H%M")
    ruta_salida = f"match_resultados_{fecha}.csv"

    todos = automaticos + sugeridos + sin_match
    with open(ruta_salida, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "estado", "csv_nombre", "csv_precio", "csv_codigo", "csv_categoria",
            "cat_id", "cat_nombre", "cat_precio", "cat_imagen",
            "score", "score_seq", "score_tok", "score_gram"
        ])
        writer.writeheader()
        writer.writerows(todos)

    log.info(f"\nResultados exportados a: {ruta_salida}")

    # 6. Stats de imágenes
    con_imagen = sum(1 for m in automaticos if m["cat_imagen"])
    total_auto = len(automaticos)
    print(f"\nDe los {total_auto} matches automáticos, {con_imagen} ya tienen imagen.")
    if total_auto > con_imagen:
        print(f"  → {total_auto - con_imagen} productos matcheados necesitan imagen.")


if __name__ == "__main__":
    main()
