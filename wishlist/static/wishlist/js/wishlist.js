"use strict";

/* =========================================
   CSRF
========================================= */

function getCSRF() {

    return document.querySelector(
        "[name=csrfmiddlewaretoken]"
    )?.value || "";
}

/* =========================================
   REMOVE WISHLIST
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

        if (data.success) {

            const card = btn.closest(".wishlist-card");

            card.style.opacity = "0";

            setTimeout(() => {
                card.remove();
            }, 300);

        }

    } catch (err) {

        console.error(err);
    }
}