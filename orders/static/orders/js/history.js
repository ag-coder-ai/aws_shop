// static/orders/js/history.js

document.querySelectorAll(".order-card").forEach(card => {

    card.addEventListener("mouseenter", () => {
        card.style.transform = "translateY(-2px)";
        card.style.transition = "0.3s";
    });

    card.addEventListener("mouseleave", () => {
        card.style.transform = "translateY(0px)";
    });

});