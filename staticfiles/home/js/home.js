
/* =========================================
   MOBILE MENU TOGGLE
========================================= */

const menuToggle = document.getElementById("menuToggle");
const nav = document.getElementById("nav");

if (menuToggle && nav) {
    menuToggle.addEventListener("click", () => {
        nav.classList.toggle("active");
    });
}


/* =========================================
   ACCOUNT DROPDOWN (CLICK BASED)
   → replaces hover (more professional UX)
========================================= */

const accountBtn = document.querySelector(".account-btn");
const dropdown = document.querySelector(".dropdown-menu");

if (accountBtn && dropdown) {

    accountBtn.addEventListener("click", function (e) {
        e.stopPropagation(); // prevent body click close
        dropdown.classList.toggle("show");
    });

}


/* =========================================
   CLOSE DROPDOWN WHEN CLICKING OUTSIDE
========================================= */

document.addEventListener("click", function (e) {

    const accountDropdown = document.querySelector(".account-dropdown");

    if (!accountDropdown) return;

    if (!accountDropdown.contains(e.target)) {

        const dropdown = accountDropdown.querySelector(".dropdown-menu");

        if (dropdown) {
            dropdown.classList.remove("show");
        }
    }

});


/* =========================================
   ESC KEY CLOSE DROPDOWN
========================================= */

document.addEventListener("keydown", function (e) {

    if (e.key === "Escape") {

        const dropdown = document.querySelector(".dropdown-menu");

        if (dropdown) {
            dropdown.classList.remove("show");
        }
    }

});


/* ================= CAROUSEL ================= */

const slides = document.querySelectorAll(".slide");
const dots = document.querySelectorAll(".dot");

let currentIndex = 0;
let interval = null;

/* SHOW SLIDE FUNCTION */
function showSlide(index) {

    slides.forEach((slide, i) => {
        slide.classList.remove("active");
        dots[i].classList.remove("active");
    });

    slides[index].classList.add("active");
    dots[index].classList.add("active");

    currentIndex = index;
}

/* NEXT SLIDE */
function nextSlide() {
    let nextIndex = (currentIndex + 1) % slides.length;
    showSlide(nextIndex);
}

/* AUTO PLAY */
function startCarousel() {
    interval = setInterval(nextSlide, 4000); // 4 seconds
}

/* DOT CLICK EVENT */
dots.forEach((dot, index) => {
    dot.addEventListener("click", () => {
        clearInterval(interval);
        showSlide(index);
        startCarousel();
    });
});

/* INIT */
if (slides.length > 0) {
    showSlide(0);
    startCarousel();
}