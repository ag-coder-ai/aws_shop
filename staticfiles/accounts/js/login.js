const loginForm = document.getElementById("loginForm");

const emailInput = document.getElementById("email");
const passwordInput = document.getElementById("password");

const loginBtn = document.getElementById("loginBtn");

const loader = document.querySelector(".loader");
const btnText = document.querySelector(".btn-text");

const togglePassword = document.getElementById("togglePassword");

/* =========================
   TOAST
========================= */

function showToast(message, type="info"){

    const container = document.getElementById("toast-container");

    const toast = document.createElement("div");

    toast.className = `toast ${type}`;

    toast.innerText = message;

    container.appendChild(toast);

    setTimeout(() => {

        toast.style.opacity = "0";
        toast.style.transform = "translateX(100%)";
        toast.style.transition = "0.4s";

        setTimeout(() => {
            toast.remove();
        }, 400);

    }, 3000);

}

/* =========================
   VALIDATION
========================= */

function validateEmail(email){

    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);

}

function clearErrors(){

    document.querySelectorAll(".error").forEach(el => {
        el.innerText = "";
    });

}

function validateForm(){

    let valid = true;

    clearErrors();

    if(emailInput.value.trim() === ""){

        emailInput.parentElement.querySelector(".error").innerText =
            "Email is required";

        valid = false;

    }
    else if(!validateEmail(emailInput.value.trim())){

        emailInput.parentElement.querySelector(".error").innerText =
            "Invalid email format";

        valid = false;

    }

    if(passwordInput.value.trim() === ""){

        passwordInput.parentElement.parentElement
            .querySelector(".error").innerText =
            "Password is required";

        valid = false;

    }
    else if(passwordInput.value.length < 8){

        passwordInput.parentElement.parentElement
            .querySelector(".error").innerText =
            "Minimum 8 characters required";

        valid = false;

    }

    return valid;

}

/* =========================
   PASSWORD TOGGLE
========================= */

togglePassword.addEventListener("click", () => {

    if(passwordInput.type === "password"){

        passwordInput.type = "text";
        togglePassword.innerText = "🙈";

    }else{

        passwordInput.type = "password";
        togglePassword.innerText = "👁";

    }

});

/* =========================
   LIVE VALIDATION
========================= */

emailInput.addEventListener("input", validateForm);
passwordInput.addEventListener("input", validateForm);

/* =========================
   AJAX LOGIN
========================= */

loginForm.addEventListener("submit", async function(e){

    e.preventDefault();

    if(!validateForm()){
        return;
    }

    loginBtn.disabled = true;

    loader.classList.remove("hidden");

    btnText.innerText = "Please wait...";

    const formData = new FormData(loginForm);

    try{

        const response = await fetch(window.location.href, {

            method:"POST",

            headers:{
                "X-Requested-With":"XMLHttpRequest"
            },

            body:formData

        });

        const data = await response.json();

        if(data.success){

            showToast(data.message, "success");

            setTimeout(() => {
                window.location.href = data.redirect_url;
            }, 1200);

        }else{

            showToast(data.message, "error");

        }

    }catch(error){

        showToast(
            "Something went wrong. Please try again.",
            "error"
        );

    }finally{

        loginBtn.disabled = false;

        loader.classList.add("hidden");

        btnText.innerText = "Login";

    }

});