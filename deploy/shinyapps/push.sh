#!/usr/bin/env bash
#
# Déploie l'app Shiny pension sur shinyapps.io (compte déjà autorisé via
# `rsconnect add`). L'app calcule OpenFisca en direct (OPENFISCA_MODE=local) :
# pas d'API HTTP séparée, pas de HF Space.
#
# Prérequis (une seule fois) :
#   1. rsconnect-python installé (groupe dev du projet : `uv sync --group dev`)
#   2. Autoriser le compte (contient TON secret, à lancer toi-même ;
#      depuis Account → Tokens sur shinyapps.io) :
#        rsconnect add --account <compte> --name <compte> --token <TOKEN> --secret <SECRET>
#
# Usage :
#   deploy/shinyapps/push.sh <compte> [nom-app]
#   ex : deploy/shinyapps/push.sh benjello simulateur-pension-tunisie
#
set -euo pipefail

COMPTE="${1:?Usage: push.sh <compte> [nom-app]}"
APPNAME="${2:-simulateur-pension-tunisie}"

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
BUNDLE="$(mktemp -d)"

echo "Assemblage du bundle dans $BUNDLE"

# Point d'entrée shinyapps (force le mode local) -> app.py.
cp "$ROOT/deploy/shinyapps/app.py" "$BUNDLE/app.py"
# Vrai code de l'app : app/app.py -> app_main.py (importé par app.py).
cp "$ROOT/app/app.py" "$BUNDLE/app_main.py"
# Module client (API/local).
cp "$ROOT/app/openfisca_client.py" "$BUNDLE/openfisca_client.py"
# Dépendances pip.
cp "$ROOT/deploy/shinyapps/requirements.txt" "$BUNDLE/requirements.txt"
# Cible Python.
echo "3.12" > "$BUNDLE/.python-version"

echo "Contenu du bundle :"
ls -1 "$BUNDLE"

# rsconnect depuis le venv du projet (uv).
"$ROOT/.venv/bin/rsconnect" deploy shiny "$BUNDLE" \
  --name "$COMPTE" \
  --title "$APPNAME" \
  --entrypoint app:app

echo "Déploiement lancé. Suivez l'URL affichée ci-dessus."
rm -rf "$BUNDLE"
