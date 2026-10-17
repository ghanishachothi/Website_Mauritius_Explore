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
    // Saved in the database (same Favourite table as the My Experiences page),
    // so a heart clicked here shows up there and the other way round.
    function csrfToken() {
        const el = document.querySelector("[name=csrfmiddlewaretoken]");
        return el ? el.value : "";
    }

    document.querySelectorAll(".eb-heart").forEach(function (btn) {
        btn.addEventListener("click", function (e) {
            e.preventDefault();      // the heart sits inside a link on the cards
            e.stopPropagation();
            const url = btn.dataset.toggleUrl;
            if (!url || btn.dataset.busy) return;
            btn.dataset.busy = "1";

            fetch(url, {
                method: "POST",
                headers: {
                    "X-CSRFToken": csrfToken(),
                    "X-Requested-With": "XMLHttpRequest"
                },
                credentials: "same-origin"
            })
                .then(function (r) { if (!r.ok) throw new Error("bad response"); return r.json(); })
                .then(function () {
                    // reload so every list on the page (preview, View All, cards) is in sync
                    window.location.reload();
                })
                .catch(function () {
                    delete btn.dataset.busy;
                    alert("Could not update your favourites. Please try again.");
                });
        });
    });
});