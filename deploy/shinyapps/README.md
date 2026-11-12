# Déploiement sur shinyapps.io

Hébergement de l'app Shiny pension (compte shinyapps.io ; plan gratuit = 25 h
actives/mois **partagées** avec les autres apps du compte, 1 Go RAM). L'app
calcule OpenFisca **en direct** dans le process (`OPENFISCA_MODE=local`) : pas
d'API HTTP séparée, pas de Hugging Face Space.

> ⚠️ **Attendre la release PyPI 0.164.** Le correctif d'éligibilité
> « 120 mois » (openfisca-tunisia PR #527) n'est actif qu'à partir de la version
> 0.164. Tant que PyPI est à 0.163, l'app déployée affichera 0 pour une carrière
> RSNA de 10 ans pile. Soit on attend 0.164, soit on bascule `requirements.txt`
> sur le fallback git (voir le commentaire dans le fichier).

## Prérequis (une seule fois)

1. **Compte** sur https://www.shinyapps.io.
2. **rsconnect-python** : `uv sync --group dev` (déjà dans le groupe dev).
3. **Autoriser le compte** — contient ton SECRET, à lancer dans TON terminal
   (depuis Account → Tokens sur shinyapps.io, bouton « Copy to clipboard »).
   Si le compte `benjello` est déjà enregistré (cas du simulateur de paie),
   **cette étape est déjà faite** :

   ```bash
   rsconnect add --account <compte> --name <compte> --token <TOKEN> --secret <SECRET>
   ```

## Déployer

```bash
deploy/shinyapps/push.sh <compte> [nom-app]
# ex :
deploy/shinyapps/push.sh benjello simulateur-pension-tunisie
```

Le script assemble un bundle propre (point d'entrée `app.py` qui force le mode
local + `app_main.py` + `openfisca_client.py` + `requirements.txt` + cible
Python 3.12) et lance `rsconnect deploy shiny`. L'URL publique s'affiche à la
fin. C'est une **application distincte** du simulateur de paie (même compte,
nom différent), avec sa propre URL.

## Note sur le démarrage à froid

`numba` compile les calculs des pensions au premier appel (JIT) : la toute
première requête après un réveil de l'app peut prendre quelques secondes.
