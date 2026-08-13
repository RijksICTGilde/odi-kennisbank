---
title: Bijdragen
# Deze pagina staat in de kennisbank-sectie maar is zelf geen bron.
bron: false
---

Een bron toevoegen of corrigeren kan volledig via de webinterface van GitHub —
je hoeft niets te installeren.

## Wat je nodig hebt

1. **Een GitHub-account.** Nog geen account?
   [Maak er een aan](https://github.com/signup); dat kan met je werkmail.
2. **Toegang tot de repository.** Vraag schrijfrechten aan bij het team, of
   werk via een fork (zie hieronder). Zonder rechten kun je wel meelezen en
   een issue openen, maar geen bestand aanmaken.

Weet je niet of je rechten hebt? Klik op de knop hieronder. Kom je in een
editor, dan zit je goed. Ziet GitHub je als bezoeker, dan biedt het aan om een
fork te maken — dat is de tweede route en werkt net zo goed: je wijziging komt
dan vanuit je eigen kopie als pull request binnen.

Liever niet zelf sleutelen? Open dan een
[issue](https://github.com/RijksICTGilde/odi-kennisbank/issues/new) met de
bron die je mist; iemand van het team voegt hem toe.

## Een bron toevoegen

Gebruik de knop onder aan deze pagina. Die opent een nieuw bestand op de juiste plek, met het sjabloon er al in.
Je hoeft dus niets te kopiëren. Verder:

1. Pas de bestandsnaam bovenaan aan, bijvoorbeeld `wegwijzer-cloudinkoop.md`.
   Kleine letters en streepjes.
2. Vul het sjabloon in. Alles tussen de streepjes is metadata; daaronder komt
   de toelichting.
3. Onderaan: **Commit changes**, kies *Create a new branch and start a pull
   request*, en klik op **Propose changes**.

## Een bestaande bron wijzigen

Open de bron, klik onderaan op **Bewerk deze pagina op GitHub** en daarna op
het potloodje. Verder gaat het net als hierboven.

## Wat de controle bewaakt

Een GitHub Action controleert bij elke pull request of de metadata klopt:
`title` is ingevuld, en `expertises`, `soorten`, `doelgroepen`, `fases` en
`themas` bevatten alleen waarden uit
[`vocabulaire.yaml`](https://github.com/RijksICTGilde/odi-kennisbank/blob/main/sites/odi/data/vocabulaire.yaml).
Gebruik de sleutel links van de dubbele punt, dus `handreiking` en niet
`Handreiking`.

Klopt er iets niet, dan faalt de controle binnen een minuut met een melding
over welk veld het gaat. Zo blijft de facettering bruikbaar: één tikfout in een
thema maakt een bron anders onvindbaar.

## Een nieuw thema of expertise

Staat een waarde er nog niet bij, voeg hem dan in dezelfde pull request toe aan
[`vocabulaire.yaml`](https://github.com/RijksICTGilde/odi-kennisbank/edit/main/sites/odi/data/vocabulaire.yaml).
Kies liever een bestaande waarde als die de lading dekt — hoe minder
bijna-identieke thema's, hoe bruikbaarder de filters.
