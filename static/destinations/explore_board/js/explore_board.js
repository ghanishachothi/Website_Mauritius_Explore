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

// Explore board: favourites update in place; View All lists expand in place with a scrollbar
(function () {
  var MORE = ".eb-rec-extra, .eb-more";
  var sections = [
    { btn: "recToggle",  list: "recGrid",  open: "eb-rec-open" },
    { btn: "favToggle",  list: "favList",  open: "eb-list-open" },
    { btn: "itinToggle", list: "itinList", open: "eb-list-open" },
    { btn: "bookToggle", list: "bookList", open: "eb-list-open" }
  ];
  function el(id) { return document.getElementById(id); }
  function mark(list) {
    list.querySelectorAll(MORE).forEach(function (n) {
      n.dataset.more = n.classList.contains("eb-more") ? "eb-more" : "eb-rec-extra";
    });
  }
  function showExtras(list, show) {
    list.querySelectorAll("[data-more]").forEach(function (n) { n.classList.toggle(n.dataset.more, !show); });
  }
  function stopsOf(list) {
    return Array.prototype.filter.call(list.children, function (n) { return n.classList.contains("eb-stop"); });
  }
  function layoutCollapsed(list) {
    var items = stopsOf(list);
    list.classList.toggle("eb-has-more", items.length > 4);
    items.forEach(function (n, i) {
      if (i < items.length - 1) { n.dataset.arrow = (i === 3) ? "cont" : "1"; } else { delete n.dataset.arrow; }
    });
  }
  function layoutSnake(list) {
    var items = stopsOf(list);
    items.forEach(function (n, i) {
      var row = Math.floor(i / 4), pos = i % 4;
      var col = row % 2 === 0 ? pos + 1 : 4 - pos;
      n.style.gridRow = String(row + 1);
      n.style.gridColumn = String(col);
      n.dataset.dir = row % 2 === 0 ? "r" : "l";
      delete n.dataset.arrow;
      if (i === items.length - 1) { n.dataset.last = "1"; }
      else if (pos === 3) { n.dataset.turn = "1"; }
    });
  }
  function clearSnake(list) {
    Array.prototype.forEach.call(list.children, function (n) {
      n.style.gridRow = "";
      n.style.gridColumn = "";
      delete n.dataset.dir;
      delete n.dataset.last;
      delete n.dataset.turn;
    });
    layoutCollapsed(list);
  }
  function setOpen(s, open) {
    var btn = el(s.btn), list = el(s.list);
    if (!btn || !list) return;
    if (open) {
      if (s.list === "itinList") {
        list.classList.add("eb-snake");
        layoutSnake(list);
        var oc = list.closest(".eb-card");
        if (oc) oc.classList.add("eb-itin-open");
      } else {
        list.style.maxHeight = list.offsetHeight + "px";
      }
      showExtras(list, true);
      list.classList.add(s.open);
    } else {
      list.classList.remove(s.open);
      list.style.maxHeight = "";
      showExtras(list, false);
      if (s.list === "itinList") {
        list.classList.remove("eb-snake");
        clearSnake(list);
        var cc = list.closest(".eb-card");
        if (cc) cc.classList.remove("eb-itin-open");
      }
      list.scrollTop = 0;
    }
    btn.setAttribute("aria-expanded", open ? "true" : "false");
    btn.innerHTML = open ? 'Show Less <i class="fa-solid fa-chevron-up"></i>' : btn.dataset.label;
  }

  sections.forEach(function (s) {
    var btn = el(s.btn), list = el(s.list);
    if (!btn || !list) return;
    btn.dataset.label = btn.innerHTML;
    mark(list);
    if (s.list === "itinList") { layoutCollapsed(list); }
    if (!list.querySelector("[data-more]")) { btn.hidden = true; return; }
    btn.addEventListener("click", function (e) {
      e.stopPropagation();
      setOpen(s, !list.classList.contains(s.open));
    });
  });

  function keepState() {
    try {
      var open = sections.filter(function (s) { var l = el(s.list); return l && l.classList.contains(s.open); })
                         .map(function (s) { return s.list; });
      sessionStorage.setItem("ebState", JSON.stringify({ y: window.scrollY, open: open }));
    } catch (err) {}
  }
  try {
    var saved = sessionStorage.getItem("ebState");
    if (saved) {
      sessionStorage.removeItem("ebState");
      var st = JSON.parse(saved);
      sections.forEach(function (s) {
        var b = el(s.btn);
        if (st.open.indexOf(s.list) > -1 && b && !b.hidden) setOpen(s, true);
      });
      window.scrollTo(0, st.y);
    }
  } catch (err) {}

  function refreshFrom(html) {
    var doc = new DOMParser().parseFromString(html, "text/html");
    var s = sections[1];
    var list = el(s.list), nl = doc.getElementById(s.list), btn = el(s.btn);
    if (!list || !nl || !btn) return false;
    var wasOpen = list.classList.contains(s.open), top = list.scrollTop;
    list.innerHTML = nl.innerHTML;
    mark(list);
    var hasMore = !!list.querySelector("[data-more]");
    btn.hidden = !hasMore;
    if (!hasMore) {
      list.classList.remove(s.open);
      list.style.maxHeight = "";
      btn.setAttribute("aria-expanded", "false");
      btn.innerHTML = btn.dataset.label;
    } else if (wasOpen) {
      showExtras(list, true);
      list.scrollTop = top;
    }
    doc.querySelectorAll("#recGrid .eb-heart[data-slug]").forEach(function (nb) {
      var cb = document.querySelector('#recGrid .eb-heart[data-slug="' + nb.dataset.slug + '"]');
      if (cb) {
        cb.className = nb.className;
        cb.innerHTML = nb.innerHTML;
        cb.setAttribute("aria-pressed", nb.getAttribute("aria-pressed") || "false");
      }
    });
    return true;
  }

  function csrf() {
    var t = document.querySelector("[name=csrfmiddlewaretoken]");
    return t ? t.value : "";
  }

  document.addEventListener("click", function (e) {
    var btn = e.target.closest ? e.target.closest(".eb-heart") : null;
    if (!btn) return;
    e.preventDefault();
    e.stopPropagation();
    var url = btn.dataset.toggleUrl;
    if (!url || btn.dataset.busy) return;
    btn.dataset.busy = "1";
    fetch(url, { method: "POST", headers: { "X-CSRFToken": csrf(), "X-Requested-With": "XMLHttpRequest" }, credentials: "same-origin" })
      .then(function (r) { if (!r.ok) throw new Error("bad response"); return r.json(); })
      .then(function () { return fetch(window.location.href, { credentials: "same-origin" }); })
      .then(function (r) { if (!r.ok) throw new Error("bad response"); return r.text(); })
      .then(function (html) {
        delete btn.dataset.busy;
        if (!refreshFrom(html)) { keepState(); window.location.reload(); }
      })
      .catch(function () {
        delete btn.dataset.busy;
        alert("Could not update your favourites. Please try again.");
      });
  }, true);
})();
