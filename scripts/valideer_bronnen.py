#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml"]
# ///
"""Controleer de frontmatter van alle bronnen tegen het vocabulaire.

Draait in CI bij elke pull request. Zonder deze controle sluipt de vervuiling
die we bij de import hebben opgeruimd (MSP naast Managing Successful
Programmes, Kwaliteitsmanagament met tikfout) er via handmatige bijdragen zo
weer in, en dan werken de filters niet meer.

Gebruik:
    ./scripts/valideer_bronnen.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent
BRONNEN = ROOT / "sites" / "odi" / "content" / "kennisbank"

# 'title' is hard verplicht: zonder titel is een bron onbruikbaar.
VERPLICHT = ("title",)

# Aanbevolen velden leveren een waarschuwing op, geen fout. De export bevat
# records die in SharePoint zelf al onvolledig zijn (zoals 'Agile Mindset'
# zonder Soort); die willen we zichtbaar maken zonder de build te blokkeren.
AANBEVOLEN = ("soorten", "eigenaar")

FACETTEN = {
    "soorten": "soort",
    "doelgroepen": "doelgroep",
    "fases": "fase",
    "themas": "thema",
}


def lees_frontmatter(pad: Path) -> dict[str, Any] | None:
    tekst = pad.read_text(encoding="utf-8")
    if not tekst.startswith("---"):
        return None
    _, _, rest = tekst.partition("---\n")
    kop, sep, _ = rest.partition("\n---")
    if not sep:
        return None
    return yaml.safe_load(kop) or {}


def main() -> int:
    vocab = yaml.safe_load((ROOT / "sites" / "odi" / "data" / "vocabulaire.yaml").read_text(encoding="utf-8"))
    fouten: list[str] = []
    waarschuwingen: list[str] = []
    aantal = 0

    for pad in sorted(BRONNEN.glob("*.md")):
        if pad.name == "_index.md":
            continue
        aantal += 1
        naam = pad.relative_to(ROOT)

        fm = lees_frontmatter(pad)
        if fm is None:
            fouten.append(f"{naam}: geen geldige YAML-frontmatter gevonden")
            continue

        for veld in VERPLICHT:
            if not fm.get(veld):
                fouten.append(f"{naam}: verplicht veld '{veld}' ontbreekt of is leeg")

        for veld in AANBEVOLEN:
            if not fm.get(veld):
                waarschuwingen.append(f"{naam}: aanbevolen veld '{veld}' is leeg")

        for meervoud, enkelvoud in FACETTEN.items():
            waarden = fm.get(meervoud)
            if waarden is None:
                continue
            if not isinstance(waarden, list):
                fouten.append(f"{naam}: '{meervoud}' moet een lijst zijn")
                continue
            toegestaan = vocab.get(enkelvoud, {})
            for waarde in waarden:
                if waarde not in toegestaan:
                    fouten.append(
                        f"{naam}: onbekende waarde {waarde!r} in '{meervoud}'. "
                        f"Voeg toe aan data/vocabulaire.yaml of gebruik een bestaande waarde."
                    )

    print(f"Gecontroleerd: {aantal} bronnen")

    if waarschuwingen:
        print(f"\n{len(waarschuwingen)} waarschuwing(en) - onvolledige bronnen:")
        for waarschuwing in waarschuwingen:
            print(f"  - {waarschuwing}")

    if fouten:
        print(f"\n{len(fouten)} fout(en) gevonden:\n", file=sys.stderr)
        for fout in fouten:
            print(f"  - {fout}", file=sys.stderr)
        return 1

    print("\nAlle bronnen voldoen aan het vocabulaire.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
