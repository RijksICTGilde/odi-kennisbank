// Zoeken over de bronnen, client-side met Fuse.js.
//
// De index staat als /index.json in de build (zie layouts/index.json) en wordt
// pas opgehaald bij de eerste keer openen: hij is een paar honderd kB en de
// meeste bezoekers zoeken niet.
//
// De UI is opgebouwd uit NLDD-componenten: een nldd-sheet met daarin een
// nldd-search-field en een nldd-list met resultaatrijen. Sheets zijn volgens
// het design system bedoeld voor "secundaire inhoud die context behoudt" —
// precies wat zoeken is; een modal zou de pagina onnodig onderbreken.

(function () {
  "use strict";

  var FUSE_OPTIES = {
    keys: [
      { name: "title", weight: 2 },
      { name: "content", weight: 1 },
    ],
    threshold: 0.3, // 0 = exact, 1 = alles matcht
    ignoreLocation: true,
    findAllMatches: true,
    minMatchCharLength: 2,
  };

  var MAX_RESULTATEN = 20;

  var fuse = null;
  var laadt = null;

  function init() {
    var sheet = document.getElementById("zoek-sheet");
    var veld = document.getElementById("zoek-veld");
    var lijst = document.getElementById("zoek-resultaten");
    var leeg = document.getElementById("zoek-leeg");
    if (!sheet || !veld || !lijst) return;

    var indexUrl = sheet.dataset.index;

    function laadIndex() {
      if (laadt) return laadt;
      laadt = fetch(indexUrl)
        .then(function (r) {
          return r.json();
        })
        .then(function (data) {
          fuse = new window.Fuse(data, FUSE_OPTIES);
        })
        .catch(function () {
          // Zonder index kan er niet gezocht worden; toon dat eerlijk in plaats
          // van een veld dat stil niets doet.
          lijst.innerHTML = "";
          if (leeg) {
            leeg.hidden = false;
            leeg.setAttribute("text", "Zoeken is nu niet beschikbaar");
            leeg.setAttribute("supporting-text", "De zoekindex kon niet geladen worden.");
          }
        });
      return laadt;
    }

    function toonResultaten(treffers, term) {
      lijst.innerHTML = "";
      var heeftTerm = term.length >= 2;

      if (leeg) {
        leeg.hidden = !heeftTerm || treffers.length > 0;
        if (!leeg.hidden) {
          leeg.setAttribute("text", "Niets gevonden");
          leeg.setAttribute("supporting-text", 'Geen bronnen voor "' + term + '".');
        }
      }
      if (!heeftTerm) return;

      treffers.slice(0, MAX_RESULTATEN).forEach(function (treffer) {
        var bron = treffer.item;
        var rij = document.createElement("nldd-list-item");
        rij.setAttribute("size", "md");
        rij.setAttribute("type", "link");
        rij.setAttribute("href", bron.url);

        var cel = document.createElement("nldd-text-cell");
        cel.setAttribute("text", bron.title);
        if (bron.content) {
          // Eén regel context, genoeg om een treffer te herkennen.
          cel.setAttribute("supporting-text", bron.content.slice(0, 120));
        }
        // query laat het component de zoekterm vetgedrukt markeren. Werkt
        // alleen op de attribuut-route, niet op slotted inhoud.
        cel.setAttribute("query", term);
        rij.appendChild(cel);
        lijst.appendChild(rij);
      });
    }

    function zoek() {
      var term = (veld.value || "").trim();
      if (!fuse) return;
      toonResultaten(term.length >= 2 ? fuse.search(term) : [], term);
    }

    function open() {
      sheet.show();
      laadIndex().then(function () {
        zoek();
        // Focus het echte input-element binnen de shadow DOM; defensief, zoals
        // de NLDD-skill voorschrijft.
        var native =
          veld.shadowRoot && veld.shadowRoot.querySelector("input");
        (native || veld).focus();
      });
    }

    // Alle zoekknoppen op de pagina openen dezelfde sheet.
    document.querySelectorAll("[data-zoek-open]").forEach(function (knop) {
      knop.addEventListener("click", open);
    });

    // Sneltoets '/' zoals in moza, maar niet terwijl je in een veld typt.
    document.addEventListener("keydown", function (e) {
      if (e.key !== "/" || e.metaKey || e.ctrlKey || e.altKey) return;
      var a = document.activeElement;
      var tag = a && a.tagName ? a.tagName.toLowerCase() : "";
      if (tag === "input" || tag === "textarea" || (a && a.isContentEditable)) return;
      if (tag.indexOf("nldd-") === 0 && tag.indexOf("field") !== -1) return;
      e.preventDefault();
      open();
    });

    // nldd-search-field levert zijn waarde via event.detail; lees defensief.
    var timer = null;
    ["input", "change", "nldd-input"].forEach(function (evt) {
      veld.addEventListener(evt, function (e) {
        if (e.detail && typeof e.detail.value === "string") veld.value = e.detail.value;
        clearTimeout(timer);
        timer = setTimeout(zoek, 150);
      });
    });
  }

  if (window.customElements) {
    Promise.all([
      customElements.whenDefined("nldd-sheet"),
      customElements.whenDefined("nldd-search-field"),
    ]).then(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
