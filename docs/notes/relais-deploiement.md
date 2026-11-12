# Relais — déploiement shinyapps.io + secrets (transmis par la session paie)

Le simulateur de paie est déployé sur shinyapps.io avec CI/CD GitHub. Cette
mécanique est transmise à **pension**, **impôt** et **amen-social**. Le kit a
déjà été **déposé dans chaque dépôt** (dossiers `scripts/`, `deploy/shinyapps/`,
`.github/workflows/`, plus `.env`/`.env.example`). Il reste à l'ADAPTER et le
committer côté chaque session.

## Ce qui a été déposé (non commité — à toi de committer)

- `scripts/set_shinyapps_secrets.sh` — pousse les 3 secrets vers un repo GitHub
  (générique, réutilisable tel quel).
- `deploy/shinyapps/` — `app.py` (force OPENFISCA_MODE=local), `push.sh`,
  `requirements.txt`, `README.md`.
- `.github/workflows/` — `ci.yml` (tests) et `deploy.yml` (déploiement auto).
- `.env` (gitignoré, chmod 600, squelette à remplir) + `.env.example` (versionné).
- Règle `.env` ajoutée au `.gitignore`.

## À ADAPTER avant de committer (important)

Le kit vient de l'app PAIE. Chaque simulateur a sa propre app, donc :

1. **`deploy/shinyapps/requirements.txt`** : mettre les dépendances de TON app
   (openfisca-tunisia et/ou openfisca_tunisia_pension selon le cas, shiny, et ce
   que ton app importe).
2. **`deploy/shinyapps/app.py` et `push.sh`** : vérifier les noms de modules
   copiés dans le bundle. Le kit suppose `app/app.py` + `app/openfisca_client.py`
   + `app/i18n.py`. Adapte la liste `cp ...` de `push.sh` à TES fichiers.
3. **`.github/workflows/deploy.yml`** : adapter le `--title` (nom du Space, ex.
   `simulateur-pension-tunisie`) et la liste des fichiers copiés dans le bundle.
4. **`.github/workflows/ci.yml`** : adapter les chemins de tests (`tests/...`).
5. **Pension uniquement** : l'app pension utilise le country-package
   `openfisca_tunisia_pension` et numba. Vérifie que `requirements.txt` inclut
   `openfisca-tunisia[pension]` et que le mode local charge le bon
   TaxBenefitSystem (voir `relais-pension.md`).

## Procédure de déploiement (une fois adapté)

1. Créer le repo GitHub s'il n'existe pas :
   `gh repo create benjello/<repo> --public`
2. Remplir `.env` (TOKEN/SECRET depuis shinyapps.io → Account → Tokens).
3. Autoriser rsconnect en local (une fois) :
   `source .env && .venv/bin/rsconnect add --account "$SHINYAPPS_ACCOUNT" --name "$SHINYAPPS_ACCOUNT" --token "$SHINYAPPS_TOKEN" --secret "$SHINYAPPS_SECRET"`
4. Premier déploiement manuel : `deploy/shinyapps/push.sh benjello <nom-app>`
5. Pousser les secrets GitHub pour le CD :
   `scripts/set_shinyapps_secrets.sh benjello/<repo>` (charge `.env` auto).
6. Committer le kit adapté → le CD prend le relais à chaque push.

## Sécurité (rappel)

- `.env` est **gitignoré** (vérifié) — ne jamais le committer.
- Le même token/secret shinyapps.io sert pour tous tes repos (compte unique
  `benjello`). Le script les propage ; GitHub les garde chiffrés.
- Si le token a fuité (capture d'écran, log), régénère-le sur shinyapps.io et
  mets à jour `.env` + les secrets GitHub de chaque repo.
