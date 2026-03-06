/* ═══════════════════════════════════════════════════════
   TIENDA INTELIGENTE — App Logic
   Fetches from n8n webhook, renders personalized catalog
   ═══════════════════════════════════════════════════════ */

// ── Config ──────────────────────────────────────────────
const CONFIG = {
    // n8n webhook — cambia a tu URL de producción si aplica
    webhookUrl: "http://localhost:5678/webhook/tienda-catalogo",
    userId: "demo_user_01"
};

// ── Emoji map for product categories (fallback images) ──
const EMOJI_MAP = {
    "Lácteos": "🥛",
    "Básicos": "🥚",
    "Panadería": "🍞",
    "Bebidas": "🥤",
    "Abarrotes": "🫘",
    "Enlatados": "🥫",
    "Limpieza": "🧹",
    "Higiene": "🧻",
    "Frutas": "🥑",
    "default": "🛍️"
};

const PRODUCT_EMOJIS = {
    "Leche Santa Clara 1L": "🥛",
    "Huevos San Juan 12 pzas": "🥚",
    "Pan Bimbo Blanco 680g": "🍞",
    "Coca-Cola 2L": "🥤",
    "Arroz SOS 1kg": "🍚",
    "Frijol Negro La Sierra 560g": "🫘",
    "Aceite 1-2-3 1L": "🫒",
    "Atún Dolores en agua 140g": "🐟",
    "Jabón Roma 1kg": "🧼",
    "Papel Higiénico Pétalo 4r": "🧻",
    "Tortillas de Maíz 1kg": "🫓",
    "Azúcar Morena 1kg": "🍯",
    "Café Nescafé Clásico 120g": "☕",
    "Crema Lala 200ml": "🍶",
    "Aguacate Hass (c/u)": "🥑"
};

// ── State ───────────────────────────────────────────────
let cart = [];
let productDataMap = {}; // product_id -> { name, price, imageUrl } para referencia

// ── Mock data (used if webhook is unreachable) ──────────
const MOCK_DATA = {
    saludo: "¡Hola! Veo que te toca surtir Leche Santa Clara 1L, ¿la agregamos de una vez? 🛒",
    favoritos: [
        { id: 1, nombre: "Leche Santa Clara 1L", categoria: "Lácteos", precio: 28.50, unidad: "lt", descripcion: "Leche entera pasteurizada", es_favorito: true, ultima_compra: "2026-02-10" },
        { id: 2, nombre: "Huevos San Juan 12 pzas", categoria: "Básicos", precio: 52.90, unidad: "doc", descripcion: "Huevo blanco fresco", es_favorito: true, ultima_compra: "2026-02-10" },
        { id: 4, nombre: "Coca-Cola 2L", categoria: "Bebidas", precio: 32.00, unidad: "lt", descripcion: "Refresco de cola", es_favorito: true, ultima_compra: "2026-02-08" },
        { id: 11, nombre: "Tortillas de Maíz 1kg", categoria: "Básicos", precio: 22.00, unidad: "kg", descripcion: "Tortillas frescas del día", es_favorito: true, ultima_compra: "2026-02-12" },
        { id: 13, nombre: "Café Nescafé Clásico 120g", categoria: "Bebidas", precio: 89.90, unidad: "pza", descripcion: "Café soluble", es_favorito: true, ultima_compra: "2026-02-05" }
    ],
    explorar: [
        { id: 3, nombre: "Pan Bimbo Blanco 680g", categoria: "Panadería", precio: 62.00, unidad: "pza", descripcion: "Pan de caja blanco", es_favorito: false },
        { id: 5, nombre: "Arroz SOS 1kg", categoria: "Abarrotes", precio: 29.90, unidad: "kg", descripcion: "Arroz grano largo", es_favorito: false },
        { id: 6, nombre: "Frijol Negro La Sierra 560g", categoria: "Abarrotes", precio: 33.50, unidad: "pza", descripcion: "Frijoles refritos listos", es_favorito: false },
        { id: 7, nombre: "Aceite 1-2-3 1L", categoria: "Abarrotes", precio: 38.90, unidad: "lt", descripcion: "Aceite vegetal comestible", es_favorito: false },
        { id: 8, nombre: "Atún Dolores en agua 140g", categoria: "Enlatados", precio: 22.50, unidad: "pza", descripcion: "Atún en trozos", es_favorito: false },
        { id: 9, nombre: "Jabón Roma 1kg", categoria: "Limpieza", precio: 35.00, unidad: "kg", descripcion: "Jabón en polvo para ropa", es_favorito: false },
        { id: 10, nombre: "Papel Higiénico Pétalo 4r", categoria: "Higiene", precio: 42.00, unidad: "paq", descripcion: "Papel higiénico suave", es_favorito: false },
        { id: 12, nombre: "Azúcar Morena 1kg", categoria: "Abarrotes", precio: 32.00, unidad: "kg", descripcion: "Azúcar estándar morena", es_favorito: false },
        { id: 14, nombre: "Crema Lala 200ml", categoria: "Lácteos", precio: 18.50, unidad: "pza", descripcion: "Crema ácida", es_favorito: false },
        { id: 15, nombre: "Aguacate Hass (c/u)", categoria: "Frutas", precio: 15.00, unidad: "pza", descripcion: "Aguacate mexicano", es_favorito: false }
    ]
};


// ═══════════════════════════════════════════════════════
// INIT
// ═══════════════════════════════════════════════════════

document.addEventListener("DOMContentLoaded", () => {
    setupCart();
    syncBadge(true);   // Badge en 0 y oculto al inicio
    fetchCatalog();
});


// ── Fetch catalog from n8n webhook ─────────────────────
async function fetchCatalog() {
    try {
        const res = await fetch(CONFIG.webhookUrl, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ user_id: CONFIG.userId })
        });

        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();

        // Validate response shape
        if (data.favoritos && data.explorar) {
            renderCatalog(data);
        } else {
            console.warn("Invalid response shape, using mock data");
            renderCatalog(MOCK_DATA);
        }
    } catch (err) {
        console.warn("Webhook unreachable, using mock data:", err.message);
        renderCatalog(MOCK_DATA);
    }
}


// ═══════════════════════════════════════════════════════
// RENDER
// ═══════════════════════════════════════════════════════

function renderCatalog(data) {
    // Greeting
    const greetText = document.getElementById("greetingText");
    greetText.innerHTML = formatGreeting(data.saludo);

    // Favoritos
    if (data.favoritos && data.favoritos.length > 0) {
        const section = document.getElementById("favoritosSection");
        const grid = document.getElementById("favoritosGrid");
        section.style.display = "block";
        section.style.animation = "fadeInUp 0.5s ease forwards";
        grid.innerHTML = data.favoritos.map(p => createProductCard(p, true)).join("");
    }

    // Explorar
    if (data.explorar && data.explorar.length > 0) {
        const section = document.getElementById("explorarSection");
        const grid = document.getElementById("explorarGrid");
        section.style.display = "block";
        section.style.animation = "fadeInUp 0.5s ease 0.15s forwards";
        grid.innerHTML = data.explorar.map(p => createProductCard(p, false)).join("");
    }

    // Guardar referencia de cada producto para uso en addToCart/changeQty
    [...(data.favoritos || []), ...(data.explorar || [])].forEach(p => {
        productDataMap[p.id] = {
            name: p.nombre,
            price: p.precio,
            imageUrl: p.imagen_url || ''
        };
    });
}

function formatGreeting(text) {
    // Bold the product name if found
    return text.replace(/(surtir\s+)([^,]+)/i, "$1<strong>$2</strong>");
}

function getProductEmoji(product) {
    return PRODUCT_EMOJIS[product.nombre] || EMOJI_MAP[product.categoria] || EMOJI_MAP.default;
}

// Decide si el producto tiene imagen real de Supabase o usa emoji de fallback
function hasRealImage(product) {
    return product.imagen_url && product.imagen_url.trim() !== '';
}

function renderProductImage(product) {
    if (product.imagen_url && product.imagen_url.trim() !== '') {
        return `<img src="${product.imagen_url}" alt="${product.nombre}" loading="lazy">`;
    }
    return getProductEmoji(product);
}

// Thumbnail para el carrito (mini versión) — misma lógica que renderProductImage
function getCartThumbFromUrl(imageUrl, name) {
    if (imageUrl && imageUrl.trim() !== '') {
        return `<img src="${imageUrl}" alt="${name}" style="width:40px;height:40px;object-fit:cover;border-radius:8px;">`;
    }
    return PRODUCT_EMOJIS[name] || '🛍️';
}

function createProductCard(product, isFavorito) {
    const priceFormatted = `$${Number(product.precio).toFixed(2)}`;
    const badge = isFavorito
        ? `<span class="product-card__badge">⭐ Favorito</span>`
        : "";
    const imageContent = renderProductImage(product);

    return `
    <article class="product-card ${isFavorito ? 'product-card--favorito' : ''}" data-id="${product.id}">
      ${badge}
      <div class="product-card__image">${imageContent}</div>
      <span class="product-card__category">${product.categoria || ''}</span>
      <h3 class="product-card__name">${product.nombre}</h3>
      <p class="product-card__desc">${product.descripcion || ''}</p>
      <div class="product-card__price-row">
        <span class="product-card__price">${priceFormatted}</span>
        <span class="product-card__unit">/ ${product.unidad || 'pza'}</span>
      </div>
      <div class="product-card__controls" id="controls-${product.id}">
        <button class="add-btn add-btn--full" id="addBtn-${product.id}" onclick="addToCart(${product.id})">
          Agregar
        </button>
      </div>
    </article>
  `;
}


// ═══════════════════════════════════════════════════════
// QUANTITY CONTROLS (integrados con carrito)
// ═══════════════════════════════════════════════════════

// Muestra el control de cantidad en la tarjeta
function showQtyControl(productId, qty) {
    const container = document.getElementById(`controls-${productId}`);
    if (!container) return;
    container.innerHTML = `
      <div class="qty-control qty-control--expanded">
        <button class="qty-control__btn" onclick="changeQty(${productId}, -1)" aria-label="Reducir">−</button>
        <span class="qty-control__value" id="qty-${productId}">${qty}</span>
        <button class="qty-control__btn" onclick="changeQty(${productId}, 1)" aria-label="Aumentar">+</button>
      </div>
    `;
}

// Muestra el botón "Agregar" original en la tarjeta
function showAddButton(productId) {
    const container = document.getElementById(`controls-${productId}`);
    if (!container) return;
    container.innerHTML = `
      <button class="add-btn add-btn--full" id="addBtn-${productId}" onclick="addToCart(${productId})">
        Agregar
      </button>
    `;
}

function changeQty(productId, delta) {
    const item = cart.find(i => i.id === productId);
    if (!item) return;

    item.qty = Math.max(0, Math.min(99, item.qty + delta));

    if (item.qty === 0) {
        // Quitar del carrito y volver a mostrar "Agregar"
        cart = cart.filter(i => i.id !== productId);
        showAddButton(productId);
    } else {
        // Actualizar el número visible
        const el = document.getElementById(`qty-${productId}`);
        if (el) {
            el.textContent = item.qty;
            el.style.transform = "scale(1.2)";
            setTimeout(() => el.style.transform = "scale(1)", 150);
        }
    }

    syncBadge(false);
    updateCartUI();
}


// ═══════════════════════════════════════════════════════
// CART
// ═══════════════════════════════════════════════════════

function setupCart() {
    const cartBtn = document.getElementById("cartBtn");
    const cartClose = document.getElementById("cartClose");
    const overlay = document.getElementById("cartOverlay");

    cartBtn.addEventListener("click", () => toggleCart(true));
    cartClose.addEventListener("click", () => toggleCart(false));
    overlay.addEventListener("click", () => toggleCart(false));
}

function toggleCart(open) {
    document.getElementById("cartPanel").classList.toggle("open", open);
    document.getElementById("cartOverlay").classList.toggle("open", open);
}

// Sincroniza el badge del carrito
function syncBadge(animate) {
    const badge = document.getElementById("cartCount");
    if (!badge) return;
    const totalItems = cart.reduce((sum, i) => sum + i.qty, 0);
    badge.textContent = totalItems;
    badge.style.display = totalItems > 0 ? 'flex' : 'none';
    if (animate && totalItems > 0) {
        badge.classList.remove("bounce");
        void badge.offsetWidth;
        badge.classList.add("bounce");
    }
}

function addToCart(productId) {
    const data = productDataMap[productId];
    if (!data) return;

    const existing = cart.find(item => item.id === productId);

    if (existing) {
        existing.qty += 1;
    } else {
        cart.push({ id: productId, name: data.name, price: data.price, imageUrl: data.imageUrl, qty: 1 });
    }

    // Swap botón → control de cantidad
    const currentQty = (existing ? existing.qty : 1);
    showQtyControl(productId, currentQty);

    syncBadge(true);
    updateCartUI();
}

function removeFromCart(productId) {
    cart = cart.filter(item => item.id !== productId);
    showAddButton(productId);
    syncBadge(false);
    updateCartUI();
}

function updateCartUI() {
    const container = document.getElementById("cartItems");
    const totalEl = document.getElementById("cartTotal");

    if (cart.length === 0) {
        container.innerHTML = '<p class="cart-panel__empty">Tu carrito está vacío</p>';
        totalEl.textContent = "$0.00";
        return;
    }

    container.innerHTML = cart.map(item => {
        const thumb = getCartThumbFromUrl(item.imageUrl, item.name);
        return `
      <div class="cart-item">
        <span class="cart-item__emoji">${thumb}</span>
        <div class="cart-item__info">
          <div class="cart-item__name">${item.name}</div>
          <div class="cart-item__meta">${item.qty} × $${item.price.toFixed(2)}</div>
        </div>
        <span class="cart-item__price">$${(item.qty * item.price).toFixed(2)}</span>
        <button class="cart-item__remove" onclick="removeFromCart(${item.id})" aria-label="Eliminar">✕</button>
      </div>`;
    }).join("");

    const total = cart.reduce((sum, item) => sum + item.qty * item.price, 0);
    totalEl.textContent = `$${total.toFixed(2)}`;
}


// ── CSS animation (injected) ────────────────────────────
const style = document.createElement("style");
style.textContent = `
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
  }
`;
document.head.appendChild(style);
