"use strict";

/* =========================================
   CSRF
========================================= */

function getCSRF() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

/* =========================================
   EMPTY TEMPLATE
========================================= */

function getEmptyWishlistHTML() {
    return `
        <div class="empty-wishlist">

            <img src="/static/images/empty-wishlist.png" alt="Wishlist Empty">

            <h2>Your wishlist is empty 💔</h2>

            <p>Explore products and save your favorites.</p>

            <a href="/" class="shop-btn">
                Continue Shopping
            </a>

        </div>
    `;
}

/* =========================================
   REMOVE WISHLIST (FIXED)
========================================= */

async function removeWishlist(productId, btn) {

    try {

        const response = await fetch("/wishlist/toggle/", {
            method: "POST",
            headers: {
                "Content-Type": "application/x-www-form-urlencoded",
                "X-CSRFToken": getCSRF()
            },
            body: new URLSearchParams({
                product_id: productId
            })
        });

        const data = await response.json();

        if (!data.success) return;

        const card = btn.closest(".wishlist-card");
        const grid = document.querySelector(".wishlist-grid");

        if (!card) return;

        /* smooth remove animation */
        card.style.transition = "all 0.25s ease";
        card.style.opacity = "0";
        card.style.transform = "scale(0.9)";

        setTimeout(() => {

            card.remove();

            /* =========================================
               PROPER EMPTY CHECK (IMPORTANT FIX)
            ========================================= */

            const remainingCards = document.querySelectorAll(".wishlist-card");

            if (remainingCards.length === 0 && grid) {
                grid.replaceWith(
                    document.createRange().createContextualFragment(
                        getEmptyWishlistHTML()
                    )
                );
            }

        }, 250);

    } catch (err) {
        console.error(err);
    }
}