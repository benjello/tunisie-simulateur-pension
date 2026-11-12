# Application — pension de retraite (local)

Interface [Shiny for Python](https://shiny.posit.co/py/) pour le simulateur de
pension. **Tout le calcul est fait par OpenFisca-Tunisia** (package pension
`openfisca_tunisia_pension`), via son API web : l'app construit la carrière d'un
assuré, la poste à l'API, et affiche la pension.

## Lancer en local

Deux processus. Dans un premier terminal, l'API OpenFisca pension (port 5001
pour cohabiter avec l'API paie sur 5000) :

```bash
uv run openfisca serve -c openfisca_tunisia_pension -p 5001
```

Dans un second, l'app Shiny :

```bash
uv run shiny run app/app.py --port 8101
```

Puis ouvrir http://localhost:8101.

Pour pointer vers une API hébergée ailleurs, définir `OPENFISCA_API_URL` :

```bash
OPENFISCA_API_URL=https://mon-api-pension.example uv run shiny run app/app.py
```

## Fichiers

- `openfisca_client.py` — construction de la carrière et appels `/calculate`
  (variables préfixées par régime : `rsna_*`, `cnrps_*`).
- `app.py` — interface Shiny (entrées : régime, année de liquidation, salaire,
  durée d'assurance, âge ; sorties : salaire de référence, taux de liquidation,
  pension brute et servie).

## Périmètre actuel

Régimes **RSNA** (privé CNSS) et **CNRPS** (public). Hypothèse : salaire
constant sur la carrière (suffisant pour la fenêtre de référence RSNA de 10 ans
et pour le dernier salaire CNRPS). Le régime **RSA** (agricole) n'est pas exposé :
son barème d'annuités n'est pas paramétré aux années récentes dans le modèle
(voir `docs/notes/backlog.md`). `pension_servie` (revalorisation post-liquidation)
n'est pas exposée : la variable est cassée dans le modèle (dépend de
`*_pension_au_31_decembre`, absente).

## Déploiement

Comme la paie : déploiement statique GitHub Pages impossible (extensions
compilées absentes de Pyodide). Mode client/serveur ; étape suivante possible :
héberger l'API ou l'exposer via un serveur MCP. Voir `docs/notes/backlog.md`.
