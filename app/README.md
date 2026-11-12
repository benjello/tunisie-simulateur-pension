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

- `openfisca_client.py` — construction de la carrière (salaire année par année,
  durée d'assurance, âge déduit de la date de naissance) et appels `/calculate`
  (variables préfixées par régime : `rsna_*`, `cnrps_*`) ; détails par période.
- `app.py` — interface Shiny à deux modes.

## Deux modes de saisie

- **Simplifié** : salaire mensuel constant + durée d'assurance (années).
- **Carrière détaillée** : grille **éditable** (salaire annuel et trimestres
  validés, année par année) ; la durée d'assurance est la somme des trimestres.

Dans les deux modes, l'**âge à la liquidation** est déduit de la **date de
naissance**. Un panneau « Détails par période » liste chaque variable pertinente
(`salaire_de_base` par année, puis `salaire_de_reference`, `taux_de_liquidation`,
`pension_brute`, `pension_minimale`, `pension`, `eligible` à la liquidation).

## Périmètre actuel

Régimes **RSNA** (privé CNSS) et **CNRPS** (public).

> **API avec le correctif d'éligibilité.** Le correctif « 120 mois ouvrent le
> droit » (RSNA/RSA, `>` → `>=`) vit dans la source locale d'openfisca-tunisia,
> pas encore dans le paquet PyPI. Pour que l'app en tienne compte, lancer l'API
> depuis le venv de la source corrigée :
> `…/openfisca-tunisia/.venv/bin/openfisca serve -c openfisca_tunisia_pension -p 5001`. Le régime **RSA** (agricole) n'est pas exposé :
son barème d'annuités n'est pas paramétré aux années récentes dans le modèle
(voir `docs/notes/backlog.md`). `pension_servie` (revalorisation post-liquidation)
n'est pas exposée : la variable est cassée dans le modèle (dépend de
`*_pension_au_31_decembre`, absente).

## Déploiement

Comme la paie : déploiement statique GitHub Pages impossible (extensions
compilées absentes de Pyodide). Mode client/serveur ; étape suivante possible :
héberger l'API ou l'exposer via un serveur MCP. Voir `docs/notes/backlog.md`.
