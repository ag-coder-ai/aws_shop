const password = document.getElementById(
    "password"
);

const strengthBar = document.querySelector(
    ".strength-bar"
);

const strengthText = document.querySelector(
    ".strength-text"
);

/* PASSWORD STRENGTH */

password.addEventListener(
    "input",
    function () {

        const value = password.value;

        let strength = 0;

        if (value.length >= 8) strength++;

        if (/[A-Z]/.test(value)) strength++;

        if (/[a-z]/.test(value)) strength++;

        if (/\d/.test(value)) strength++;

        if (/[!@#$%^&*]/.test(value)) strength++;

        if (strength <= 2) {

            strengthBar.style.width = "30%";
            strengthBar.style.background = "red";
            strengthText.innerText = "Weak Password";

        }

        else if (strength <= 4) {

            strengthBar.style.width = "70%";
            strengthBar.style.background = "orange";
            strengthText.innerText = "Medium Password";

        }

        else {

            strengthBar.style.width = "100%";
            strengthBar.style.background = "green";
            strengthText.innerText = "Strong Password";

        }

    }
);

/* SHOW PASSWORD */

document.querySelectorAll(
    ".toggle-password"
).forEach(icon => {

    icon.addEventListener(
        "click",
        function () {

            const target = document.getElementById(
                this.dataset.target
            );

            if (target.type === "password") {

                target.type = "text";

            } else {

                target.type = "password";

            }

        }
    );

});

/* FORM VALIDATION */

document.getElementById(
    "signupForm"
).addEventListener(
    "submit",
    function (e) {

        let valid = true;

        document.querySelectorAll(
            ".field-error"
        ).forEach(el => el.innerText = "");

        /* NAME */

        const fullName = document.getElementById(
            "full_name"
        );

        if (fullName.value.trim().length < 3) {

            fullName.parentElement
            .querySelector(".field-error")
            .innerText =
            "Enter valid full name.";

            valid = false;

        }
                    /* PHONE */

            const phone = document.getElementById(
                "phone"
            );

            const phonePattern =
            /^[6-9]\d{9}$/;

            if (!phonePattern.test(phone.value)) {

                phone.parentElement
                .querySelector(".field-error")
                .innerText =
                "Enter valid mobile number.";

                valid = false;

            }

        /* EMAIL */

        const email = document.getElementById(
            "email"
        );

        const emailPattern =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

        if (!emailPattern.test(email.value)) {

            email.parentElement
            .querySelector(".field-error")
            .innerText =
            "Enter valid email address.";

            valid = false;

        }

        /* PASSWORD */

        const password = document.getElementById(
            "password"
        );

        if (password.value.length < 8) {

            password.parentElement.parentElement
            .querySelector(".field-error")
            .innerText =
            "Password must be minimum 8 characters.";

            valid = false;

        }

        /* CONFIRM */

        const confirm = document.getElementById(
            "confirm_password"
        );

        if (
            password.value !== confirm.value
        ) {

            confirm.parentElement.parentElement
            .querySelector(".field-error")
            .innerText =
            "Passwords do not match.";

            valid = false;

        }

        if (!valid) {

            e.preventDefault();

        }

    }
);