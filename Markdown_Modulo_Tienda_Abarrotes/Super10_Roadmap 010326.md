# Super 10 — Módulo Tienda Abarrotes
## Roadmap del Proyecto — v2

---

## ✅ tienda.html — Experiencia del Comprador

### Base técnica
- Frontend HTML/CSS/JS en un solo archivo
- Datos en Supabase (tabla `catalogo_productos`)
- Imágenes en Supabase Storage (bucket `productos`, público)
- Fetch en cascada: n8n webhook → Supabase directo como fallback
- Servidor local: `python -m http.server 8080`

### Navegación y catálogo
- Header con nombre dinámico desde `CONFIG.nombreTienda`
- Barra de categorías sticky con pills + scroll horizontal sin scrollbar
  - Inicio, Bebidas, Lácteos, Básicos, Frutas, Panadería, Enlatados, Abarrotes, Limpieza, Higiene
  - Navegación por `data-cat` (fiable, sin depender de textContent)
  - Botón Inicio restaura catálogo completo + scroll arriba
- Sección "Mis Favoritos" (scroll horizontal) con badges "USUAL"
- Sección "Explorar más" (grid 2 columnas)
- `catalogData` separado de `activeData` para que el filtro por categoría no corrompa el catálogo original

### Búsqueda
- Búsqueda fuzzy sin acentos con función `normalize()` (NFD + regex)
- Dropdown predictivo con hasta 5 sugerencias (imagen real o emoji)
- Botón ← para limpiar y volver al catálogo desde búsqueda
- Botón X a la derecha del input
- Blur en móvil: cierra dropdown pero mantiene resultados visibles

### Carrito
- Persistencia en localStorage
- Badge con conteo en ícono del carrito
- Drawer con: imagen, nombre, precio unitario, controles +/−, subtotal, botón ×
- Selector de entrega: 🏪 Recoger en tienda (activo) / 🚚 Envío a domicilio (Próximamente)
- Botón "Enviar por WhatsApp" con mensaje estructurado
- Botón "Pagar en línea — Próximamente" (deshabilitado, listo para Stripe)
- Botón "Vaciar carrito" al fondo del drawer

### Diseño
- Paleta: Azul marino `#1B4F8A` + Verde lima `#8BC34A`
- Fuentes: Varela Round + Nunito Sans
- PWA meta tags + manifest.json (iconos pendientes)
- Optimizado para móvil (max-width 480px centrado)

---

## ✅ admin.html — Panel del Tendero

### Estructura
- Mismo sistema de diseño que tienda.html (paleta, fuentes, cards)
- Header: nombre tienda + "Panel del Tendero" + botón "Ver mi tienda →"
- Bottom nav fijo con 4 tabs grandes (ícono 1.6rem, label .75rem):
  📦 Productos | 🎤 Voz | 📊 Salud | 🛒 Surtir
- Tab activo resalta con ícono 1.8rem

### Tab 📦 Productos
- Formulario completo: nombre, precio, costo, stock, categoría
- Subir foto / URL / buscar imagen
- Toggle: producto activo, destacado, control de inventario
- Etiquetas personalizadas
- Sección "Recién agregados" con mock data

### Tab 🎤 Voz — Inventario por voz
- Botón circular grande con animación de ondas pulsantes al escuchar
- Web Speech API (lang: 'es-MX') para uso real en móvil con HTTPS
- **Modo texto** para probar sin micrófono (input + botón "Probar →")
- Lógica de extracción inteligente de cantidad:
  - Palabras numéricas primero (uno, dos... doce, veinte...)
  - Dígitos solo si NO van seguidos de unidad de medida (lts, kg, ml, g, pzas...)
  - Ejemplo: "seis coca colas de 2 lts" → cantidad=6, ignora el 2
- Búsqueda por score de palabras clave, normalizada sin acentos
- Tarjeta de confirmación: foto grande + nombre + "¿Agregar X unidades?"
  - ✓ Sí → actualiza stock en memoria + toast + flash verde en tabla
  - ✗ No → picker manual con todos los productos
- **Tabla "Inventario actual"** siempre visible debajo:
  - Producto (imagen real o emoji) | Stock | Última actualización
  - Fila actualizada: flash verde claro por 3 segundos
  - Botón "Ver inventario ↓" para hacer scroll directo a la tabla

### Tab 📊 Salud del negocio
5 tarjetas en lenguaje de tendero (sin tecnicismos, todo en pesos):

| Tarjeta | Lógica | Ejemplo de texto |
|---------|--------|-----------------|
| 🏆 Tu campeón | Mayor `vendidos` | "Las Tortillas fueron tu estrella. Vendiste 31 — más de 4 al día" |
| 💰 Lo que más te deja | Mayor `(precio-costo)*vendidos` | "Por cada Café Nescafé te quedas $17.90. Esta semana te dejó $143.20" |
| ⚠️ Ojo con esto | `stock < 5` | Lista con "Te quedan X piezas" + texto alentador |
| 📈 Cómo va tu semana | Top 5 tabla | Producto \| Piezas \| Lo que te dejó ($) — emoji 🔥 al #1 |
| 💡 Tip de la semana | Ganancia alta + pocas ventas, o stock crítico + alta rotación | Consejo accionable en lenguaje simple |

### Tab 🛒 Surtir
- Cálculo: `dias_restantes = stock / (vendidos / 7)`
- 🔴 Urgente (< 2 días): card con emoji + nombre + días + cantidad sugerida (`vendidos * 2`)
- 🟡 Esta semana (2-5 días): misma card en amarillo
- 🟢 Estás bien (> 5 días): lista compacta
- Botón "✓ Ya surtí" → +20 stock en memoria + re-renderiza semáforo
- Botón "📋 Enviar lista al proveedor por WhatsApp" → abre `wa.me/525513222091` con mensaje formateado

---

## 🔧 Bugs documentados y resueltos

| Bug | Causa | Solución |
|-----|-------|----------|
| RLS bloquea UPDATE silenciosamente | Sin política UPDATE para anon | SQL Editor (postgres bypasea RLS) |
| Bucket Storage privado da 404 | Default privado | `UPDATE storage.buckets SET public = true WHERE id = 'productos'` |
| Categoría Inicio no funcionaba | `textContent.includes()` frágil | `data-cat=""` + comparación exacta `p.dataset.cat === ''` |
| Filtro categoría corrompe catálogo | `activeData` se sobreescribía | Variable `catalogData` separada como fuente de verdad |
| extractCantidad agarra número de presentación | Dígito match tenía prioridad | Palabras numéricas primero, dígitos solo si no van seguidos de unidad |
| Unsplash imágenes incorrectas | No determinista para marcas MX | Eliminado, solo OFF por barcode |
| Walmart/Aurrera anti-bot | Akamai detecta Playwright | No viable para scraping |

---

## 🔑 Configuración actual

```javascript
// tienda.html — CONFIG
const CONFIG = {
  webhookUrl:     'http://localhost:5678/webhook/tienda-catalogo',
  userId:         'demo_user_01',
  whatsappNumero: '525513222091',
  nombreTienda:   'Super 10',
  eslogan:        'Tu tienda de confianza'
};

// admin.html — CONFIG
const CONFIG = {
  nombreTienda:        'Super 10',
  whatsappProveedor:   '525513222091'
};
```

```
// Supabase
URL: https://dqrhqzdfzhkqpgawgjga.supabase.co
Bucket: productos (público)
Tabla: catalogo_productos
15 productos con imágenes .webp reales
```

---

## 📋 Pendientes — Próximos pasos

### 1. Conectar admin.html a Supabase real
- El inventario actualmente vive en memoria (se pierde al recargar)
- Crear tabla `inventario` en Supabase: `producto_id, stock, ultima_actualizacion`
- Al confirmar entrada por voz → UPDATE en Supabase
- Al cargar admin.html → SELECT para mostrar stock real

### 2. Proteger admin.html con contraseña
- PIN simple de 4 dígitos en localStorage
- O contraseña en Supabase (tabla `tiendas` con campo `pin_admin`)
- Sin esto cualquiera que tenga el link puede ver el panel

### 3. Probar en celular del tendero
- Subir a Vercel/Netlify (gratis, 5 minutos)
- URL real necesaria para: HTTPS → micrófono funciona, PWA funciona
- Probar inventario por voz real con el micrófono

### 4. Nombre dinámico desde Supabase
**Hoy:** `CONFIG.nombreTienda = 'Super 10'` (hardcodeado)
**Meta:** leer de tabla `tiendas` en Supabase

```sql
-- Tabla pendiente de crear
CREATE TABLE tiendas (
  id uuid PRIMARY KEY,
  slug text UNIQUE,          -- 'super-10'
  nombre text,               -- 'Super 10'
  whatsapp text,
  whatsapp_proveedor text,
  logo_url text,
  color_primario text,       -- '#1B4F8A'
  envio_activo boolean DEFAULT false,
  costo_envio numeric,
  pin_admin text
);
```

### 5. QR + Materiales físicos
- Generar QR con URL real del dominio
- Imán, cartel para tienda, imagen para WhatsApp
- URL amigable: `surtidor.app/super-10`

### 6. Pagos en línea (Stripe)
- Tendero abre cuenta Stripe (10 min)
- Supabase Edge Function crea Payment Intent
- Activar botón "Pagar en línea" (ya existe en UI)

### 7. Iconos PWA
- Crear `icon-192.png` e `icon-512.png`
- Quitar warnings de consola

---

## 💰 Modelo de negocio propuesto

| Plan | Precio | Incluye |
|------|--------|---------|
| Básico | $299/mes | Tienda en línea + pedidos por WhatsApp |
| Pro | $599/mes | + Dashboard de ventas + inventario por voz |
| Premium | $999/mes | + Pagos en línea + inventario persistente |

*Mercado objetivo: tiendas de abarrotes en LATAM (México principalmente)*

---

## 🏪 Plan de lanzamiento

1. ✅ **Fase construcción:** tienda.html + admin.html en localhost
2. ⬜ **Fase prueba:** Vercel/Netlify, probar con tienda piloto real
3. ⬜ **Fase lanzamiento:** Dominio propio, Supabase conectado, primer cliente de pago
4. ⬜ **Fase escala:** Multi-tienda, Stripe, inventario persistente

---

*Documento actualizado el 1 de marzo de 2026 — v2*
*Stack: HTML/CSS/JS + Supabase + n8n + Web Speech API*
