
"use strict";

/* =========================================
   CSRF TOKEN
========================================= */

function getCSRF() {
    return document.querySelector("[name=csrfmiddlewaretoken]")?.value || "";
}

/* =========================================
   API HELPER
========================================= */

async function post(url, body = {}) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded",
            "X-CSRFToken": getCSRF()
        },
        body: new URLSearchParams(body)
    });

    return await response.json();
}

/* =========================================
   GET VALUE
========================================= */

function getVal(id) {
    const el = document.getElementById(id);
    return el ? el.value.trim() : "";
}

/* =========================================
   TOAST
========================================= */

function showToast(message, type = "success") {
    const oldToast = document.querySelector(".custom-toast");

    if (oldToast) oldToast.remove();

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

    document.getElementById("toast-container").appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 100);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

/* =========================================
   CLEAR ERRORS
========================================= */

function clearErrors() {
    document.querySelectorAll(".field-error").forEach(el => el.remove());
    document.querySelectorAll(".input-error").forEach(el => el.classList.remove("input-error"));
}

/* =========================================
   SHOW FIELD ERRORS
========================================= */

function showFieldErrors(errors) {
    clearErrors();

    const fieldMap = {
        full_name: "fullName",
        phone: "phone",
        email: "email",
        address_line_1: "address",
        city: "city",
        state: "state",
        postal_code: "pincode"
    };

    Object.keys(errors).forEach(field => {
        const inputId = fieldMap[field] || field;
        const input = document.getElementById(inputId);
        if (!input) return;

        input.classList.add("input-error");

        const errorDiv = document.createElement("div");
        errorDiv.className = "field-error";
        errorDiv.innerText = errors[field][0];

        input.parentNode.appendChild(errorDiv);

        input.addEventListener("input", () => {
            input.classList.remove("input-error");
            errorDiv.remove();
        }, { once: true });
    });
}

/* =========================================
   VALIDATION
========================================= */

function validateCheckoutForm() {

    clearErrors();

    let errors = {};

    const fullName = getVal("fullName");
    const phone = getVal("phone");
    const email = getVal("email").toLowerCase();
    const address = getVal("address");
    const city = getVal("city");
    const state = getVal("state");
    const pincode = getVal("pincode");

    if (!fullName) {
        errors.full_name = ["Full name is required"];
    } else if (fullName.length < 3) {
        errors.full_name = ["Full name must be at least 3 characters"];
    }

    const phoneRegex = /^[6-9]\d{9}$/;
    if (!phoneRegex.test(phone)) {
        errors.phone = ["Enter valid 10 digit Indian mobile number"];
    }

    if (!email) {
        errors.email = ["Email address is required"];
    }

    if (!address) {
        errors.address_line_1 = ["Address is required"];
    }

    if (address && address.length < 10) {
        errors.address_line_1 = ["Address is too short"];
    }

    if (!city) {
        errors.city = ["City is required"];
    }

    if (!state) {
        errors.state = ["State is required"];
    }

    const pincodeRegex = /^[1-9][0-9]{5}$/;
    if (!pincodeRegex.test(pincode)) {
        errors.postal_code = ["Enter valid 6 digit Indian pincode"];
    }

    if (Object.keys(errors).length > 0) {
        showFieldErrors(errors);
        return false;
    }

    return true;
}

/* =========================================
   PAYMENT OPTION ACTIVE STATE
========================================= */

document.querySelectorAll(".payment-option").forEach(option => {
    option.addEventListener("click", () => {
        document.querySelectorAll(".payment-option").forEach(el => el.classList.remove("active"));
        option.classList.add("active");
    });
});

/* =========================================
   CHECKOUT
========================================= */

let appliedCoupon = null;

document.addEventListener("click", async (e) => {

    if (!e.target || e.target.id !== "placeOrderBtn") return;

    e.preventDefault();

    const btn = e.target;

    console.log("🔥 PLACE ORDER CLICKED");

    btn.disabled = true;
    btn.innerText = "Processing...";

    try {

        const isValid = validateCheckoutForm();

        if (!isValid) {
            btn.disabled = false;
            btn.innerText = "Place Secure Order";
            return;
        }

        const paymentMethod = document.querySelector('input[name="payment"]:checked')?.value;

        if (!paymentMethod) {
            showToast("Select payment method", "error");
            btn.disabled = false;
            btn.innerText = "Place Secure Order";
            return;
        }

        /* =========================
           CREATE CHECKOUT
        ========================= */
        const couponSnapshot = appliedCoupon;
        const checkout = await post("/orders/create-checkout/", {
            full_name: getVal("fullName"),
            phone: getVal("phone"),
            email: getVal("email").toLowerCase(),
            address: getVal("address"),
            city: getVal("city"),
            state: getVal("state"),
            pincode: getVal("pincode"),
            coupon_code: couponSnapshot,
            payment_method: paymentMethod
        });

        if (!checkout.success) {
            if (checkout.field_errors) {
                showFieldErrors(checkout.field_errors);
            } else {
                showToast(checkout.message || "Checkout failed", "error");
            }
            btn.disabled = false;
            btn.innerText = "Place Secure Order";
            return;
        }

        /* =========================
           COD FLOW
        ========================= */

        if (paymentMethod === "COD") {
            showToast("Order placed successfully");

            setTimeout(() => {
                window.location.href = `/orders/success/?order_id=${checkout.order_id}`;
            }, 1000);

            return;
        }

        /* =========================
           PREPAID FLOW
        ========================= */


        const payment = await post("/payments/create/", {
            coupon_code: appliedCoupon
        });

        if (!payment.success) {
            showToast(payment.message || "Payment initialization failed", "error");
            btn.disabled = false;
            btn.innerText = "Place Secure Order";
            return;
        }

        /* =========================
           RAZORPAY
        ========================= */

        const options = {

            key: payment.key,
            amount: payment.amount,
            currency: payment.currency,
            order_id: payment.order_id,

            name: "UnityThreads",
            description: "Secure Checkout",

        handler: function (response) {

                console.log("PAYMENT SUCCESS:", response);

                showToast("Payment successful. Processing order...");

                // webhook will handle everything

                setTimeout(() => {
                    window.location.href = "/orders/success/?status=processing";
                }, 1500);
            },

            modal: {
                escape: false,
                backdropclose: false,
                ondismiss: function () {
                    showToast("Payment cancelled", "error");
                }
            },

            prefill: {
                name: getVal("fullName"),
                email: getVal("email"),
                contact: getVal("phone")
            },

            theme: {
                color: "#111827"
            }
        };

        const razorpay = new Razorpay(options);
        razorpay.open();

    } catch (err) {

        console.error("CHECKOUT ERROR:", err);
        showToast("Unable to process checkout", "error");

    } finally {
        btn.disabled = false;
        btn.innerText = "Place Secure Order";
    }
});

/* =========================================
   COUPON SYSTEM
========================================= */

/* =========================================
   COUPON SYSTEM
========================================= */

window.applyCoupon = async function(code) {

    console.log("APPLY COUPON FUNCTION CALLED");

    const btn = document.getElementById("applyCouponBtn");
    const msg = document.getElementById("couponMessage");
    const text = document.getElementById("couponBtnText");

    // 🛑 SAFE GUARD
    if (!btn || !msg || !text) {
        console.error("DOM elements missing on page");
        return;
    }

    if (!code) {
        showToast("Enter coupon code", "error");
        return;
    }

    if (appliedCoupon === code) {
        showToast("Coupon already applied", "info");
        return;
    }

    btn.disabled = true;
    text.innerText = "Applying...";

    try {

        const res = await post("/apply-coupon/", {
            coupon_code: code
        });

        if (!res.success) {
            msg.style.color = "red";
            msg.innerText = res.message;
            showToast(res.message, "error");
            return;
        }

        appliedCoupon = res.coupon || code;

        msg.style.color = "green";
        msg.innerText = `Coupon applied: ${appliedCoupon}`;

        document.getElementById("discountAmount").innerText = "₹" + res.discount;
        document.getElementById("grandTotal").innerText = "₹" + res.final_total;

        showToast("Coupon applied successfully");

    } catch (err) {
        console.error(err);
        showToast("Something went wrong", "error");
    } finally {
        btn.disabled = false;
        text.innerText = "Apply";
    }
};


/* =========================================
   APPLY FROM LIST
========================================= */

window.applyCouponFromList = function (code) {
    document.getElementById("couponCode").value = code;

    setTimeout(() => {
        applyCoupon(code);
    }, 50);
};


/* =========================================
   BUTTON EVENT HANDLER
========================================= */

document.addEventListener("DOMContentLoaded", function () {

    const btn = document.getElementById("applyCouponBtn");

    if (btn) {
        btn.addEventListener("click", function () {
            const code = document.getElementById("couponCode").value.trim();
            applyCoupon(code);
        });
    }

});
