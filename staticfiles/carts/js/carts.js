"use strict";

/* ==============================
   CSRF TOKEN
============================== */

function getCSRF() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

/* ==============================
   FETCH WRAPPER
============================== */

async function post(url, body = {}) {

    const res = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRF()
        },
        body: new URLSearchParams(body)
    });

    return await res.json();
}

/* ==============================
   MONEY FORMAT
============================== */

function money(value) {

    if (value === null || value === undefined) return "₹0.00";

    // remove ₹, commas, spaces safely
    const cleanValue = String(value)
        .replace(/₹/g, "")
        .replace(/,/g, "")
        .trim();

    const num = Number(cleanValue);

    if (isNaN(num)) return "₹0.00";

    return new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        minimumFractionDigits: 2
    }).format(num);
}

/* ==============================
   SAFE ELEMENT HELPERS
============================== */

function el(id) {
    return document.getElementById(id);
}

/* ==============================
   UPDATE GLOBAL CART UI
============================== */

function updateCartUI(data) {

    if (!data) return;

    const totalEl = el("cart-total");
    const subEl = el("cart-subtotal");
    const countEl = el("cart-count");

    if (totalEl) totalEl.innerText = money(data.cart_total);
    if (subEl) subEl.innerText = money(data.cart_subtotal);
    if (countEl) countEl.innerText = data.cart_count || 0;

    /* 🔥 HANDLE EMPTY CART INSTANTLY */
    handleEmptyCart(data.cart_count);
}

/* ==============================
   EMPTY CART HANDLER (NEW)
============================== */

function handleEmptyCart(count) {

    if (count > 0) return;

    const cartItems = document.getElementById("cart-items-wrapper");
    const summary = document.querySelector(".cart-summary");
    const cartLeft = document.querySelector(".cart-left");

    if (cartItems) cartItems.remove();
    if (summary) summary.remove();

    if (cartLeft && !document.querySelector(".empty-cart")) {

        cartLeft.innerHTML += `
            <div class="empty-cart" id="empty-cart">
                <i class="fa fa-cart-shopping empty-cart-icon"></i>
                <h2>Your Cart Is Empty</h2>
                <p>Looks like you haven’t added anything yet.</p>
                <a href="/" class="continue-shopping-btn">
                    Continue Shopping
                </a>
            </div>
        `;
    }
}

/* ==============================
   UPDATE QUANTITY
============================== */

async function updateQty(itemId, action, btn = null) {

    try {

        if (btn) btn.disabled = true;

        const res = await post("/cart/update/", {
            item_id: itemId,
            action: action
        });

       if (!res.success) {
            showToast(res.message, "error");
            return;
        }

        const data = res.data;

        const qtyEl = el(`qty-${itemId}`);
        const totalEl = el(`total-${itemId}`);

        if (qtyEl) qtyEl.innerText = data.quantity;
        if (totalEl) totalEl.innerText = money(data.item_total);

        updateCartUI(data);

        /* 🔥 subtle animation */
        const row = el(`cart-item-${itemId}`);
        if (row) {
            row.classList.add("cart-updated");
            setTimeout(() => row.classList.remove("cart-updated"), 300);
        }

    } catch (err) {
        console.error("Update error:", err);
    } finally {
        if (btn) btn.disabled = false;
    }
}

/* ==============================
   REMOVE ITEM (IMPROVED)
============================== */

async function removeItem(itemId) {

    const row = el(`cart-item-${itemId}`);

    if (row) {
        row.style.opacity = "0.6";
        row.style.pointerEvents = "none";
    }

    try {

        const res = await post("/cart/remove/", {
            item_id: itemId
        });

        if (!res.success) {

            if (row) {
                row.style.opacity = "1";
                row.style.pointerEvents = "auto";
            }

            alert(res.message);
            return;
        }

        if (row) {
            row.style.transition = "0.25s ease";
            row.style.transform = "scale(0.95)";
            row.style.opacity = "0";

            setTimeout(() => row.remove(), 200);
        }

        updateCartUI(res.data);

    } catch (err) {
        console.error("Remove error:", err);
    }
}

/* ==============================
   CART SYNC ON LOAD
============================== */

document.addEventListener("DOMContentLoaded", async () => {

    try {

        const res = await post("/cart/summary/", {});

        if (res.success) {
            updateCartUI(res.data);
        }

    } catch (err) {
        console.error("Cart sync error:", err);
    }
});

/* ==============================
   CHECKOUT BUTTON SAFETY
============================== */

const checkoutBtn = document.getElementById("checkoutBtn");

if (checkoutBtn) {
    checkoutBtn.addEventListener("click", function (e) {
        e.preventDefault();
        window.location.href = "/checkout/";
    });
}


/* ==============================
   TOAST FUNCTION
============================== */

function showToast(message, type = "info") {

    const container = document.getElementById("toast-container");

    if (!container) return;

    const toast = document.createElement("div");

    toast.className = `toast ${type}`;

    toast.innerText = message;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(120%)";

        setTimeout(() => toast.remove(), 300);

    }, 2500);
}