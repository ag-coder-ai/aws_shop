"use strict";

/* ==============================
   CSRF TOKEN
============================== */

function getCSRF() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

/* ==============================
   FETCH WRAPPER (POST JSON SAFE)
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
    return `₹${Number(value || 0).toFixed(2)}`;
}

/* ==============================
   UPDATE GLOBAL CART UI
============================== */

function updateCartUI(data) {

    if (!data) return;

    const totalEl = document.getElementById("cart-total");
    const subEl = document.getElementById("cart-subtotal");
    const countEl = document.getElementById("cart-count");

    if (totalEl) totalEl.innerText = money(data.cart_total);
    if (subEl) subEl.innerText = money(data.cart_subtotal);
    if (countEl) countEl.innerText = data.cart_count || 0;
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
            alert(res.message);
            return;
        }

        const data = res.data;

        const qtyEl = document.getElementById(`qty-${itemId}`);
        const totalEl = document.getElementById(`total-${itemId}`);

        if (qtyEl) qtyEl.innerText = data.quantity;
        if (totalEl) totalEl.innerText = money(data.item_total);

        updateCartUI(data);

        const row = document.getElementById(`cart-item-${itemId}`);
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
   REMOVE ITEM
============================== */

async function removeItem(itemId) {

    const row = document.getElementById(`cart-item-${itemId}`);

    if (row) row.style.opacity = "0.5";

    try {

        const res = await post("/cart/remove/", {
            item_id: itemId
        });

        if (!res.success) {
            alert(res.message);
            if (row) row.style.opacity = "1";
            return;
        }

        if (row) {
            row.style.transition = "0.3s";
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
   CART SYNC ON PAGE LOAD
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
   CHECKOUT NAVIGATION (FIXED)
============================== */

// SAFE: only attach if element exists
const checkoutBtn = document.getElementById("checkoutBtn");

if (checkoutBtn) {
    checkoutBtn.addEventListener("click", function (e) {
        e.preventDefault();
        window.location.href = "/checkout/";
    });
}