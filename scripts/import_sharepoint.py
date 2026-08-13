#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Zet de SharePoint-export om in Hugo-content onder content/bronnen/.

De export is een Excel-CSV in Mac Roman met ';' als kolomscheiding en ';#' als
scheiding *binnen* meerwaardige velden. Beide gebruiken een puntkomma, dus de
volgorde van splitsen is essentieel: eerst de csv-module het bestand laten
parsen (die respecteert quoting), pas daarna op ';#' splitsen.

Het script is idempotent: het schrijft content/bronnen/ volledig opnieuw, zodat
een nieuwe export gewoon opnieuw gedraaid kan worden. Waarden die niet naar het
vocabulaire te mappen zijn worden niet geraden maar gerapporteerd.

Gebruik:
    ./scripts/import_sharepoint.py ~/Map1.csv
    ./scripts/import_sharepoint.py ~/Map1.csv --dry-run
"""

from __future__ import annotations

import argparse
import csv
import io
import re
import sys
import unicodedata
from datetime import date, datetime
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "sites" / "odi"
DATA = SITE / "data"
UITVOER = SITE / "content" / "kennisbank"

# De export is Mac Roman: daarin decoderen de 89 euro-tekens en de Nederlandse
# diakrieten (ë, é) correct, waar cp1252 en latin-1 mojibake opleveren.
BRON_ENCODING = "mac_roman"

MULTI_SCHEIDER = ";#"

# Facetsleutel -> meervoud zoals gedefinieerd onder 'taxonomies' in hugo.yaml.
# Hugo vult een taxonomie alleen als de frontmatter-sleutel het meervoud is.
FACET_MEERVOUD = {
    "soort": "soorten",
    "doelgroep": "doelgroepen",
    "fase": "fases",
    "thema": "themas",
}

# Bronnen die niet gepubliceerd worden. De export bevat verwijzingen naar
# documenten die als intern zijn gemarkeerd; die horen niet in een openbare
# repository, ook niet als alleen de titel overblijft.
NIET_PUBLICEREN_BRONNEN = {
    "Draaiboek uitvoering projecten",
}

# Persoonsnamen uit de export komen niet in de gepubliceerde content. Ze staan
# er als auteur van openbaar werk, maar in een publieke repository noemen we
# geen personen zonder dat zij daar iets over te zeggen hebben gehad.
#
# De vervangingen staan in data/anonimisering.yaml. Dat bestand staat in
# .gitignore: de namen zelf horen net zomin in de repository als in de content.
# Zonder dat bestand draait de import gewoon door, maar zonder anonimisering --
# de melding aan het eind waarschuwt daarvoor.
ANONIMISERING_BESTAND = SITE / "data" / "anonimisering.yaml"

# Titels en organisatienamen worden voor de publieke testrepo herschreven,
# zodat ze niet een-op-een matchen met de echte documenten. De vervangingen
# staan in hetzelfde (niet-gecommitte) bestand onder 'titel' en 'organisatie'.
# Zet DEMO_MODUS uit zodra de repo intern staat en de echte namen mogen.
DEMO_MODUS = True

# Velden die bewust niet in de gepubliceerde content terechtkomen.
# 'Interne beheersopmerking' bevat interne notities met e-mailadressen en
# afspraken; 'Itemtype' en 'Pad' zijn SharePoint-administratie.
NIET_PUBLICEREN = {"Interne beheersopmerking", "Itemtype", "Pad"}


def laad_yaml(naam: str) -> dict[str, Any]:
    with (DATA / naam).open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def laad_anonimisering() -> dict[str, dict[str, str]]:
    leeg = {"tekst": {}, "eigenaar": {}, "titel": {}, "organisatie": {}}
    if not ANONIMISERING_BESTAND.exists():
        return leeg
    data = yaml.safe_load(ANONIMISERING_BESTAND.read_text(encoding="utf-8")) or {}
    return {sleutel: data.get(sleutel) or {} for sleutel in leeg}


def herschrijf_titel(titel: str) -> str:
    """Varieer de bewoording zodat een titel niet exact matcht met het origineel.

    Alleen in demomodus. Woord-voor-woord vervanging houdt de titel leesbaar en
    herkenbaar van soort, zonder de precieze documentnaam prijs te geven.
    """
    if not DEMO_MODUS:
        return titel
    oorspronkelijk = titel
    for origineel, vervanging in ANONIMISERING["titel"].items():
        titel = re.sub(rf"\b{re.escape(origineel)}\b", vervanging, titel, flags=re.I)
    # De woordvervangingen raken lang niet elke titel; wat onveranderd blijft
    # zou nog exact matchen met het echte document. Een achtervoegsel maakt
    # duidelijk dat het om testdata gaat en houdt de titel leesbaar.
    if titel == oorspronkelijk:
        titel = f"{titel} (voorbeeld)"
    return titel


def herschrijf_organisatie(naam: str) -> str:
    if not DEMO_MODUS:
        return naam
    return ANONIMISERING["organisatie"].get(naam, naam)


ANONIMISERING = laad_anonimisering()


def anonimiseer(tekst: str) -> str:
    """Vervang persoonsnamen door een neutrale omschrijving."""
    for naam, vervanging in ANONIMISERING["tekst"].items():
        tekst = tekst.replace(naam, vervanging)
    if DEMO_MODUS:
        for origineel, vervanging in ANONIMISERING["organisatie"].items():
            tekst = tekst.replace(origineel, vervanging)
    return tekst


def schoon_tekst(waarde: str | None) -> str:
    """Normaliseer whitespace en verwijder exportartefacten uit een veld."""
    if not waarde:
        return ""
    tekst = unicodedata.normalize("NFC", waarde)
    # Non-breaking spaces uit Word/SharePoint worden gewone spaties.
    tekst = tekst.replace(" ", " ").replace(" ", " ")
    # Leidende vraagtekens zijn exportruis ("???Overzichtsplaat" -> "Overzichtsplaat").
    tekst = re.sub(r"^[?\s]+", "", tekst)
    tekst = re.sub(r"[ \t]+", " ", tekst)
    tekst = re.sub(r"\n{3,}", "\n\n", tekst)
    return anonimiseer(tekst.strip())


def slugify(waarde: str) -> str:
    tekst = unicodedata.normalize("NFKD", waarde)
    tekst = tekst.encode("ascii", "ignore").decode("ascii").lower()
    tekst = re.sub(r"[^a-z0-9]+", "-", tekst)
    return tekst.strip("-")


def splits_multi(waarde: str | None) -> list[str]:
    if not waarde:
        return []
    delen = [schoon_tekst(d) for d in waarde.split(MULTI_SCHEIDER)]
    return [d for d in delen if d]


def parse_datum(waarde: str | None) -> date | None:
    """Lees de Nederlandse datumnotaties uit de export (d-m-Y, met of zonder tijd)."""
    tekst = schoon_tekst(waarde)
    if not tekst:
        return None
    for patroon in ("%d-%m-%Y %H:%M", "%d-%m-%Y"):
        try:
            return datetime.strptime(tekst, patroon).date()
        except ValueError:
            continue
    return None


class Mapper:
    """Vertaalt ruwe exportwaarden naar slugs uit het vocabulaire."""

    def __init__(self) -> None:
        self.vocab = laad_yaml("vocabulaire.yaml")
        self.synoniemen = laad_yaml("synoniemen.yaml")
        # Weergavenaam -> slug, zodat de export op naam kan matchen.
        self.op_naam = {
            facet: {naam: slug for slug, naam in waarden.items()}
            for facet, waarden in self.vocab.items()
        }
        self.ongemapt: dict[str, set[str]] = {facet: set() for facet in self.vocab}

    def map(self, facet: str, ruwe_waarde: str) -> str | None:
        waarde = schoon_tekst(ruwe_waarde)
        if not waarde:
            return None
        syn = self.synoniemen.get(facet, {})
        if waarde in syn:
            return syn[waarde]
        if waarde in self.op_naam[facet]:
            return self.op_naam[facet][waarde]
        if waarde in self.vocab[facet]:
            return waarde
        self.ongemapt[facet].add(waarde)
        return None

    def map_lijst(self, facet: str, ruwe_waarde: str | None) -> list[str]:
        slugs = [self.map(facet, deel) for deel in splits_multi(ruwe_waarde)]
        # dict.fromkeys ontdubbelt met behoud van volgorde.
        return list(dict.fromkeys(s for s in slugs if s))


def lees_rijen(pad: Path) -> list[dict[str, str]]:
    ruw = pad.read_bytes().decode(BRON_ENCODING)
    # De export mengt CRLF, CR en LF door elkaar.
    ruw = ruw.replace("\r\n", "\n").replace("\r", "\n")
    return list(csv.DictReader(io.StringIO(ruw), delimiter=";"))


def bouw_bron(rij: dict[str, str], mapper: Mapper, index: int) -> dict[str, Any] | None:
    ruwe_titel = schoon_tekst(rij.get("Titel"))
    if not ruwe_titel or ruwe_titel in NIET_PUBLICEREN_BRONNEN:
        return None
    titel = herschrijf_titel(ruwe_titel)

    gewijzigd = parse_datum(rij.get("Gewijzigd"))
    review_vanaf = parse_datum(rij.get("Review vanaf"))
    linktekst = schoon_tekst(rij.get("Link (url)"))

    return {
        "titel": titel,
        "slug": slugify(titel) or f"bron-{index}",
        "soort": mapper.map_lijst("soort", rij.get("Soort")),
        "doelgroep": mapper.map_lijst("doelgroep", rij.get("Doelgroep")),
        "fase": mapper.map_lijst("fase", rij.get("Fase")),
        "thema": mapper.map_lijst("thema", rij.get("Thema")),
        "eigenaar": herschrijf_organisatie(
            ANONIMISERING["eigenaar"].get(
                schoon_tekst(rij.get("Eigenaar of publicist")),
                schoon_tekst(rij.get("Eigenaar of publicist")),
            )
        ),
        "linktekst": linktekst,
        "toelichting": schoon_tekst(rij.get("Toelichting")),
        "gewijzigd": gewijzigd,
        "review_vanaf": review_vanaf,
    }


def frontmatter(bron: dict[str, Any], vandaag: date) -> dict[str, Any]:
    """Stel de Hugo-frontmatter samen.

    De export bevat geen echte URL's: Excel heeft de hyperlinks platgeslagen tot
    hun weergavetekst. Zolang die ontbreken krijgt elke bron een placeholder en
    de vlag url_ontbreekt, zodat de site zichtbaar maakt wat nog aangevuld moet
    worden en een latere export ze simpelweg overschrijft.
    """
    fm: dict[str, Any] = {
        "title": bron["titel"],
        "slug": bron["slug"],
        "date": bron["gewijzigd"] or vandaag,
        "eigenaar": bron["eigenaar"],
    }
    if bron["toelichting"]:
        # Hugo's SEO-description; de volledige tekst staat in de body. Hugo
        # waarschuwt boven 160 tekens, dus knippen we inclusief het beletselteken.
        # Hugo telt bytes, geen tekens: een '€' in de tekst telt voor drie.
        # Daarom knippen we ruim onder de grens van 160.
        toelichting = " ".join(bron["toelichting"].split())
        if len(toelichting) > 150:
            toelichting = toelichting[:147].rstrip() + "..."
        fm["description"] = toelichting

    # Hugo koppelt frontmatter aan een taxonomie op de *meervoudsnaam* uit
    # hugo.yaml, niet op de enkelvoudige sleutel. Met 'soort:' blijft de
    # taxonomie leeg; het moet 'soorten:' zijn.
    for facet, meervoud in FACET_MEERVOUD.items():
        if bron[facet]:
            fm[meervoud] = bron[facet]

    # De hele export komt uit de kennisbank Programma- en projectmanagement.
    # Bronnen uit andere expertisegebieden krijgen hun eigen waarde zodra ze
    # worden toegevoegd.
    fm["expertises"] = ["agile-project-programma-en-portfoliomanagement"]

    fm["bron_url"] = "https://example.org/te-vervangen"
    fm["url_ontbreekt"] = True
    if bron["linktekst"]:
        fm["linktekst"] = bron["linktekst"]

    # Alleen de datum zelf, zonder afgeleid 'verlopen'-oordeel: bij 76 van de
    # 116 gevulde rijen is 'Review vanaf' gelijk aan 'Gewijzigd', wat erop
    # wijst dat het veld meeschrijft bij bewerken in plaats van bewust gepland
    # te zijn. Te wankel om er een waarschuwing op te baseren.
    if bron["review_vanaf"]:
        fm["review_vanaf"] = bron["review_vanaf"]

    return fm


def schrijf_bestand(bron: dict[str, Any], fm: dict[str, Any], doel: Path) -> None:
    kop = yaml.safe_dump(fm, allow_unicode=True, sort_keys=False, default_flow_style=False)
    body = bron["toelichting"] or "_Voor deze bron is nog geen toelichting beschikbaar._"
    doel.write_text(f"---\n{kop}---\n\n{body}\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Pad naar de SharePoint-export")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Toon alleen wat er zou gebeuren, schrijf niets",
    )
    args = parser.parse_args()

    if not args.csv.exists():
        print(f"Bestand niet gevonden: {args.csv}", file=sys.stderr)
        return 1

    mapper = Mapper()
    vandaag = date.today()
    rijen = lees_rijen(args.csv)

    bronnen: list[dict[str, Any]] = []
    for index, rij in enumerate(rijen, start=1):
        bron = bouw_bron(rij, mapper, index)
        if bron:
            bronnen.append(bron)

    # Titels die twee keer voorkomen zijn aparte records met afwijkende facetten
    # (zie 'Problematische legacy'). Ze worden niet samengevoegd -- dat is een
    # inhoudelijke keuze -- maar krijgen een oplopend achtervoegsel.
    gezien: dict[str, int] = {}
    for bron in bronnen:
        slug = bron["slug"]
        if slug in gezien:
            gezien[slug] += 1
            bron["slug"] = f"{slug}-{gezien[slug]}"
            bron["dubbel"] = True
        else:
            gezien[slug] = 1

    if not args.dry_run:
        if UITVOER.exists():
            for oud in UITVOER.glob("*.md"):
                if oud.name != "_index.md":
                    oud.unlink()
        UITVOER.mkdir(parents=True, exist_ok=True)
        for bron in bronnen:
            fm = frontmatter(bron, vandaag)
            schrijf_bestand(bron, fm, UITVOER / f"{bron['slug']}.md")

    zonder_review = sum(1 for b in bronnen if not b["review_vanaf"])
    dubbel = sum(1 for b in bronnen if b.get("dubbel"))
    zonder_thema = sum(1 for b in bronnen if not b["thema"])

    print(f"Gelezen rijen        : {len(rijen)}")
    print(f"Geschreven bronnen   : {len(bronnen)}{' (dry-run)' if args.dry_run else ''}")
    print(f"Zonder reviewdatum   : {zonder_review}")
    print(f"Dubbele titels       : {dubbel}")
    print(f"Zonder thema         : {zonder_thema}")
    print("URL's                : 0 echt, alle bronnen kregen een placeholder")
    if DEMO_MODUS:
        print("Demomodus            : titels en organisaties zijn herschreven")
    if not ANONIMISERING_BESTAND.exists():
        print(
            "\nLet op: data/anonimisering.yaml ontbreekt, dus persoonsnamen uit "
            "de export zijn niet vervangen."
        )

    heeft_ongemapt = any(mapper.ongemapt.values())
    if heeft_ongemapt:
        print("\nOngemapte waarden (vul aan in data/synoniemen.yaml):")
        for facet, waarden in mapper.ongemapt.items():
            for waarde in sorted(waarden):
                print(f"  {facet}: {waarde!r}")
    else:
        print("\nAlle facetwaarden zijn gemapt.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
