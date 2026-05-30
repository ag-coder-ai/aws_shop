document.addEventListener("DOMContentLoaded", function () {

    const menuToggle = document.getElementById("menuToggle");
    const nav = document.getElementById("nav");

    const accountBtn = document.getElementById("accountBtn");
    const dropdown = document.getElementById("dropdownMenu");

    const logoutForm = document.getElementById("logoutForm");

    /* =========================
       MOBILE MENU
    ========================= */
    if (menuToggle && nav) {
        menuToggle.addEventListener("click", () => {
            nav.classList.toggle("show");
        });
    }

    /* =========================
       DROPDOWN TOGGLE
    ========================= */
    if (accountBtn && dropdown) {

        accountBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            dropdown.classList.toggle("show");
        });

        document.addEventListener("click", (e) => {
            if (!accountBtn.contains(e.target) && !dropdown.contains(e.target)) {
                dropdown.classList.remove("show");
            }
        });

        document.addEventListener("keydown", (e) => {
            if (e.key === "Escape") {
                dropdown.classList.remove("show");
            }
        });
    }

    /* =========================
       LOGOUT (REAL-TIME FIX)
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

                    // 🔥 INSTANT UI FIX (NO REFRESH NEEDED)
                    const account = document.getElementById("accountWrapper");
                    const guest = document.getElementById("guestMenu");

                    if (account) account.style.display = "none";
                    if (guest) guest.style.display = "flex";

                    window.location.href = data.redirect_url;

                } else {
                    alert(data.message);
                }

            } catch (err) {
                console.error(err);
                alert("Logout failed");
            }
        });
    }

});