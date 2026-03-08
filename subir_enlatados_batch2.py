"""
subir_enlatados_batch2.py
─────────────────────────────────────────────────────────────────
Sube los 15 productos PENDIENTES de Enlatados a Supabase Storage
y actualiza imagen_url en catalogo_productos.

Los 16 productos anteriores (Catsup_Heinz, gelatinas Gari, etc.)
ya estaban subidos — este script NO los toca.

Uso:
    1. Copia este script a la carpeta del proyecto
    2. Pon las 15 imágenes .webp en FOTOS_DIR (o en la misma carpeta que el script)
    3. Ejecuta: python subir_enlatados_batch2.py
─────────────────────────────────────────────────────────────────
"""

import os
import requests

# ── Configuración ──────────────────────────────────────────────
SUPABASE_URL = "https://dqrhqzdfzhkqpgawgjga.supabase.co"
SUPABASE_KEY = "sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ"
BUCKET       = "productos"

FOTOS_DIR = r"C:\Users\USER\Desktop\Agencia_IA\Modulo_Tienda_Abarrotes\FOTOS - PRODUCTOS"

HEADERS = {
    "apikey":        SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}

# ── Mapeo: archivo local → storage_key (ASCII puro) → nombre exacto en DB ─────
# Si el nombre_db no coincide con tu tabla, corrígelo antes de correr el script.
# Usa: SELECT nombre FROM catalogo_productos WHERE categoria = 'Enlatados';
PRODUCTOS = [
    {
        "archivo":    "Gelatina_Limon.webp",
        "storage_key":"Gelatina_Limon.webp",
        "nombre_db":  "Gelatina Limon",
    },
    {
        "archivo":    "Gelatina_Uva.webp",
        "storage_key":"Gelatina_Uva.webp",
        "nombre_db":  "Gelatina Uva",
    },
    {
        "archivo":    "Granos_De_Elote_220g_Herdez.webp",
        "storage_key":"Granos_De_Elote_220g_Herdez.webp",
        "nombre_db":  "Granos De Elote 220g Herdez",
    },
    {
        "archivo":    "Huevo.webp",
        "storage_key":"Huevo.webp",
        "nombre_db":  "Huevo",
    },
    {
        "archivo":    "Jalapeños_En_Rajas_La_Costeña_220_G.webp",
        "storage_key":"Jalapenos_En_Rajas_La_Costena_220_G.webp",
        "nombre_db":  "Jalapeños En Rajas La Costeña 220 G",
    },
    {
        "archivo":    "Jalapeños_Enteros_La_Costeña_220_G.webp",
        "storage_key":"Jalapenos_Enteros_La_Costena_220_G.webp",
        "nombre_db":  "Jalapeños Enteros La Costeña 220 G",
    },
    {
        "archivo":    "Mole_Verde_Doña_Maria.webp",
        "storage_key":"Mole_Verde_Dona_Maria.webp",
        "nombre_db":  "Mole Verde Doña Maria",
    },
    {
        "archivo":    "Nachos_Jalapeños_220g_La_Costeña.webp",
        "storage_key":"Nachos_Jalapenos_220g_La_Costena.webp",
        "nombre_db":  "Nachos Jalapeños 220g La Costeña",
    },
    {
        "archivo":    "Rajas_Verdes_La_Costeña_105g.webp",
        "storage_key":"Rajas_Verdes_La_Costena_105g.webp",
        "nombre_db":  "Rajas Verdes La Costeña 105g",
    },
    {
        "archivo":    "Salsa_Guacamole_Picante.webp",
        "storage_key":"Salsa_Guacamole_Picante.webp",
        "nombre_db":  "Salsa Guacamole Picante",
    },
    {
        "archivo":    "Salsa_Inglesa_Crosse___Blackwell.webp",
        "storage_key":"Salsa_Inglesa_Crosse_Blackwell.webp",
        "nombre_db":  "Salsa Inglesa Crosse & Blackwell",
    },
    {
        "archivo":    "Salsa_Taquera_Herdez.webp",
        "storage_key":"Salsa_Taquera_Herdez.webp",
        "nombre_db":  "Salsa Taquera Herdez",
    },
    {
        "archivo":    "Tomates_Molidos_Condimentados_Del_Fuerte.webp",
        "storage_key":"Tomates_Molidos_Condimentados_Del_Fuerte.webp",
        "nombre_db":  "Tomates Molidos Condimentados Del Fuerte",
    },
    {
        "archivo":    "Vinagre_Blanco_Clemente_Jacques.webp",
        "storage_key":"Vinagre_Blanco_Clemente_Jacques.webp",
        "nombre_db":  "Vinagre Blanco Clemente Jacques",
    },
    {
        "archivo":    "Vinagre_Clemente_Jacques_Manzana.webp",
        "storage_key":"Vinagre_Clemente_Jacques_Manzana.webp",
        "nombre_db":  "Vinagre Clemente Jacques Manzana 500 Ml",
    },
]

# ── Helpers ────────────────────────────────────────────────────

def subir_imagen(storage_key: str, ruta_local: str) -> str | None:
    url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{storage_key}"
    with open(ruta_local, "rb") as f:
        resp = requests.post(
            url,
            headers={**HEADERS, "Content-Type": "image/webp"},
            data=f,
        )
    if resp.status_code in (200, 201):
        return f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_key}"
    else:
        print(f"    ✗ Storage error {resp.status_code}: {resp.text}")
        return None


def actualizar_imagen_url(nombre_db: str, imagen_url: str) -> bool:
    url = (
        f"{SUPABASE_URL}/rest/v1/catalogo_productos"
        f"?nombre=eq.{requests.utils.quote(nombre_db)}"
    )
    resp = requests.patch(
        url,
        headers={**HEADERS, "Content-Type": "application/json", "Prefer": "return=minimal"},
        json={"imagen_url": imagen_url},
    )
    return resp.status_code in (200, 204)


# ── Main ───────────────────────────────────────────────────────

def main():
    ok, fail = [], []

    for p in PRODUCTOS:
        ruta = os.path.join(FOTOS_DIR, p["archivo"])

        # Fallback: buscar en el mismo directorio que el script
        if not os.path.exists(ruta):
            ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), p["archivo"])

        if not os.path.exists(ruta):
            print(f"[SKIP] No encontrado: {p['archivo']}")
            fail.append(p["archivo"])
            continue

        print(f"[→] Subiendo: {p['archivo']}")
        imagen_url = subir_imagen(p["storage_key"], ruta)

        if not imagen_url:
            fail.append(p["archivo"])
            continue

        print(f"    ✓ Storage OK")

        if actualizar_imagen_url(p["nombre_db"], imagen_url):
            print(f"    ✓ DB actualizada: {p['nombre_db']}")
            ok.append(p["archivo"])
        else:
            print(f"    ✗ DB falló (RLS): {p['nombre_db']} → usa SQL Editor")
            fail.append(p["archivo"])

    print("\n─────────────────────────────")
    print(f"✅ OK:    {len(ok)}/15")
    print(f"❌ Falló: {len(fail)}/15")
    if fail:
        print("Fallidos:", fail)
        print("\nSi DB falló por RLS, corre el archivo SQL de respaldo en Supabase SQL Editor.")


if __name__ == "__main__":
    main()
