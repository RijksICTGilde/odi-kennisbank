# Bijdragen

Een bron toevoegen of wijzigen kan volledig via de webinterface van GitHub —
je hoeft niets te installeren.

> **Let op:** dit is een testomgeving. De titels en organisatienamen in de
> huidige bronnen zijn bewust aangepast, zodat ze niet een-op-een matchen met
> de echte documenten. Bij de overgang naar een interne omgeving worden ze
> vervangen door de originelen.

## Een bron toevoegen via GitHub

1. Ga naar [`sites/odi/content/kennisbank/`](../../tree/main/sites/odi/content/kennisbank).
2. Klik op **Add file → Create new file**.
3. Geef het bestand een naam die eindigt op `.md`, bijvoorbeeld
   `handreiking-cloudinkoop.md`. Gebruik kleine letters en streepjes.
4. Plak het sjabloon hieronder en pas het aan.
5. Onderaan: **Commit changes**, kies *Create a new branch and start a pull
   request*, en klik op **Propose changes**.

De controle draait automatisch op je pull request. Klopt er iets niet aan de
metadata, dan zie je binnen een minuut welk veld het betreft.

## Sjabloon

```markdown
---
title: Handreiking cloudinkoop
eigenaar: Bureau Informatiebeleid
description: Eén of twee zinnen over wat dit is en voor wie het nuttig is.
expertises:
  - cloud-en-platform-technologie
soorten:
  - handreiking
doelgroepen:
  - projectmanager
  - opdrachtgever
themas:
  - inkoop
  - cloud
bron_url: https://example.org/de-echte-link
---

De volledige toelichting. Eén of twee alinea's is genoeg; dit is een
verwijzing naar de bron, niet de bron zelf.
```

### Welke velden zijn verplicht?

| Veld | Verplicht | Toelichting |
| --- | --- | --- |
| `title` | ja | De titel zoals die op de kaart komt |
| `soorten` | aanbevolen | Ontbreekt hij, dan krijg je een waarschuwing |
| `eigenaar` | aanbevolen | De organisatie die de bron publiceert |
| `expertises` | nee | Standaard leeg; vul in als je het weet |
| `doelgroepen`, `fases`, `themas` | nee | Hoe meer je invult, hoe beter vindbaar |
| `bron_url` | nee | Laat weg als de link nog niet bekend is |

### Toegestane waarden

`expertises`, `soorten`, `doelgroepen`, `fases` en `themas` mogen alleen
waarden bevatten die in
[`sites/odi/data/vocabulaire.yaml`](../../blob/main/sites/odi/data/vocabulaire.yaml)
staan. Gebruik de sleutel (links van de dubbele punt), dus `handreiking` en
niet `Handreiking`.

Die controle is er met een reden: in de oorspronkelijke SharePoint-export
stonden `MSP` en `Managing Successful Programmes (MSP)` naast elkaar, en
`Kwaliteitsmanagament` naast `Kwaliteitsmanagement`. Zulke varianten splitsen
een filter in tweeën, waardoor bronnen onvindbaar worden.

## Een nieuw thema of expertise

Staat een waarde er nog niet bij, voeg hem dan in dezelfde pull request toe aan
`vocabulaire.yaml`. Kies liever een bestaande waarde als die de lading dekt:
hoe minder bijna-identieke thema's, hoe bruikbaarder de filters.

## Een bestaande bron wijzigen

Open het bestand in GitHub en klik op het potloodje. Verder gaat het net als
hierboven: commit naar een nieuwe branch en open een pull request.

## Wat er met je pull request gebeurt

1. De metadata wordt automatisch gecontroleerd.
2. Iemand kijkt inhoudelijk mee.
3. Na het samenvoegen staat de wijziging binnen een paar minuten live.
