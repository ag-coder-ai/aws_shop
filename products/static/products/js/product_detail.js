/* ======================================================
   VARIANT DATA
====================================================== */

const variantData = JSON.parse(

    document.getElementById(
        "variant-data"
    ).textContent

);


/* ======================================================
   GLOBAL VARIABLES
====================================================== */

let selectedSize = null;

let selectedColor = null;

let selectedVariant = null;

let quantity = 1;


/* ======================================================
   IMAGE CHANGE
====================================================== */

function changeImage(img){

    document.getElementById(
        "mainImage"
    ).src = img.src;

}


/* ======================================================
   SIZE SELECT
====================================================== */

function selectSize(btn){

    document.querySelectorAll(
        ".size-btn"
    ).forEach(button => {

        button.classList.remove(
            "active"
        );

    });

    btn.classList.add("active");

    selectedSize = btn.dataset.size;

    updateVariant();
}


/* ======================================================
   COLOR SELECT
====================================================== */

function selectColor(btn){

    document.querySelectorAll(
        ".color-btn"
    ).forEach(button => {

        button.classList.remove(
            "active"
        );

    });

    btn.classList.add("active");

    selectedColor = btn.dataset.color;

    updateVariant();
}


/* ======================================================
   UPDATE VARIANT
====================================================== */

function updateVariant(){

    const priceEl = document.getElementById(
        "price"
    );

    const stockEl = document.getElementById(
        "stockStatus"
    );

    const addBtn = document.getElementById(
        "addToCartBtn"
    );

    if(!selectedSize || !selectedColor){

        addBtn.disabled = true;

        return;
    }

    const variant = variantData.find(v =>

        v.size === selectedSize &&
        v.color === selectedColor

    );

    console.log("SELECTED VARIANT:", variant);

    if(variant){

        selectedVariant = variant;

        // PRICE
        priceEl.innerText = variant.price;

        // STOCK
        if(variant.stock > 0){

            stockEl.innerText =
                `In Stock (${variant.stock})`;

            stockEl.style.color = "green";

            addBtn.disabled = false;

        } else {

            stockEl.innerText =
                "Out Of Stock";

            stockEl.style.color = "red";

            addBtn.disabled = true;
        }

    } else {

        selectedVariant = null;

        priceEl.innerText = "--";

        stockEl.innerText =
            "Variant Not Available";

        stockEl.style.color = "red";

        addBtn.disabled = true;
    }
}


/* ======================================================
   QUANTITY INCREASE
====================================================== */

function increaseQty(){

    if(!selectedVariant) return;

    if(quantity < selectedVariant.stock){

        quantity++;

        document.getElementById(
            "quantity"
        ).value = quantity;
    }
}


/* ======================================================
   QUANTITY DECREASE
====================================================== */

function decreaseQty(){

    if(quantity > 1){

        quantity--;

        document.getElementById(
            "quantity"
        ).value = quantity;
    }
}


/* ======================================================
   SHOW MESSAGE
====================================================== */

function showMessage(message, color){

    const messageBox = document.getElementById(
        "cartMessage"
    );

    messageBox.innerText = message;

    messageBox.style.color = color;
}

/* ======================================================
   ADD TO CART
====================================================== */
/* ======================================================
   ADD TO CART
====================================================== */

const addToCartBtn = document.getElementById(
    "addToCartBtn"
);

if(addToCartBtn){

    addToCartBtn.addEventListener("click", function(){

        console.log("ADD TO CART CLICKED");

        // =====================================
        // VARIANT VALIDATION
        // =====================================

        if(!selectedVariant){

            showMessage(
                "Please select size and color",
                "red"
            );

            return;
        }

        const csrfToken = document.querySelector(
            "[name=csrfmiddlewaretoken]"
        ).value;

        fetch("/cart/add/", {

            method: "POST",

            headers: {

                "Content-Type":
                    "application/x-www-form-urlencoded",

                "X-CSRFToken":
                    csrfToken

            },

            body: new URLSearchParams({

                variant_id: selectedVariant.id,

                quantity: quantity

            })

        })

        .then(async response => {

            const data = await response.json();

            // =====================================
            // LOGIN REQUIRED
            // =====================================

            if(response.status === 401){

                showMessage(
                    "Please login to continue",
                    "red"
                );

                setTimeout(() => {

                    window.location.href =
                        "/login/";

                }, 1500);

                return;
            }

            // =====================================
            // SUCCESS
            // =====================================

            if(data.success){

                showMessage(
                    data.message,
                    "green"
                );

                setTimeout(() => {

                    window.location.href = "/cart/";

                }, 800);

            }

            // =====================================
            // FAILED
            // =====================================

            else {

                showMessage(
                    data.message,
                    "red"
                );
            }

        })

        .catch(error => {

            console.log(error);

            showMessage(
                "Something went wrong",
                "red"
            );

        });

    });

}


/* ======================================================
   WISHLIST
====================================================== */

function getSelectedVariantId() {

    const size = document.querySelector(".size-btn.active")?.dataset.size;
    const color = document.querySelector(".color-btn.active")?.dataset.color;

    if (!size || !color) return null;

    const variants = JSON.parse(
        document.getElementById("variant-data").textContent
    );

    const match = variants.find(v =>
        v.size === size && v.color === color
    );

    return match ? match.id : null;
}


/* =========================================
   WISHLIST TOGGLE
========================================= */

function showToast(message, type = "success") {

    /* REMOVE OLD TOAST */

    const oldToast =
        document.querySelector(".custom-toast");

    if (oldToast) {
        oldToast.remove();
    }

    /* CREATE TOAST */

    const toast = document.createElement("div");

    toast.className = `custom-toast ${type}`;

    toast.innerHTML = `
        <div class="toast-content">

            <div class="toast-icon">
                ${type === "success" ? "✓" : "!"}
            </div>

            <div class="toast-message">
                ${message}
            </div>

        </div>
    `;

    document.body.appendChild(toast);

    /* SHOW */

    setTimeout(() => {
        toast.classList.add("show");
    }, 100);

    /* HIDE */

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => {
            toast.remove();
        }, 300);

    }, 3000);
}

document.addEventListener("DOMContentLoaded", () => {

    const wishlistBtn = document.getElementById("wishlistBtn");

    if (!wishlistBtn) return;

    function isAuthenticated() {

        return document.body.dataset.authenticated === "true";
    }

    wishlistBtn.addEventListener("click", async () => {

        /* =========================================
           LOGIN CHECK
        ========================================= */

        if (!isAuthenticated()) {

            showToast(
                "Please login to use wishlist",
                "error"
            );

            return;
        }

        /* =========================================
           PRODUCT ID
        ========================================= */

        const productId =
            wishlistBtn.dataset.productId;

        if (!productId) {

            showToast(
                "Product not found",
                "error"
            );

            return;
        }

        try {

            /* =========================================
               API REQUEST
            ========================================= */

            const res = await post(
                "/wishlist/toggle/",
                {
                    product_id: productId
                }
            );

            console.log("Wishlist Response:", res);

            /* =========================================
               SUCCESS
            ========================================= */

            if (res.success) {

                /* TOGGLE HEART */

                wishlistBtn.classList.toggle(
                    "active",
                    res.added
                );

               wishlistBtn.innerHTML = res.added
                        ? "❤️"
                        : "🤍";

                    wishlistBtn.classList.toggle(
                        "active",
                        res.added
                    );

                /* SUCCESS TOAST */

                if (res.added) {

                    showToast(
                        "Successfully added to wishlist",
                        "success"
                    );

                } else {

                    showToast(
                        "Removed from wishlist",
                        "success"
                    );
                }

            } else {

                showToast(
                    res.message || "Wishlist failed",
                    "error"
                );
            }

        } catch (err) {

            console.error("Wishlist Error:", err);

            showToast(
                "Something went wrong",
                "error"
            );
        }
    });
});


let currentIndex = 0;
let totalSlides = document.querySelectorAll(".slide").length;
const track = document.getElementById("sliderTrack");

function showSlide(index){
    if(index >= totalSlides) currentIndex = 0;
    else if(index < 0) currentIndex = totalSlides - 1;
    else currentIndex = index;

    track.style.transform = `translateX(-${currentIndex * 100}%)`;
}

function nextSlide(){
    showSlide(currentIndex + 1);
}

let autoSlide = setInterval(nextSlide, 2000); // 3 sec auto slide

// pause on hover
document.querySelector(".slider-wrapper").addEventListener("mouseenter", () => {
    clearInterval(autoSlide);
});

document.querySelector(".slider-wrapper").addEventListener("mouseleave", () => {
    autoSlide = setInterval(nextSlide, 3000);
});

// thumbnail click
function goToSlide(index){
    showSlide(index);
}

// optional initial
showSlide(0);




function openSizeChart(){
    document.getElementById("sizeModal").classList.add("active");
    document.getElementById("sizeOverlay").classList.add("active");
}

function closeSizeChart(){
    document.getElementById("sizeModal").classList.remove("active");
    document.getElementById("sizeOverlay").classList.remove("active");
}

/* ESC key close (PRO UX) */
document.addEventListener("keydown", function(e){
    if(e.key === "Escape"){
        closeSizeChart();
    }
});



