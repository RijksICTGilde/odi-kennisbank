// Client-side facetfilter voor het bronnenoverzicht.
//
// Binnen één facet geldt OF (soort=kader OF soort=handreiking), tussen facetten
// geldt EN. Dat is wat mensen intuïtief verwachten: meer vinkjes binnen een
// groep verbreedt, een extra groep versmalt.
//
// Een filterrij is een nldd-list-item[checkbox]: de rij draagt de rol en de
// status, de nldd-checkbox erin is decoratief. Dat is hetzelfde model als de
// filter-sidebar van Wies. Twee dingen zijn daarbij belangrijk:
//
//   1. De rij beheert zijn eigen `checked`-attribuut. Zet je dat zelf op een
//      klik, dan draait het component het meteen weer terug -- daarom lezen we
//      de status na afloop uit in plaats van hem te forceren.
//   2. De klik ontstaat binnen de shadow DOM van een cel, dus event.target is
//      niet de rij. Het composed path bevat de rij wel, maar pas een paar
//      niveaus hoger (achter de interne button van het component), dus we
//      scannen het hele pad -- net als Wies met composedPath doet.
//
// De actieve filters staan in de query-string, zodat een gefilterd overzicht
// deelbaar en bookmarkbaar is en de terugknop werkt.

(function () {
  "use strict";

  const FACETTEN = ["expertises", "soorten", "doelgroepen", "fases", "themas"];

  function init() {
    const lijst = document.getElementById("bronnen-lijst");
    if (!lijst) return;

    const items = Array.from(lijst.querySelectorAll(".bron-item"));
    const tellerEl = document.getElementById("zichtbaar-aantal");
    const geenResultaten = document.getElementById("geen-resultaten");
    const wisKnop = document.getElementById("filters-wissen");
    const zoekVeld = document.getElementById("bronnen-zoek");
    const rijen = Array.from(document.querySelectorAll("nldd-list-item[data-facet]"));

    // De data-attributen zijn spatiegescheiden slugs; vooraf splitsen scheelt
    // werk bij elke filterslag.
    const itemWaarden = new Map(
      items.map((item) => [
        item,
        Object.fromEntries(
          FACETTEN.map((facet) => [
            facet,
            (item.dataset[facet] || "").split(" ").filter(Boolean),
          ])
        ),
      ])
    );

    // Titel, toelichting en eigenaar staan als kleine letters in data-tekst.
    const itemTekst = new Map(items.map((item) => [item, item.dataset.tekst || ""]));

    function zoekterm() {
      return (zoekVeld ? zoekVeld.value || "" : "").trim().toLowerCase();
    }

    const isAan = (rij) => rij.hasAttribute("checked");

    // De decoratieve nldd-checkbox in de rij volgt de rijstatus.
    function spiegelVakje(rij) {
      const vakje = rij.querySelector("nldd-checkbox");
      if (vakje) vakje.toggleAttribute("checked", isAan(rij));
    }

    // Alleen gebruiken om een rij programmatisch te zetten (URL herstellen,
    // filters wissen) -- niet tijdens een klik, want dan wint het component.
    function zetRij(rij, aan) {
      rij.toggleAttribute("checked", aan);
      spiegelVakje(rij);
    }

    function huidigeSelectie() {
      const selectie = {};
      for (const facet of FACETTEN) selectie[facet] = [];
      for (const rij of rijen) {
        if (isAan(rij)) selectie[rij.dataset.facet].push(rij.dataset.value);
      }
      return selectie;
    }

    function pastBijSelectie(waarden, selectie) {
      return FACETTEN.every((facet) => {
        const gekozen = selectie[facet];
        if (gekozen.length === 0) return true;
        return gekozen.some((waarde) => waarden[facet].includes(waarde));
      });
    }

    function pasToe({ updateUrl = true } = {}) {
      const selectie = huidigeSelectie();
      const term = zoekterm();
      const actief =
        FACETTEN.some((facet) => selectie[facet].length > 0) || term !== "";
      let zichtbaar = 0;

      for (const item of items) {
        // Zoekterm en facetten zijn allebei voorwaarden: samen versmallen ze.
        const past =
          pastBijSelectie(itemWaarden.get(item), selectie) &&
          (term === "" || itemTekst.get(item).includes(term));
        item.hidden = !past;
        if (past) zichtbaar++;
      }

      // Laat de facetlabels de zoekterm markeren, zodat je ziet waarom een
      // filteroptie overblijft. query werkt alleen op de attribuut-route van
      // nldd-text-cell, niet op slotted inhoud.
      for (const rij of rijen) {
        const cel = rij.querySelector("nldd-text-cell");
        if (cel) cel.setAttribute("query", term);
      }

      if (tellerEl) tellerEl.textContent = String(zichtbaar);
      if (geenResultaten) geenResultaten.hidden = zichtbaar !== 0;
      if (wisKnop) wisKnop.toggleAttribute("hidden", !actief);

      if (updateUrl) {
        const params = new URLSearchParams();
        for (const facet of FACETTEN) {
          for (const waarde of selectie[facet]) params.append(facet, waarde);
        }
        if (term) params.set("zoek", term);
        const query = params.toString();
        history.replaceState(null, "", query ? `?${query}` : window.location.pathname);
      }
    }

    // Gedelegeerd op document. De klik ontstaat in de shadow DOM van een cel,
    // dus event.target is niet de rij. Het composed path bevat de rij wel --
    // zij het pas een paar niveaus hoger, achter de interne button van het
    // component -- dus scannen we het pad zelf op het eerste list-item.
    document.addEventListener("click", (event) => {
      const rij = event
        .composedPath()
        .find(
          (knoop) =>
            knoop instanceof Element &&
            knoop.matches instanceof Function &&
            knoop.matches("nldd-list-item[data-facet]")
        );
      if (!rij) return;
      // Het component werkt zijn eigen checked-attribuut bij na dit event;
      // wacht dat af en lees dan pas de status, anders filteren we op de
      // waarde van vóór de klik.
      requestAnimationFrame(() => {
        spiegelVakje(rij);
        pasToe();
      });
    });

    // De knop op smalle schermen opent de sheet van nldd-sidebar-section.
    const openKnop = document.getElementById("filters-openen");
    const sectie = document.querySelector("nldd-sidebar-section");
    if (openKnop && sectie) {
      openKnop.addEventListener("click", () => {
        if (typeof sectie.show === "function") sectie.show();
        else if (typeof sectie.toggle === "function") sectie.toggle();
      });
    }

    if (wisKnop) {
      wisKnop.addEventListener("click", () => {
        for (const rij of rijen) zetRij(rij, false);
        if (zoekVeld) zoekVeld.value = "";
        pasToe();
      });
    }

    if (zoekVeld) {
      let timer = null;
      // nldd-search-field levert zijn waarde ook via event.detail; lees beide.
      ["input", "change", "search"].forEach((evt) => {
        zoekVeld.addEventListener(evt, (e) => {
          if (e.detail && typeof e.detail.value === "string") {
            zoekVeld.value = e.detail.value;
          }
          clearTimeout(timer);
          timer = setTimeout(() => pasToe(), 150);
        });
      });
    }

    // Selectie uit de URL herstellen, zodat een gedeelde link hetzelfde toont.
    const params = new URLSearchParams(window.location.search);
    if ([...params.keys()].length) {
      for (const rij of rijen) {
        zetRij(rij, params.getAll(rij.dataset.facet).includes(rij.dataset.value));
      }
      if (zoekVeld && params.get("zoek")) zoekVeld.value = params.get("zoek");
    }

    pasToe({ updateUrl: false });
  }

  // Wachten tot de componenten geüpgraded zijn, anders overschrijft de upgrade
  // de attributen die wij zetten.
  if (window.customElements) {
    Promise.all([
      customElements.whenDefined("nldd-list-item"),
      customElements.whenDefined("nldd-checkbox"),
      customElements.whenDefined("nldd-search-field"),
    ]).then(init);
  } else {
    document.addEventListener("DOMContentLoaded", init);
  }
})();
