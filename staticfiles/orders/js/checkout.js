"use strict";

/* =========================================
   CSRF TOKEN
========================================= */

function getCSRF() {

    return document.querySelector(
        "[name=csrfmiddlewaretoken]"
    )?.value || "";
}

/* =========================================
   API HELPER
========================================= */

async function post(url, body = {}) {

    const response = await fetch(url, {

        method: "POST",

        headers: {

            "Content-Type":
                "application/x-www-form-urlencoded",

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

    const oldToast = document.querySelector(
        ".custom-toast"
    );

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

document.getElementById("toast-container").appendChild(toast);

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

    document.querySelectorAll(".field-error")
        .forEach(el => {

            el.remove();
        });

    document.querySelectorAll(".input-error")
        .forEach(el => {

            el.classList.remove("input-error");
        });
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

        const errorDiv =
            document.createElement("div");

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
   VALIDATE FORM
========================================= */

function validateCheckoutForm() {

    clearErrors();

    let errors = {};

    const fullName = getVal("fullName");

    const phone = getVal("phone");

    const email = getVal("email")
        .toLowerCase();

    const address = getVal("address");

    const city = getVal("city");

    const state = getVal("state");

    const pincode = getVal("pincode");

    /* =========================================
       FULL NAME
    ========================================= */

    if (!fullName) {

        errors.full_name = [
            "Full name is required"
        ];

    } else if (fullName.length < 3) {

        errors.full_name = [
            "Full name must be at least 3 characters"
        ];
    }

    /* =========================================
       PHONE VALIDATION
    ========================================= */

    const phoneRegex = /^[6-9]\d{9}$/;

    if (!phoneRegex.test(phone)) {

        errors.phone = [
            "Enter valid 10 digit Indian mobile number"
        ];
    }

    /* =========================================
       EMAIL VALIDATION
    ========================================= */

    /* =========================================
   EMAIL VALIDATION
========================================= */

const disposableDomains = [

    "tempmail.com",
    "10minutemail.com",
    "guerrillamail.com",
    "mailinator.com",
    "yopmail.com",
    "fakeinbox.com",
    "trashmail.com",
    "sharklasers.com"
];

const emailValue = email.trim().toLowerCase();

/* =========================================
   BASIC CHECK
========================================= */

if (!emailValue) {

    errors.email = [
        "Email address is required"
    ];
}

/* =========================================
   LENGTH CHECK
========================================= */

else if (emailValue.length > 254) {

    errors.email = [
        "Email address is too long"
    ];
}

/* =========================================
   ADVANCED EMAIL REGEX
========================================= */

else {

    const emailRegex =
        /^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$/;

    if (!emailRegex.test(emailValue)) {

        errors.email = [
            "Enter valid email address"
        ];
    }

    else {

        const parts = emailValue.split("@");

        const localPart = parts[0];

        const domainPart = parts[1];

        /* =========================================
           LOCAL PART VALIDATION
        ========================================= */

        if (localPart.length > 64) {

            errors.email = [
                "Invalid email username"
            ];
        }

        else if (
            localPart.startsWith(".") ||
            localPart.endsWith(".")
        ) {

            errors.email = [
                "Invalid email format"
            ];
        }

        else if (localPart.includes("..")) {

            errors.email = [
                "Email cannot contain consecutive dots"
            ];
        }

        /* =========================================
           DOMAIN VALIDATION
        ========================================= */

        else if (!domainPart.includes(".")) {

            errors.email = [
                "Invalid email domain"
            ];
        }

        else if (
            domainPart.startsWith("-") ||
            domainPart.endsWith("-")
        ) {

            errors.email = [
                "Invalid email domain"
            ];
        }

        else if (domainPart.includes("..")) {

            errors.email = [
                "Invalid email domain"
            ];
        }

        /* =========================================
           BLOCK DISPOSABLE EMAILS
        ========================================= */

        else if (
            disposableDomains.includes(domainPart)
        ) {

            errors.email = [
                "Temporary email addresses are not allowed"
            ];
        }

        /* =========================================
           DOMAIN EXTENSION VALIDATION
        ========================================= */

        else {

            const domainParts =
                domainPart.split(".");

            const extension =
                domainParts[domainParts.length - 1];

            if (extension.length < 2) {

                errors.email = [
                    "Invalid email domain extension"
                ];
            }
        }
    }
}

    /* =========================================
       ADDRESS VALIDATION
    ========================================= */

    if (!address) {

        errors.address_line_1 = [
            "Address is required"
        ];

    } else if (address.length < 10) {

        errors.address_line_1 = [
            "Address is too short"
        ];
    }

    /* =========================================
       CITY VALIDATION
    ========================================= */

    if (!city) {

        errors.city = [
            "City is required"
        ];
    }

    /* =========================================
       STATE VALIDATION
    ========================================= */

    if (!state) {

        errors.state = [
            "State is required"
        ];
    }

    /* =========================================
       PINCODE VALIDATION
    ========================================= */

    const pincodeRegex = /^[1-9][0-9]{5}$/;

    if (!pincodeRegex.test(pincode)) {

        errors.postal_code = [
            "Enter valid 6 digit Indian pincode"
        ];
    }

    /* =========================================
       SHOW ERRORS
    ========================================= */

    if (Object.keys(errors).length > 0) {

        showFieldErrors(errors);

        return false;
    }

    return true;
}

/* =========================================
   PAYMENT OPTION ACTIVE STATE
========================================= */

document.querySelectorAll(".payment-option")
    .forEach(option => {

        option.addEventListener("click", () => {

            document.querySelectorAll(
                ".payment-option"
            ).forEach(el => {

                el.classList.remove("active");
            });

            option.classList.add("active");
        });
    });

/* =========================================
   CHECKOUT
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    console.log("Checkout JS Loaded");

    const btn =
        document.getElementById("placeOrderBtn");

    if (!btn) {

        console.error(
            "Place Order button not found"
        );

        return;
    }

    btn.addEventListener("click", async (e) => {

        e.preventDefault();

        clearErrors();

        btn.disabled = true;

        btn.innerText = "Processing...";

        try {

            /* =========================================
               FRONTEND VALIDATION
            ========================================= */

            const isValid =
                validateCheckoutForm();

            if (!isValid) {

                btn.disabled = false;

                btn.innerText =
                    "Place Secure Order";

                return;
            }

            const paymentMethod =
                document.querySelector(
                    'input[name="payment"]:checked'
                )?.value;

            if (!paymentMethod) {

                showToast(
                    "Select payment method",
                    "error"
                );

                btn.disabled = false;

                btn.innerText =
                    "Place Secure Order";

                return;
            }

            /* =========================================
               CREATE CHECKOUT
            ========================================= */

            const checkout = await post(

                "/orders/create-checkout/",

                {

                    full_name:
                        getVal("fullName"),

                    phone:
                        getVal("phone"),

                    email:
                        getVal("email")
                            .toLowerCase(),

                    address:
                        getVal("address"),

                    city:
                        getVal("city"),

                    state:
                        getVal("state"),

                    pincode:
                        getVal("pincode"),

                    payment_method:
                        paymentMethod
                }
            );

            console.log(
                "CHECKOUT RESPONSE:",
                checkout
            );

            /* =========================================
               BACKEND VALIDATION ERRORS
            ========================================= */

            if (!checkout.success) {

                if (checkout.field_errors) {

                    showFieldErrors(
                        checkout.field_errors
                    );

                } else {

                    showToast(
                        checkout.message ||
                        "Checkout failed",
                        "error"
                    );
                }

                return;
            }

            /* =========================================
               COD FLOW
            ========================================= */

            if (paymentMethod === "COD") {

                showToast(
                    "Order placed successfully"
                );

                setTimeout(() => {

                    window.location.href =
                        `/orders/success/?order_id=${checkout.order_id}`;

                }, 1000);

                return;
            }

            /* =========================================
               PREPAID FLOW
            ========================================= */

            const payment = await post(

                "/payments/create/",

                {
                    amount: checkout.amount
                }
            );

            console.log(
                "PAYMENT RESPONSE:",
                payment
            );

            if (!payment.success) {

                showToast(
                    payment.message ||
                    "Payment initialization failed",
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

                description:
                    "Secure Checkout",

                handler: async function (
                    response
                ) {

                    try {

                        const verify =
                            await post(

                                "/payments/verify/",

                                {

                                    razorpay_order_id:
                                        response
                                        .razorpay_order_id,

                                    razorpay_payment_id:
                                        response
                                        .razorpay_payment_id,

                                    razorpay_signature:
                                        response
                                        .razorpay_signature
                                }
                            );

                        console.log(
                            "VERIFY RESPONSE:",
                            verify
                        );

                        if (verify.success) {

                            showToast(
                                "Payment successful"
                            );

                            setTimeout(() => {

                                window.location.href =
                                    `/orders/success/?order_id=${verify.order_id}`;

                            }, 1200);

                        } else {

                            showToast(

                                verify.message ||

                                "Payment verification failed",

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

                    name:
                        getVal("fullName"),

                    email:
                        getVal("email"),

                    contact:
                        getVal("phone")
                },

                theme: {
                    color: "#111827"
                }
            };

            const razorpay =
                new Razorpay(options);

            razorpay.open();

        } catch (err) {

            console.error(
                "CHECKOUT ERROR:",
                err
            );

            showToast(
                "Unable to process checkout",
                "error"
            );

        } finally {

            btn.disabled = false;

            btn.innerText =
                "Place Secure Order";
        }
    });
});