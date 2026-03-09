/* â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
   TIENDA INTELIGENTE â€” App Logic
   Fetches from n8n webhook, renders personalized catalog
   â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â• */

// â”€â”€ Config â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const CONFIG = {
    // n8n webhook â€” cambia a tu URL de producciÃ³n si aplica
    webhookUrl: "",
    userId: "demo_user_01"
};

// â”€â”€ Emoji map for product categories (fallback images) â”€â”€
const EMOJI_MAP = {
    "LÃ¡cteos": "ðŸ¥›",
    "BÃ¡sicos": "ðŸ¥š",
    "PanaderÃ­a": "ðŸž",
    "Bebidas": "ðŸ¥¤",
    "Abarrotes": "ðŸ«˜",
    "Enlatados": "ðŸ¥«",
    "Limpieza": "ðŸ§¹",
    "Higiene": "ðŸ§»",
    "Frutas": "ðŸ¥‘",
    "default": "ðŸ›ï¸"
};

const PRODUCT_EMOJIS = {
    "Leche Santa Clara 1L": "ðŸ¥›",
    "Huevos San Juan 12 pzas": "ðŸ¥š",
    "Pan Bimbo Blanco 680g": "ðŸž",
    "Coca-Cola 2L": "ðŸ¥¤",
    "Arroz SOS 1kg": "ðŸš",
    "Frijol Negro La Sierra 560g": "ðŸ«˜",
    "Aceite 1-2-3 1L": "ðŸ«’",
    "AtÃºn Dolores en agua 140g": "ðŸŸ",
    "JabÃ³n Roma 1kg": "ðŸ§¼",
    "Papel HigiÃ©nico PÃ©talo 4r": "ðŸ§»",
    "Tortillas de MaÃ­z 1kg": "ðŸ«“",
    "AzÃºcar Morena 1kg": "ðŸ¯",
    "CafÃ© NescafÃ© ClÃ¡sico 120g": "â˜•",
    "Crema Lala 200ml": "ðŸ¶",
    "Aguacate Hass (c/u)": "ðŸ¥‘"
};

// â”€â”€ State â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
let cart = [];
let productDataMap = {}; // product_id -> { name, price, imageUrl } para referencia

// â”€â”€ Mock data (used if webhook is unreachable) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const MOCK_DATA = {
    saludo: "Â¡Hola! Veo que te toca surtir Leche Santa Clara 1L, Â¿la agregamos de una vez? ðŸ›’",
    favoritos: [
        { id: 1, nombre: "Leche Santa Clara 1L", categoria: "LÃ¡cteos", precio: 28.50, unidad: "lt", descripcion: "Leche entera pasteurizada", es_favorito: true, ultima_compra: "2026-02-10" },
        { id: 2, nombre: "Huevos San Juan 12 pzas", categoria: "BÃ¡sicos", precio: 52.90, unidad: "doc", descripcion: "Huevo blanco fresco", es_favorito: true, ultima_compra: "2026-02-10" },
        { id: 4, nombre: "Coca-Cola 2L", categoria: "Bebidas", precio: 32.00, unidad: "lt", descripcion: "Refresco de cola", es_favorito: true, ultima_compra: "2026-02-08" },
        { id: 11, nombre: "Tortillas de MaÃ­z 1kg", categoria: "BÃ¡sicos", precio: 22.00, unidad: "kg", descripcion: "Tortillas frescas del dÃ­a", es_favorito: true, ultima_compra: "2026-02-12" },
        { id: 13, nombre: "CafÃ© NescafÃ© ClÃ¡sico 120g", categoria: "Bebidas", precio: 89.90, unidad: "pza", descripcion: "CafÃ© soluble", es_favorito: true, ultima_compra: "2026-02-05" }
    ],
    explorar: [
        { id: 3, nombre: "Pan Bimbo Blanco 680g", categoria: "PanaderÃ­a", precio: 62.00, unidad: "pza", descripcion: "Pan de caja blanco", es_favorito: false },
        { id: 5, nombre: "Arroz SOS 1kg", categoria: "Abarrotes", precio: 29.90, unidad: "kg", descripcion: "Arroz grano largo", es_favorito: false },
        { id: 6, nombre: "Frijol Negro La Sierra 560g", categoria: "Abarrotes", precio: 33.50, unidad: "pza", descripcion: "Frijoles refritos listos", es_favorito: false },
        { id: 7, nombre: "Aceite 1-2-3 1L", categoria: "Abarrotes", precio: 38.90, unidad: "lt", descripcion: "Aceite vegetal comestible", es_favorito: false },
        { id: 8, nombre: "AtÃºn Dolores en agua 140g", categoria: "Enlatados", precio: 22.50, unidad: "pza", descripcion: "AtÃºn en trozos", es_favorito: false },
        { id: 9, nombre: "JabÃ³n Roma 1kg", categoria: "Limpieza", precio: 35.00, unidad: "kg", descripcion: "JabÃ³n en polvo para ropa", es_favorito: false },
        { id: 10, nombre: "Papel HigiÃ©nico PÃ©talo 4r", categoria: "Higiene", precio: 42.00, unidad: "paq", descripcion: "Papel higiÃ©nico suave", es_favorito: false },
        { id: 12, nombre: "AzÃºcar Morena 1kg", categoria: "Abarrotes", precio: 32.00, unidad: "kg", descripcion: "AzÃºcar estÃ¡ndar morena", es_favorito: false },
        { id: 14, nombre: "Crema Lala 200ml", categoria: "LÃ¡cteos", precio: 18.50, unidad: "pza", descripcion: "Crema Ã¡cida", es_favorito: false },
        { id: 15, nombre: "Aguacate Hass (c/u)", categoria: "Frutas", precio: 15.00, unidad: "pza", descripcion: "Aguacate mexicano", es_favorito: false }
    ]
};


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// INIT
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

document.addEventListener("DOMContentLoaded", () => {
    setupCart();
    syncBadge(true);   // Badge en 0 y oculto al inicio
    fetchCatalog();
});


// â”€â”€ Fetch catalog from n8n webhook â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
async function fetchCatalog() {
    try {
        const res = await fetch(`https://dqrhqzdfzhkqpgawgjga.supabase.co/rest/v1/catalogo_productos?select=id,nombre,categoria,subcategoria,precio,unidad,descripcion,imagen_url&order=subcategoria.asc,nombre.asc`, {
            headers: { "apikey": "sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ", "Authorization": "Bearer sb_publishable_kponNfbiTEBSbJaP6tf-Xg_pVOdCApQ" }
        });
        const productos = await res.json();
        const data = {
            saludo: "¡Hola! Aquí tienes tu catálogo actualizado.",
            favoritos: productos.slice(0, 5).map(p => ({ ...p, es_favorito: true })),
            explorar: productos.slice(5).map(p => ({ ...p, es_favorito: false }))
        };
        renderCatalog(data);
    } catch (err) {
        console.error("Error cargando catálogo:", err.message);
        renderCatalog(MOCK_DATA);
    }
}


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// RENDER
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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

// Thumbnail para el carrito (mini versiÃ³n) â€” misma lÃ³gica que renderProductImage
function getCartThumbFromUrl(imageUrl, name) {
    if (imageUrl && imageUrl.trim() !== '') {
        return `<img src="${imageUrl}" alt="${name}" style="width:40px;height:40px;object-fit:cover;border-radius:8px;">`;
    }
    return PRODUCT_EMOJIS[name] || 'ðŸ›ï¸';
}

function createProductCard(product, isFavorito) {
    const priceFormatted = `$${Number(product.precio).toFixed(2)}`;
    const badge = isFavorito
        ? `<span class="product-card__badge">â­ Favorito</span>`
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


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// QUANTITY CONTROLS (integrados con carrito)
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

// Muestra el control de cantidad en la tarjeta
function showQtyControl(productId, qty) {
    const container = document.getElementById(`controls-${productId}`);
    if (!container) return;
    container.innerHTML = `
      <div class="qty-control qty-control--expanded">
        <button class="qty-control__btn" onclick="changeQty(${productId}, -1)" aria-label="Reducir">âˆ’</button>
        <span class="qty-control__value" id="qty-${productId}">${qty}</span>
        <button class="qty-control__btn" onclick="changeQty(${productId}, 1)" aria-label="Aumentar">+</button>
      </div>
    `;
}

// Muestra el botÃ³n "Agregar" original en la tarjeta
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
        // Actualizar el nÃºmero visible
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


// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
// CART
// â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

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

    // Swap botÃ³n â†’ control de cantidad
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
        container.innerHTML = '<p class="cart-panel__empty">Tu carrito estÃ¡ vacÃ­o</p>';
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
          <div class="cart-item__meta">${item.qty} Ã— $${item.price.toFixed(2)}</div>
        </div>
        <span class="cart-item__price">$${(item.qty * item.price).toFixed(2)}</span>
        <button class="cart-item__remove" onclick="removeFromCart(${item.id})" aria-label="Eliminar">âœ•</button>
      </div>`;
    }).join("");

    const total = cart.reduce((sum, item) => sum + item.qty * item.price, 0);
    totalEl.textContent = `$${total.toFixed(2)}`;
}


// â”€â”€ CSS animation (injected) â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
const style = document.createElement("style");
style.textContent = `
  @keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
  }
`;
document.head.appendChild(style);


