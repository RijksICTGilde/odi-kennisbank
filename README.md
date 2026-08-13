# ODI Start — proof of concept

Eén statische site die de eerste stap ('Phase 0') vormt richting één plek waar
ODI-medewerkers kennis over digitaliseringsvraagstukken vinden.

| Pagina | Wat het is |
| --- | --- |
| `/` | **ODI Start** — de startplek die verwijst naar bestaande bronnen, expertises en tools. |
| `/kennisbank/` | **Kennisbank** — 144 kaders, handreikingen, sjablonen en opleidingen, doorzoekbaar en te filteren op vijf facetten. |

De site staat in `sites/odi/`; de vormgeving in `gedeeld/` wordt daarin
gemount.

## Uitgangspunten

Conform het Phase 0-document:

- **Verwijzen, niet herbouwen.** Bestaande bronnen (Wies, ZAD) blijven waar ze
  zijn; ODI Start linkt ernaar.
- **De Kennisbank is de hoofdbron.** Daar staat de kennis zelf: 144 kaders,
  handreikingen, sjablonen en opleidingen, doorzoekbaar en te filteren op vijf
  facetten. Wies en Samenwerkruimten helpen je bij mensen en teams en zijn
  daarmee ondersteunend.
- **Eén expertise-indeling.** `sites/odi/data/expertises.yaml` bevat de
  expertisegebieden van het ODI; Wies gebruikt dezelfde termen, zodat je per
  gebied kennis én collega's vindt.
- **Hergebruik van bestaande opzetten.** De vormgeving komt uit het
  [NLDD design system](https://minbzk.github.io/storybook/); de
  componentpatronen (filter-sidebar, kaarten, lijstrijen) zijn overgenomen uit
  [Wies](https://github.com/RijksICTGilde/wies) (PR #427, "Feature/nldd design
  system"). De paginaopbouw volgt [moza-site](https://github.com/MinBZK/moza-site),
  de werkwijze (markdown in git, PR's, CI-controle op metadata)
  [Algoritmekader](https://github.com/MinBZK/Algoritmekader).
- **Beheer via Git.** Dat mag voorlopig wat technischer zijn.

## Aan de slag

```sh
brew install hugo just

just up      # ontwikkelserver -> http://localhost:1313
just build   # bouw naar public/
just check   # valideer de frontmatter van de bronnen
```

## Structuur

| Pad | Inhoud |
| --- | --- |
| `gedeeld/static/vendor/nldd/` | Het NLDD design system, gevendord uit npm (zie VERSION.txt) |
| `gedeeld/assets/` | Eigen CSS en JavaScript — alleen de ruimte tússen componenten |
| `gedeeld/layouts/` | Header, footer, head en basissjabloon |
| `sites/odi/data/expertises.yaml` | De expertise-indeling, gelijk aan Wies |
| `sites/odi/data/bronnen.yaml` | Kennisbronnen en tools waar Start naar verwijst |
| `sites/odi/content/kennisbank/` | Eén markdown-bestand per bron |
| `sites/odi/data/vocabulaire.yaml` | Toegestane facetwaarden — de bron van waarheid |
| `sites/odi/data/synoniemen.yaml` | Afwijkende schrijfwijzen uit de export |
| `scripts/` | Import vanuit SharePoint en validatie |

Een bestand in `sites/odi/` gaat vóór op de gedeelde laag: zet een `layouts/`
met dezelfde naam daar neer om iets te overschrijven.

## De kennisbank: facetten

Een bron wordt op vijf assen geclassificeerd. `expertises` is de bovenste as
en gebruikt dezelfde indeling als Wies, zodat de kennisbank kan groeien voorbij
programma- en projectmanagement. Daaronder liggen `soorten`, `doelgroepen`,
`fases` en `themas` uit de SharePoint-bron. Elk facet is een Hugo-taxonomie,
dus `/themas/governance/` bestaat automatisch. Op `/bronnen/` kun je ze
combineren; de filters staan in de URL, zodat een selectie deelbaar is.

Let op: Hugo koppelt frontmatter aan een taxonomie op de **meervoudsnaam**.
`soorten:` werkt, `soort:` laat de taxonomie leeg.

## Zoeken

De Kennisbank heeft een client-side zoekfunctie (Fuse.js) over titel en
inhoud van alle bronnen. De index staat als `/index.json` in de build en wordt
pas opgehaald bij het openen van het zoekvenster. Openen kan met de knop in de
navigatie of met de sneltoets `/`.

ODI Start heeft geen zoekindex — die site verwijst alleen door — en zet
daarom `zoeken: false` in `hugo.yaml`.

## Een bron toevoegen

```sh
cd sites/odi
hugo new content/bronnen/mijn-bron.md
```

Vul de frontmatter en open een pull request. De controle in CI weigert waarden
die niet in `data/vocabulaire.yaml` staan — dat voorkomt dat er weer varianten
als `MSP` naast `Managing Successful Programmes (MSP)` ontstaan.

## De data opnieuw importeren

```sh
./scripts/import_sharepoint.py ~/Map1.csv --dry-run   # eerst kijken
./scripts/import_sharepoint.py ~/Map1.csv             # dan schrijven
```

Idempotent: het herschrijft `sites/odi/content/kennisbank/` volledig.
Waarden die het niet kan mappen worden niet geraden maar gerapporteerd.

## Testdata

Dit is een openbare testomgeving. De inhoud is daarom bewerkt:

- **Titels en organisatienamen zijn herschreven** zodat ze niet een-op-een
  matchen met de echte documenten. Titels die door de woordvervangingen niet
  veranderden, kregen het achtervoegsel "(voorbeeld)".
- **Persoonsnamen zijn verwijderd.** Twee bronnen noemden een auteur; die
  staan er nu zonder naam.
- **Eén bron is weggelaten** omdat die in de bron als intern was gemarkeerd.

De vervangingen staan in `sites/odi/data/anonimisering.yaml`, dat
bewust niet in de repository staat. Zet `DEMO_MODUS` in
`scripts/import_sharepoint.py` op `False` en draai de import opnieuw zodra de
omgeving intern is; dan komen de originele namen terug.

## Status van de gegevens

De 143 bronnen komen uit een SharePoint-export. Daarbij is geconstateerd:

- **Er zitten geen URL's in de export.** Excel heeft de hyperlinks
  platgeslagen tot alleen hun weergavetekst. Alle bronnen hebben daarom een
  placeholder en de vlag `url_ontbreekt`. Een nieuwe export mét adressen lost
  dit in één keer op.
- **De kolom `Review vanaf` is onbetrouwbaar.** Bij 76 van de 116 gevulde
  rijen is die datum gelijk aan `Gewijzigd`, wat erop wijst dat het veld
  meeschrijft bij bewerken in plaats van bewust gepland te zijn. De datum wordt
  daarom alleen feitelijk getoond ("Nagekeken tot").
- **41 bronnen hebben geen thema** en 51 geen toelichting.
- De export is **Mac Roman** gecodeerd, niet UTF-8 of cp1252.
- Eén titel komt twee keer voor (*Problematische legacy*) met verschillende
  fasen en thema's. Die records zijn niet samengevoegd — dat is een
  inhoudelijke keuze.

Ook op ODI Start staan bronnen zonder link (Samenwerkruimten, Templates &
Formats, ODI Links). Die tonen zichtbaar "nog geen link" in plaats van een
doodlopende verwijzing.

## Licentie

Zie [LICENSE](LICENSE), overgenomen uit moza-site (EUPL 1.2).
