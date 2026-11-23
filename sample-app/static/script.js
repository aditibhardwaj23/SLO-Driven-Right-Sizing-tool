
const productGrid = document.getElementById("product-grid");
const searchInput = document.getElementById("search");
const categorySelect = document.getElementById("category");

const cartPanel = document.getElementById("cart-panel");
const cartToggle = document.getElementById("cart-toggle");
const cartClose = document.getElementById("cart-close");
const cartItems = document.getElementById("cart-items");
const cartCount = document.getElementById("cart-count");
const cartTotal = document.getElementById("cart-total");
const overlay = document.getElementById("overlay");

const productModal = document.getElementById("product-modal");
const productModalContent =
    document.getElementById("product-modal-content");

const orderModal = document.getElementById("order-modal");
const toast = document.getElementById("toast");

function formatPrice(price) {
    return "₹" + Number(price).toLocaleString("en-IN");
}

function discountPercent(product) {
    return Math.round(
        (1 - product.price / product.original_price) * 100
    );
}

function escapeHTML(value) {
    return String(value).replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#39;"
    })[char]);
}

async function api(url, options = {}) {
    const response = await fetch(url, {
        ...options,
        headers: {
            "Content-Type": "application/json",
            ...options.headers
        }
    });

    const data = await response.json();

    if (!response.ok) {
        throw new Error(data.error || "Something went wrong");
    }

    return data;
}

function showToast(message) {
    toast.textContent = message;
    toast.classList.add("active");

    setTimeout(() => {
        toast.classList.remove("active");
    }, 2500);
}

// ----------------------------------
// LOAD PRODUCTS
// ----------------------------------

async function loadProducts() {
    productGrid.innerHTML = "<p>Loading products...</p>";

    try {
        const search = encodeURIComponent(searchInput.value.trim());
        const category = encodeURIComponent(categorySelect.value);

        const products = await api(
            `/api/products?search=${search}&category=${category}`
        );

        productGrid.innerHTML = "";

        if (products.length === 0) {
            productGrid.innerHTML =
                "<p>No products found. Try another search.</p>";
            return;
        }

        products.forEach(product => {
            const discount = discountPercent(product);

            const card = document.createElement("article");
            card.className = "product-card";

            card.innerHTML = `
                <div class="product-image">
                    <span class="discount-badge">
                        ${discount}% OFF
                    </span>

                    <img src="${escapeHTML(product.image)}"
                         alt="${escapeHTML(product.name)}"
                         loading="lazy">
                </div>

                <div class="product-info">
                    <span class="category-tag">
                        ${escapeHTML(product.category)}
                    </span>

                    <h3>${escapeHTML(product.name)}</h3>

                    <div class="rating">
                        ★★★★★
                        <span>
                            ${product.rating}/5
                            (${product.reviews} reviews)
                        </span>
                    </div>

                    <p>${escapeHTML(product.description)}</p>

                    <div class="product-bottom">
                        <div class="price">
                            ${formatPrice(product.price)}
                            <span class="old-price">
                                ${formatPrice(product.original_price)}
                            </span>
                        </div>

                        <div class="card-actions">
                            <button class="details-button"
                                    data-action="details"
                                    data-id="${product.id}">
                                View
                            </button>

                            <button class="add-button"
                                    data-action="add"
                                    data-id="${product.id}">
                                + Cart
                            </button>
                        </div>
                    </div>
                </div>
            `;

            productGrid.appendChild(card);
        });

    } catch (error) {
        productGrid.textContent =
            "Unable to load products: " + error.message;
    }
}

// ----------------------------------
// PRODUCT ACTIONS
// ----------------------------------

productGrid.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");

    if (!button) return;

    const id = Number(button.dataset.id);

    try {
        if (button.dataset.action === "add") {
            await api("/api/cart/items", {
                method: "POST",
                body: JSON.stringify({
                    product_id: id,
                    quantity: 1
                })
            });

            showToast("✓ Product added to your cart");
            await loadCart();

        } else if (button.dataset.action === "details") {
            await showProductDetails(id);
        }

    } catch (error) {
        showToast(error.message);
    }
});

// ----------------------------------
// PRODUCT DETAILS MODAL
// ----------------------------------

async function showProductDetails(id) {
    const product = await api(`/api/products/${id}`);

    const discount = discountPercent(product);

    productModalContent.innerHTML = `
        <div class="detail-layout">

            <img class="detail-image"
                 src="${escapeHTML(product.image)}"
                 alt="${escapeHTML(product.name)}">

            <div class="detail-info">

                <span class="category-tag">
                    ${escapeHTML(product.category)}
                </span>

                <h2>${escapeHTML(product.name)}</h2>

                <div class="rating">
                    ★★★★★
                    <span>${product.rating}/5
                    (${product.reviews} reviews)</span>
                </div>

                <p>${escapeHTML(product.details)}</p>

                <div class="detail-price">
                    ${formatPrice(product.price)}
                    <span class="old-price">
                        ${formatPrice(product.original_price)}
                    </span>
                </div>

                <span class="discount-badge">
                    ${discount}% OFF
                </span>

                <div class="stock-label">
                    ✓ ${product.stock} units available
                </div>

                <button class="primary-button"
                        id="modal-add-button">
                    Add to Cart
                </button>

            </div>
        </div>
    `;

    productModal.classList.add("active");

    document.getElementById("modal-add-button")
        .addEventListener("click", async () => {
            try {
                await api("/api/cart/items", {
                    method: "POST",
                    body: JSON.stringify({
                        product_id: id,
                        quantity: 1
                    })
                });

                productModal.classList.remove("active");
                await loadCart();
                showToast("✓ Product added to cart");

            } catch (error) {
                showToast(error.message);
            }
        });
}

document.getElementById("product-modal-close")
    .addEventListener("click", () => {
        productModal.classList.remove("active");
    });

productModal.addEventListener("click", event => {
    if (event.target === productModal) {
        productModal.classList.remove("active");
    }
});

// ----------------------------------
// CART
// ----------------------------------

async function loadCart() {
    try {
        const cart = await api("/api/cart");

        cartCount.textContent = cart.item_count;
        cartTotal.textContent = formatPrice(cart.total);

        cartItems.innerHTML = "";

        if (cart.items.length === 0) {
            cartItems.innerHTML =
                "<p>Your cart is empty. Start shopping!</p>";
            return;
        }

        cart.items.forEach(item => {
            const element = document.createElement("div");
            element.className = "cart-item";

            element.innerHTML = `
                <div class="cart-item-icon">
                    <img src="${escapeHTML(item.image)}"
                         alt="${escapeHTML(item.name)}">
                </div>

                <div class="cart-item-info">
                    <h4>${escapeHTML(item.name)}</h4>
                    <p>${formatPrice(item.subtotal)}</p>

                    <div class="quantity-controls">

                        <button data-action="decrease"
                                data-id="${item.id}">−</button>

                        <span>${item.quantity}</span>

                        <button data-action="increase"
                                data-id="${item.id}">+</button>

                        <button class="remove-button"
                                data-action="remove"
                                data-id="${item.id}">
                            Remove
                        </button>

                    </div>
                </div>
            `;

            cartItems.appendChild(element);
        });

    } catch (error) {
        showToast(error.message);
    }
}

// Cart controls
cartItems.addEventListener("click", async event => {
    const button = event.target.closest("button[data-action]");

    if (!button) return;

    const id = Number(button.dataset.id);
    const action = button.dataset.action;

    try {
        if (action === "remove") {
            await api(`/api/cart/items/${id}`, {
                method: "DELETE"
            });

        } else {
            const cart = await api("/api/cart");
            const item = cart.items.find(p => p.id === id);

            if (!item) return;

            const quantity = action === "increase"
                ? item.quantity + 1
                : item.quantity - 1;

            await api(`/api/cart/items/${id}`, {
                method: "PATCH",
                body: JSON.stringify({ quantity })
            });
        }

        await loadCart();

    } catch (error) {
        showToast(error.message);
    }
});

// ----------------------------------
// OPEN AND CLOSE CART
// ----------------------------------

function openCart() {
    cartPanel.classList.add("active");
    overlay.classList.add("active");
    loadCart();
}

function closeCart() {
    cartPanel.classList.remove("active");
    overlay.classList.remove("active");
}

cartToggle.addEventListener("click", openCart);
cartClose.addEventListener("click", closeCart);
overlay.addEventListener("click", closeCart);

// ----------------------------------
// CHECKOUT
// ----------------------------------

document.getElementById("checkout-button")
    .addEventListener("click", async () => {

        try {
            const order = await api("/api/checkout", {
                method: "POST",
                body: JSON.stringify({})
            });

            closeCart();
            await loadCart();

            document.getElementById("order-id").textContent =
                order.order_id;

            document.getElementById("order-total").textContent =
                formatPrice(order.total);

            orderModal.classList.add("active");

        } catch (error) {
            showToast(error.message);
        }
    });

document.getElementById("order-close")
    .addEventListener("click", () => {
        orderModal.classList.remove("active");
    });

orderModal.addEventListener("click", event => {
    if (event.target === orderModal) {
        orderModal.classList.remove("active");
    }
});

// ----------------------------------
// SEARCH AND FILTER
// ----------------------------------

let searchTimeout;

searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);

    searchTimeout = setTimeout(() => {
        loadProducts();
    }, 300);
});

categorySelect.addEventListener("change", loadProducts);

// ----------------------------------
// INITIALIZE APPLICATION
// ----------------------------------

async function initializeStore() {
    await loadProducts();
    await loadCart();
}

initializeStore();
