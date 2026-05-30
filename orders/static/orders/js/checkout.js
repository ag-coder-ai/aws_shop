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

    if (oldToast) {
        oldToast.remove();
    }

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

    setTimeout(() => {
        toast.classList.add("show");
    }, 100);

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => {
            toast.remove();
        }, 300);

    }, 3000);
}

/* =========================================
   CLEAR ERRORS
========================================= */

function clearErrors() {

    document.querySelectorAll(".field-error").forEach(el => {
        el.remove();
    });

    document.querySelectorAll(".input-error").forEach(el => {
        el.classList.remove("input-error");
    });
}

/* =========================================
   FIELD ERRORS
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
   CHECKOUT
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    console.log("Checkout JS Loaded");

    const btn = document.getElementById("placeOrderBtn");

    if (!btn) {
        console.error("Place Order button not found");
        return;
    }

    btn.addEventListener("click", async (e) => {

        e.preventDefault();

        console.log("BUTTON CLICKED");

        clearErrors();

        btn.disabled = true;

        btn.innerText = "Processing...";

        try {

            const paymentMethod =
                document.querySelector('input[name="payment"]:checked')?.value;

            if (!paymentMethod) {

                showToast("Select payment method", "error");

                return;
            }

            /* =========================================
               CREATE CHECKOUT
            ========================================= */

            const checkout = await post("/orders/create-checkout/", {

                full_name: getVal("fullName"),

                phone: getVal("phone"),

                email: getVal("email"),

                address: getVal("address"),

                city: getVal("city"),

                state: getVal("state"),

                pincode: getVal("pincode"),

                payment_method: paymentMethod
            });

            console.log("CHECKOUT RESPONSE:", checkout);

            /* =========================================
               VALIDATION ERRORS
            ========================================= */

           console.log("FULL CHECKOUT RESPONSE:", checkout);

            if (!checkout.success) {

                console.log("CHECKOUT FAILED");

                if (checkout.field_errors) {

                    console.log("FIELD ERRORS:", checkout.field_errors);

                    showFieldErrors(checkout.field_errors);

                } else {

                    console.log("MESSAGE:", checkout.message);

                    showToast(
                        checkout.message || "Checkout failed",
                        "error"
                    );
                }

                return;
            }


            /* =========================================
               COD FLOW
            ========================================= */

            if (paymentMethod === "COD") {

                showToast("Order placed successfully");

                setTimeout(() => {

                    window.location.href =
                        `/orders/success/?order_id=${checkout.order_id}`;

                }, 1000);

                return;
            }

            /* =========================================
               PREPAID FLOW
            ========================================= */

          /* =========================================
               PREPAID FLOW
            ========================================= */

            const payment = await post(

                "/payments/create/",

                {
                    amount: checkout.amount
                }

            );

            console.log("PAYMENT RESPONSE:", payment);

            if (!payment.success) {

                showToast(
                    payment.message || "Payment initialization failed",
                    "error"
                );

                return;
            }

            /* =========================================
               RAZORPAY
            ========================================= */

            const options = {

                key: payment.key,

                amount: payment.amount,

                currency: payment.currency,

                order_id: payment.order_id,

                name: "Fashion Hub",

                description: "Secure Checkout",

                handler: async function (response) {

                    try {

                        const verify = await post("/payments/verify/", {

                            razorpay_order_id:
                                response.razorpay_order_id,

                            razorpay_payment_id:
                                response.razorpay_payment_id,

                            razorpay_signature:
                                response.razorpay_signature
                        });

                        console.log("VERIFY RESPONSE:", verify);

                        if (verify.success) {

                            showToast("Payment successful");

                            setTimeout(() => {

                                window.location.href =
                                    `/orders/success/?order_id=${verify.order_id}`;

                            }, 1200);

                        } else {

                            showToast(
                                verify.message || "Payment verification failed",
                                "error"
                            );
                        }

                    } catch (err) {

                        console.error(err);

                        showToast(
                            "Payment verification failed",
                            "error"
                        );
                    }
                },

                modal: {

                    ondismiss: function () {

                        showToast(
                            "Payment cancelled",
                            "error"
                        );
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

            showToast(
                "Unable to process checkout",
                "error"
            );

        } finally {

            btn.disabled = false;

            btn.innerText = "Place Secure Order";
        }
    });
});