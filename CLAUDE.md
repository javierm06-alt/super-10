# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Proyecto

**Tienda Inteligente de Abarrotes** — Catálogo mobile-first personalizado (estilo Dribbble). Muestra primero los productos que el usuario ya ha comprado ("Favoritos") y luego el resto ("Explorar"). Sin framework, sin build step.

---

## Stack

| Capa | Tecnología |
|------|------------|
| Frontend | HTML/CSS/JS vanilla, mobile-first, estilo Dribbble |
| Backend/API | n8n local `http://localhost:5678` |
| Base de datos | Supabase PostgreSQL — proyecto `dqrhqzdfzhkqpgawgjga` |
| Pipeline de imágenes | Python 3.12 + rembg[gpu] + Pillow |
| IA local | ComfyUI + R-ESRGAN (GPU HP Victus) |
| venv | `C:/Users/USER/Desktop/Agencia_IA/venv` (compartido con la agencia) |

---

## Credenciales (no commitear)

```
SUPABASE_URL   = https://dqrhqzdfzhkqpgawgjga.supabase.co
SUPABASE_KEY   = sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ
N8N_API_KEY    = (ver config_tienda.json)
N8N_WEBHOOK    = http://localhost:5678/webhook/tienda-catalogo
N8N_WF_ID      = 7ZBpMV18Foo9MrYu
DEMO_USER_ID   = demo_user_01
```

---

## Comandos clave

```bash
# Activar venv (desde la raíz de Agencia_IA)
venv\Scripts\activate

# Ejecutar pipeline de imágenes
cd Modulo_Tienda_Abarrotes\scripts
python procesar_fotos.py

# Verificar dependencias Python
pip list | findstr -i "rembg pillow supabase requests"

# Probar webhook n8n (PowerShell)
Invoke-RestMethod -Method POST `
  -Uri "http://localhost:5678/webhook/tienda-catalogo" `
  -Body '{"user_id":"demo_user_01"}' `
  -ContentType "application/json"
```

---

## Arquitectura

```
index.html / tienda.html (frontend mobile-first)
  └── app.js
        └── POST /webhook/tienda-catalogo  { user_id }
              └── n8n workflow 7ZBpMV18Foo9MrYu
                    ├── Traer Catalogo  → GET Supabase/catalogo_productos?select=*
                    ├── Traer Historial → GET Supabase/historial_compras?user_id=eq.{user_id}
                    ├── Personalizar Catalogo (Code JS)
                    │     → divide en favoritos[] + explorar[]
                    │     → genera saludo proactivo
                    └── Responder → { saludo, favoritos[], explorar[] }
```

Si el webhook falla, `app.js` cae automáticamente a `MOCK_DATA` hardcodeado (15 productos + 5 favoritos de `demo_user_01`).

### Datos Supabase

**`catalogo_productos`** — id, nombre, categoria, precio, unidad, imagen_url, descripcion
**`historial_compras`** — id, user_id (TEXT), producto_id FK, cantidad, fecha_compra

RLS habilitado con políticas de lectura pública (demo). `demo_user_01` tiene historial en IDs: 1, 2, 4, 11, 13 → aparecen como Favoritos.

Estado de imágenes:
- ✅ Con imagen Unsplash: IDs 1, 2, 3, 4, 15
- ❌ Sin imagen (11 productos): IDs 5–14 excepto 15

---

## Estado actual del proyecto

| Archivo | Estado |
|---------|--------|
| `index.html` + `app.js` + `styles.css` | ✅ Frontend original Antigravity funcional |
| `tienda.html` | 🎯 Pendiente crear — frontend nuevo estilo Dribbble |
| `create_workflow.js` | ✅ Ejecutado — workflow activo |
| `setup_supabase.sql` | ✅ Ejecutado — tablas + 15 productos demo |
| `update_images.js` | ⏳ Pendiente ejecutar |
| `scripts/procesar_fotos.py` | 🎯 Crear — pipeline principal de imágenes |

---

## Tarea principal pendiente: `scripts/procesar_fotos.py`

Pipeline exacto para cada producto sin imagen válida:

```
Supabase catalogo_productos (imagen_url vacía)
  → Buscar en Open Food Facts por nombre
      ✅ Encontró → descargar imagen
      ❌ No → fallback Unsplash
  → rembg (GPU) → quitar fondo
  → Pillow → fondo blanco + padding + resize 800×800px
  → Supabase Storage (bucket: "productos")
  → UPDATE catalogo_productos SET imagen_url = storage_url
```

---

## Bugs conocidos

| Bug | Ubicación | Fix |
|-----|-----------|-----|
| URL del historial empieza con `=` | `create_workflow.js` nodo "Traer Historial" | Quitar `=` inicial de la URL |
| `user_id` incorrecto | `app.js` línea 10 — usa `user_test_001` | Cambiar a `demo_user_01` |

---

## Pipeline de imágenes — Fases

- **Fase 0** ✅ — rembg[gpu] instalado, Supabase listo, n8n activo
- **Fase 1** 🎯 — `procesar_fotos.py` local: 15 productos → fotos reales fondo blanco
- **Fase 2** ⬜ — Workflow n8n automático: nuevo producto → busca imagen → procesa → guarda
- **Fase 3** ⬜ — Productos sin imagen en Open Food Facts → ComfyUI genera render 3D + R-ESRGAN upscaling

---

## Skills disponibles

11 skills globales en `~/.claude/skills/`:

| Skill | Cuándo usarlo |
|-------|---------------|
| `ui-ux-pro-max` | Diseño de componentes mobile-first, layouts, animaciones CSS |
| `supabase-automation` | Queries, RLS, Storage, triggers de Supabase |
| `supabase-realtime` | Suscripciones en tiempo real a tablas |
| `planning-architect` | Diseño de arquitectura antes de implementar |
| `n8n-workflow-patterns` | Estructura de workflows, loops, merges |
| `n8n-code-javascript` | Nodos Code JS en n8n |
| `n8n-code-python` | Nodos Code Python en n8n |
| `n8n-expression-syntax` | Expresiones `={{ }}` en n8n |
| `n8n-node-configuration` | Configuración de nodos específicos |
| `n8n-validation-expert` | Validación y manejo de errores en n8n |
| `n8n-mcp-tools-expert` | Integración MCP con n8n |

Invocar con `/nombre-del-skill` antes de iniciar una tarea relevante.

---

## Reglas del proyecto

1. Frontend siempre mobile-first. Referencia visual: Dribbble / estilo app moderna.
2. Los cambios de n8n van en scripts `.js` que usan la API REST — nunca editar workflows manualmente salvo confirmación.
3. El venv está en `Agencia_IA/venv`, no dentro de este módulo.
4. `tienda.html` es el frontend objetivo; `index.html` es el legacy que sirve de referencia.
5. Antes de implementar algo no trivial, invocar `/planning-architect`.
