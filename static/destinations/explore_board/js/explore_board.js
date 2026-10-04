// FILE: apps/destinations/static/destinations/explore_board/js/explore_board.js

document.addEventListener("DOMContentLoaded", function () {

    // ---------- Navigation bar arrows ----------
    const navTrack = document.getElementById("navTrack");
    const navPrev = document.getElementById("navPrev");
    const navNext = document.getElementById("navNext");

    if (navTrack) {
        const step = 260;
        navPrev.addEventListener("click", () => navTrack.scrollBy({ left: -step }));
        navNext.addEventListener("click", () => navTrack.scrollBy({ left: step }));

        // Start the bar two tabs before the active page
        // (Guides & Packages | Island Calendar | Explore Board | Reserve...)
        function alignNav() {
            const links = Array.from(navTrack.querySelectorAll(".eb-nav-link"));
            const activeIndex = links.findIndex((a) => a.classList.contains("active"));
            if (activeIndex < 2) return;
            const target = links[activeIndex - 2];
            const offset = target.getBoundingClientRect().left - navTrack.getBoundingClientRect().left;
            navTrack.style.scrollBehavior = "auto";
            navTrack.scrollLeft += offset - 10;
            navTrack.style.scrollBehavior = "";
        }
        alignNav();
        window.addEventListener("load", alignNav);   // run again once fonts have loaded
    }

    // ---------- Dropdowns: "View All" buttons + profile icon ----------
    // Click a button -> its dropdown opens. Click it again (or anywhere else) -> it closes.
    const toggles = document.querySelectorAll("[data-dropdown-toggle]");

    function closeAll(except) {
        toggles.forEach(function (btn) {
            const panel = document.getElementById(btn.dataset.dropdownToggle);
            if (panel && panel !== except) {
                panel.hidden = true;
                btn.setAttribute("aria-expanded", "false");
            }
        });
    }

    toggles.forEach(function (btn) {
        const panel = document.getElementById(btn.dataset.dropdownToggle);
        if (!panel) return;
        btn.addEventListener("click", function (e) {
            e.stopPropagation();
            const willOpen = panel.hidden;
            closeAll(panel);                       // only one dropdown open at a time
            panel.hidden = !willOpen;
            btn.setAttribute("aria-expanded", willOpen ? "true" : "false");
        });
        panel.addEventListener("click", (e) => e.stopPropagation());
    });

    document.addEventListener("click", () => closeAll(null));
    document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeAll(null); });

    // ---------- Favourite hearts ----------
    // Front-end only for now (no favourites model yet): un-hearting removes the
    // card from view immediately, everywhere it appears (the preview row AND the
    // "View All" dropdown), but a page refresh brings it back since nothing is
    // saved to the database yet. Wire this to a real endpoint once favourites exist.
    document.querySelectorAll(".eb-heart").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const icon = btn.querySelector("i");
            const nowFav = !btn.classList.contains("is-fav");
            btn.classList.toggle("is-fav", nowFav);
            btn.setAttribute("aria-pressed", nowFav ? "true" : "false");
            icon.classList.toggle("fa-solid", nowFav);
            icon.classList.toggle("fa-regular", !nowFav);

            if (!nowFav) {
                const slug = btn.dataset.slug;
                document.querySelectorAll('[data-slug="' + slug + '"]').forEach(function (el) {
                    const row = el.closest(".eb-fav-item, .eb-dropdown-row");
                    if (row) row.remove();
                });
                document.querySelectorAll(".eb-dropdown-row").forEach(function (row) {
                    const link = row.getAttribute("href") || "";
                    if (link.includes("experience=" + slug)) row.remove();
                });
            }
            // Later: send btn.dataset.slug to a favourites endpoint to save it.
        });
    });
});