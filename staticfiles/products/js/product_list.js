function toggleFilters(){
    document.querySelector(".sidebar").classList.toggle("active");
    document.querySelector(".shop-container").classList.toggle("blur-active");
}

/* CLOSE ON OUTSIDE CLICK */
document.addEventListener("click", function(e){

    const sidebar = document.querySelector(".sidebar");
    const button = document.querySelector(".mobile-filter-btn");

    if(!sidebar.contains(e.target) && !button.contains(e.target)){
        sidebar.classList.remove("active");
        document.querySelector(".shop-container").classList.remove("blur-active");
    }
});