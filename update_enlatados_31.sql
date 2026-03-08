-- ─────────────────────────────────────────────────────────────────────────────
-- UPDATE masivo imagen_url — Categoría: Enlatados (31 productos)
-- Ejecutar en: Supabase SQL Editor (bypassa RLS con postgres)
-- 
-- ⚠️  Antes de correr:
--   1. Verifica que los nombres coincidan con tu tabla:
--      SELECT nombre FROM catalogo_productos WHERE categoria = 'Enlatados' ORDER BY nombre;
--   2. Los storage_key de los 16 primeros asume que los subiste con el mismo
--      nombre de archivo. Ajusta si fue diferente.
-- ─────────────────────────────────────────────────────────────────────────────

-- BASE URL
-- https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/

-- ── 16 productos ya subidos anteriormente ─────────────────────────────────────

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Catsup_Heinz_567_g.webp'
WHERE nombre = 'Catsup Heinz 567 g';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Champinones_Rebanados_Herdez.webp'
WHERE nombre = 'Champiñones Rebanados Herdez';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Chicharos_Herdez_400g.webp'
WHERE nombre = 'Chicharos Herdez 400g';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Ensalada_De_Legumbres_Herdez.webp'
WHERE nombre = 'Ensalada De Legumbres Herdez';

-- NOTA: si tienes dos variantes (Herdez y Herdez_400g), ajusta el nombre_db aquí:
-- UPDATE catalogo_productos SET imagen_url = '...Ensalada_De_Legumbres_Herdez_1.webp'
-- WHERE nombre = 'Ensalada De Legumbres Herdez 400g';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Flan_Gari_Vainilla.webp'
WHERE nombre = 'Flan Gari Vainilla';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Fresa.webp'
WHERE nombre = 'Gelatina Fresa';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Chocolate.webp'
WHERE nombre = 'Gelatina Gari Chocolate';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Durazno.webp'
WHERE nombre = 'Gelatina Gari Durazno';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Frambuesa.webp'
WHERE nombre = 'Gelatina Gari Frambuesa';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Jerez.webp'
WHERE nombre = 'Gelatina Gari Jerez';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Limon.webp'
WHERE nombre = 'Gelatina Gari Limon';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Mango.webp'
WHERE nombre = 'Gelatina Gari Mango';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Mazapan.webp'
WHERE nombre = 'Gelatina Gari Mazapan';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Nuez.webp'
WHERE nombre = 'Gelatina Gari Nuez';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Gari_Pina.webp'
WHERE nombre = 'Gelatina Gari Piña';

-- ── 15 productos nuevos (batch 2) ─────────────────────────────────────────────

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Limon.webp'
WHERE nombre = 'Gelatina Limon';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Gelatina_Uva.webp'
WHERE nombre = 'Gelatina Uva';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Granos_De_Elote_220g_Herdez.webp'
WHERE nombre = 'Granos De Elote 220g Herdez';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Huevo.webp'
WHERE nombre = 'Huevo';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Jalapenos_En_Rajas_La_Costena_220_G.webp'
WHERE nombre = 'Jalapeños En Rajas La Costeña 220 G';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Jalapenos_Enteros_La_Costena_220_G.webp'
WHERE nombre = 'Jalapeños Enteros La Costeña 220 G';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Mole_Verde_Dona_Maria.webp'
WHERE nombre = 'Mole Verde Doña Maria';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Nachos_Jalapenos_220g_La_Costena.webp'
WHERE nombre = 'Nachos Jalapeños 220g La Costeña';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Rajas_Verdes_La_Costena_105g.webp'
WHERE nombre = 'Rajas Verdes La Costeña 105g';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Salsa_Guacamole_Picante.webp'
WHERE nombre = 'Salsa Guacamole Picante';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Salsa_Inglesa_Crosse_Blackwell.webp'
WHERE nombre = 'Salsa Inglesa Crosse & Blackwell';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Salsa_Taquera_Herdez.webp'
WHERE nombre = 'Salsa Taquera Herdez';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Tomates_Molidos_Condimentados_Del_Fuerte.webp'
WHERE nombre = 'Tomates Molidos Condimentados Del Fuerte';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Vinagre_Blanco_Clemente_Jacques.webp'
WHERE nombre = 'Vinagre Blanco Clemente Jacques';

UPDATE catalogo_productos SET imagen_url = 'https://dqrhqzdfzhkqpgawgjga.supabase.co/storage/v1/object/public/productos/Vinagre_Clemente_Jacques_Manzana.webp'
WHERE nombre = 'Vinagre Clemente Jacques Manzana 500 Ml';

-- ── Verificación final ────────────────────────────────────────────────────────
-- Corre esto después para confirmar que los 31 tienen imagen:
-- SELECT nombre, imagen_url IS NOT NULL as tiene_imagen
-- FROM catalogo_productos
-- WHERE categoria = 'Enlatados'
-- ORDER BY nombre;
