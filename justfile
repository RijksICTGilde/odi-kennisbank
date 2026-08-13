[private]
default:
    @just --list

# Start de ontwikkelserver op http://localhost:1313
up:
    cd sites/odi && hugo server --baseURL http://localhost:1313/ --appendPort=false

# Bouw de site naar public/
build:
    rm -rf public && cd sites/odi && hugo --minify --destination ../../public

# Controleer de frontmatter van alle bronnen
check:
    ./scripts/valideer_bronnen.py

# Importeer de SharePoint-export opnieuw (pad naar de CSV meegeven)
import CSV:
    ./scripts/import_sharepoint.py {{CSV}}
