# Flujo de Imágenes de Productos — Super 10

## Resumen

Este documento describe el proceso completo para tomar fotos de productos de una tienda de abarrotes, procesarlas, subirlas a Supabase Storage y vincularlas al catálogo. También cubre el flujo de matching difuso cuando se recibe un CSV de inventario de una tienda nueva.

---

## 1. Captura de fotos

Tomar foto del producto con celular. No importa mucho el fondo porque se elimina después. Convención de nombres: `nombre_producto_gramaje.ext` (ej: `sabritas_adobadas_42g.jpg`).

Guardar en la carpeta correspondiente dentro de `FOTOS - PRODUCTOS/`:

```
Modulo_Tienda_Abarrotes/
  FOTOS - PRODUCTOS/
    Botanas/          ← fotos originales + processed/
    Bebidas/
    Enlatados/
    [nueva categoría]/
```

---

## 2. Procesamiento de imagen

### Herramienta: rembg (remove background)

Usamos rembg porque da los mejores resultados con empaques mexicanos (fondos irregulares, reflejos en bolsas metálicas, etc.). Se probó también con threshold de Pillow pero el resultado era inferior.

**Instalación (una vez):**
```bash
cd C:\Users\USER\Desktop\Agencia_IA
venv\Scripts\activate
pip install rembg[gpu]
```

**Uso:**
```bash
rembg i foto_original.jpg foto_sin_fondo.png
```

O en lote para toda una carpeta:
```bash
rembg p carpeta_entrada/ carpeta_salida/
```

### Estándar de calidad

Las imágenes deben cumplir con el estándar visual del catálogo existente:

| Parámetro | Valor |
|-----------|-------|
| Formato de salida | `.png` (transparencia) o `.webp` |
| Resolución mínima | 400×400 px |
| Fondo | Transparente (PNG) o blanco |
| Tamaño archivo | 15-350 KB |
| Contenido | Producto centrado, sin recortes |

---

## 3. Subida a Supabase Storage

### Opción A — Dashboard (más fácil)

1. Ir a [Supabase Dashboard](https://supabase.com/dashboard) → proyecto → **Storage** → bucket **productos**
2. Navegar a la subcarpeta de la categoría (ej: `botanas/`)
3. Click **Upload files** → seleccionar las imágenes procesadas
4. El bucket es **PUBLIC**, las URLs son accesibles sin autenticación

### Opción B — Script Python

```bash
cd Modulo_Tienda_Abarrotes/scripts
set SUPABASE_SERVICE_KEY=tu_service_role_key_aqui
python upload_botanas.py
```

La service_role key se encuentra en: **Supabase Dashboard → Settings → API → service_role (secret)**

### Estructura en Storage

```
productos/                    ← bucket público
  1_leche_santa_clara_1l.webp
  2_huevos_san_juan_12pzs.webp
  ...
  botanas/
    Chettos_torciditos_55g.png
    Crujitos_36g.png
    Rufles_Mega_Crunch_50g.png
    Rufles_Queso_48g.png
    Sabritas_adobadas.png
  bebidas/
    ...
```

### URL pública

```
https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/{ruta_archivo}
```

---

## 4. Actualizar base de datos

Después de subir las imágenes, actualizar el campo `imagen_url` en `catalogo_productos` con la URL pública del archivo en Storage.

**Desde SQL Editor de Supabase:**

```sql
UPDATE catalogo_productos
SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/botanas/Sabritas_adobadas.png'
WHERE id = 413;
```

---

## 5. Matching difuso — CSV de tienda nueva

Cuando se recibe un CSV de inventario capturado a mano (nombres con abreviaturas, errores, formato variable), usamos el script `match_csv_productos.py` para cruzar automáticamente contra el catálogo existente.

### Uso

```bash
cd Modulo_Tienda_Abarrotes/scripts
python match_csv_productos.py inventario_nueva_tienda.csv
```

### Qué hace

1. Lee el CSV (detecta automáticamente delimitador, encoding y columnas)
2. Normaliza nombres: minúsculas, sin acentos, expande abreviaturas ("grs" → "g", "lt" → "l", "adob." → "adobadas", "chettos" → "cheetos")
3. Para cada producto del CSV, lo compara contra todo el catálogo con un score compuesto:
   - 40% similitud de secuencia (orden de palabras)
   - 35% similitud de tokens (palabras clave)
   - 25% coincidencia de gramaje
4. Clasifica en 3 categorías:
   - **✅ Match automático (≥85%):** se asigna imagen directo
   - **🟡 Match sugerido (60-84%):** tú confirmas
   - **❌ Sin match (<60%):** revisión manual, foto nueva
5. Exporta resultados a CSV (`match_resultados_YYYYMMDD.csv`)

### Rendimiento probado

Con un CSV de prueba de 25 productos escritos como los escribiría un tendero:

| Resultado | Cantidad | % |
|-----------|----------|---|
| Match automático | 21 | 84% |
| Match sugerido | 3 | 12% |
| Sin match | 1 | 4% |

Ejemplos de matches exitosos:

| CSV (tendero escribió) | Catálogo (match encontrado) | Score |
|------------------------|----------------------------|-------|
| Chettos Torciditos 55grs | Cheetos Torciditos 55g | 100% |
| Sabritas Adob. 42g | Sabritas Adobadas 42g | 100% |
| Leche Sta Clara 1lt | Leche Santa Clara 1L | 100% |
| Pan Bimbo Blco 680g | Pan Bimbo Blanco 680g | 100% |
| Rufles Mega Crunch 50gr | Ruffles Mega Crunch 50g | 100% |

### Formato del CSV de entrada

El script detecta automáticamente las columnas. Headers aceptados:

- Nombre: `nombre`, `producto`, `descripcion`, `articulo`, `item`
- Precio: `precio`, `price`, `costo`, `valor`
- Código: `codigo`, `code`, `ean`, `upc`, `barcode`, `sku`
- Categoría: `categoria`, `category`, `depto`, `departamento`

Ejemplo mínimo:
```csv
nombre,precio
Leche Sta Clara 1lt,28.50
Sabritas Adob. 42g,18.50
```

---

## 6. Flujo completo para tienda nueva

```
1. Recibir CSV de inventario de la tienda
2. Correr match_csv_productos.py
3. Revisar reporte:
   - Automáticos → ya tienen imagen del catálogo existente
   - Sugeridos → confirmar manualmente
   - Sin match → son productos nuevos:
     a. Agregar al catálogo en Supabase
     b. Tomar foto del producto
     c. Procesar con rembg
     d. Subir a Storage
     e. Actualizar imagen_url
4. Conforme se agregan tiendas, el catálogo crece
   y el % de match automático sube
```

---

## 7. Despliegue a producción

### Infraestructura actual (todo gratis)

| Servicio | Plan | Costo | Uso |
|----------|------|-------|-----|
| Cloudflare Pages | Free | $0 | Hosting del frontend (tienda + POS) |
| Supabase | Free | $0 | Base de datos + Storage de imágenes |
| GitHub | Free (repo privado) | $0 | Código fuente |
| n8n | Local | $0 | Workflows (webhook tienda personalizada) |

### URLs en producción

- **Tienda online:** `https://super-10.pages.dev/tienda`
- **Punto de venta:** `https://super-10.pages.dev/pos`
- **QR Generator:** `https://super-10.pages.dev/qr.html`

### Deploy automático

El repo `javierm06-alt/super-10` está conectado a Cloudflare Pages con deploy automático en branch `main`. Cada `git push origin main` dispara un nuevo deploy en segundos.

```bash
# Desde Modulo_Tienda_Abarrotes/
git add [archivos]
git commit -m "descripción del cambio"
git push origin main
# Cloudflare detecta y despliega automáticamente
```

### Escalabilidad multi-tienda

Con un solo proyecto de Supabase se pueden manejar múltiples tiendas usando `tienda_id` como discriminador. Si se llega al límite del free tier:

- **Supabase Pro ($25/mes):** 8GB DB + 100GB Storage + 250GB bandwidth — suficiente para 10+ tiendas
- **Cloudflare Pages:** ilimitado en el free tier

---

## 8. POS — Funcionalidades

### Flujo de cobro (con confirmación)

```
Agregar productos al carrito
  → Click "Cobrar $X.XX"
    → Modal de VISTA PREVIA (banner amarillo "La venta NO se ha registrado aún")
      → ✅ Confirmar Venta  →  guarda en Supabase + ticket + "Gracias por su compra"
      → ❌ Cancelar          →  cierra modal, carrito intacto, NO registra nada
```

Esto evita ventas accidentales: si el cliente se arrepintió o se equivocó, el tendero cancela sin que quede registrada.

### Versión móvil

El POS es responsive y funciona en celular/tablet:

- Los productos ocupan toda la pantalla en grid compacta (3 columnas en <400px)
- Botón flotante 🛒 (FAB) abajo a la derecha con badge de cantidad y total
- Al tocar el FAB, sube un drawer con el carrito desde abajo (85% de pantalla)
- Header compacto, barra de atajos oculta (no aplica en touch)
- Modal de recibo adaptado a pantalla pequeña

---

## Archivos del proyecto

| Archivo | Descripción |
|---------|-------------|
| `pos.html` | Punto de venta completo (responsive, cobro con confirmación) |
| `tienda.html` | Tienda online para clientes (mobile-first) |
| `qr.html` | Generador de códigos QR para la tienda |
| `admin.html` | Panel de administración |
| `scripts/match_csv_productos.py` | Script de matching difuso CSV → catálogo |
| `scripts/procesar_fotos.py` | Pipeline de procesamiento de imágenes |
| `scripts/upload_botanas.py` | Script de upload a Supabase Storage |
| `scripts/ejemplo_inventario_tienda.csv` | CSV de prueba con nombres "de tendero" |
| `docs/flujo_imagenes_productos.md` | Este documento |
| `.gitignore` | Excluye fotos, videos, CLAUDE.md, archivos dev |
| `_headers` | Cache headers para Cloudflare Pages |
| `FOTOS - PRODUCTOS/` | Fotos originales y procesadas por categoría |
