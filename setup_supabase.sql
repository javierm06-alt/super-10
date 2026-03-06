-- =====================================================
-- TIENDA INTELIGENTE - Setup Supabase
-- Ejecutar en: Supabase SQL Editor (dqrhqzdfzhkqpgawgjga)
-- =====================================================

-- 1. Limpiar tablas previas (evitar duplicados)
DROP TABLE IF EXISTS historial_compras CASCADE;
DROP TABLE IF EXISTS catalogo_productos CASCADE;

-- 2. Catálogo de productos
CREATE TABLE catalogo_productos (
  id SERIAL PRIMARY KEY,
  nombre TEXT NOT NULL,
  categoria TEXT NOT NULL,
  precio NUMERIC(10,2) NOT NULL,
  unidad TEXT DEFAULT 'pza',
  imagen_url TEXT,
  descripcion TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 3. Historial de compras por usuario
CREATE TABLE historial_compras (
  id SERIAL PRIMARY KEY,
  user_id TEXT NOT NULL,
  producto_id INT REFERENCES catalogo_productos(id) ON DELETE CASCADE,
  cantidad INT DEFAULT 1,
  fecha_compra DATE DEFAULT CURRENT_DATE,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 4. Índice para búsquedas rápidas por usuario
CREATE INDEX idx_historial_user ON historial_compras(user_id);

-- 5. Habilitar RLS (Row Level Security) — lectura pública para demo
ALTER TABLE catalogo_productos ENABLE ROW LEVEL SECURITY;
ALTER TABLE historial_compras ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Leer catálogo público" ON catalogo_productos
  FOR SELECT USING (true);

CREATE POLICY "Leer historial propio" ON historial_compras
  FOR SELECT USING (true);

-- =====================================================
-- DATOS DE DEMO — 15 Productos de Abarrotes
-- =====================================================
INSERT INTO catalogo_productos (nombre, categoria, precio, unidad, imagen_url, descripcion) VALUES
  ('Leche Santa Clara 1L',      'Lácteos',     28.50, 'lt',  '', 'Leche entera pasteurizada'),
  ('Huevos San Juan 12 pzas',   'Básicos',     52.90, 'doc', '', 'Huevo blanco fresco'),
  ('Pan Bimbo Blanco 680g',     'Panadería',   62.00, 'pza', '', 'Pan de caja blanco'),
  ('Coca-Cola 2L',              'Bebidas',     32.00, 'lt',  '', 'Refresco de cola'),
  ('Arroz SOS 1kg',             'Abarrotes',   29.90, 'kg',  '', 'Arroz grano largo'),
  ('Frijol Negro La Sierra 560g','Abarrotes',  33.50, 'pza', '', 'Frijoles refritos listos'),
  ('Aceite 1-2-3 1L',           'Abarrotes',   38.90, 'lt',  '', 'Aceite vegetal comestible'),
  ('Atún Dolores en agua 140g', 'Enlatados',   22.50, 'pza', '', 'Atún en trozos'),
  ('Jabón Roma 1kg',            'Limpieza',    35.00, 'kg',  '', 'Jabón en polvo para ropa'),
  ('Papel Higiénico Pétalo 4r', 'Higiene',     42.00, 'paq', '', 'Papel higiénico suave'),
  ('Tortillas de Maíz 1kg',     'Básicos',     22.00, 'kg',  '', 'Tortillas frescas del día'),
  ('Azúcar Morena 1kg',         'Abarrotes',   32.00, 'kg',  '', 'Azúcar estándar morena'),
  ('Café Nescafé Clásico 120g', 'Bebidas',     89.90, 'pza', '', 'Café soluble'),
  ('Crema Lala 200ml',          'Lácteos',     18.50, 'pza', '', 'Crema ácida'),
  ('Aguacate Hass (c/u)',       'Frutas',      15.00, 'pza', '', 'Aguacate mexicano');

-- =====================================================
-- HISTORIAL DE DEMO — usuario "demo_user_01"
-- (Ha comprado 5 productos antes)
-- =====================================================
INSERT INTO historial_compras (user_id, producto_id, cantidad, fecha_compra) VALUES
  ('demo_user_01', 1, 2, '2026-02-10'),  -- Leche Santa Clara
  ('demo_user_01', 2, 1, '2026-02-10'),  -- Huevos
  ('demo_user_01', 4, 3, '2026-02-08'),  -- Coca-Cola
  ('demo_user_01', 11, 2, '2026-02-12'), -- Tortillas
  ('demo_user_01', 13, 1, '2026-02-05'); -- Café Nescafé
