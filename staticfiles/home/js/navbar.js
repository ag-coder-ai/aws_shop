document.addEventListener("DOMContentLoaded", function () {



    const menuToggle = document.getElementById("menuToggle");
    const nav = document.getElementById("nav");
    const overlay = document.querySelector(".nav-overlay");

    const accountBtn = document.getElementById("accountBtn");
    const dropdown = document.getElementById("dropdownMenu");
    const logoutForm = document.getElementById("logoutForm");

    /* =========================
       MOBILE MENU TOGGLE
    ========================= */

    if (menuToggle && nav && overlay) {

        menuToggle.addEventListener("click", () => {

            nav.classList.toggle("active");
            overlay.classList.toggle("active");

            const isOpen = nav.classList.contains("active");

            menuToggle.innerHTML = isOpen ? "✕" : "☰";

            document.body.style.overflow = isOpen ? "hidden" : "auto";
        });

        overlay.addEventListener("click", () => {
            nav.classList.remove("active");
            overlay.classList.remove("active");
            menuToggle.innerHTML = "☰";
            document.body.style.overflow = "auto";
        });

        nav.querySelectorAll("a").forEach(link => {
            link.addEventListener("click", () => {
                nav.classList.remove("active");
                overlay.classList.remove("active");
                menuToggle.innerHTML = "☰";
                document.body.style.overflow = "auto";
            });
        });
    }

    /* =========================
       ACCOUNT DROPDOWN (FIXED SAFE VERSION)
    ========================= */

    if (accountBtn && dropdown) {
        accountBtn.addEventListener("click", function (e) {
            e.preventDefault();
            e.stopPropagation();
            dropdown.classList.toggle("show");
        });

        document.addEventListener("click", function (e) {

            if (!accountBtn.contains(e.target) &&
                !dropdown.contains(e.target)) {

                dropdown.classList.remove("show");
            }
        });

    } else {
        console.warn("Dropdown elements not found on this page");
    }

    /* =========================
       LOGOUT HANDLER
    ========================= */

    if (logoutForm) {

        logoutForm.addEventListener("submit", async function (e) {
            e.preventDefault();

            const btn = logoutForm.querySelector("button");
            btn.disabled = true;
            btn.innerText = "Logging out...";

            try {
                const res = await fetch("/logout/", {
                    method: "POST",
                    headers: {
                        "X-Requested-With": "XMLHttpRequest"
                    },
                    body: new FormData(logoutForm)
                });

                const data = await res.json();

                if (data.success) {
                    window.location.href = data.redirect_url;
                } else {
                    alert(data.message);
                }

            } catch (err) {
                console.error("Logout error:", err);
                alert("Logout failed");
            }
        });
    }

});