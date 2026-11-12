# tunisie-simulateur-pension

Simulateur de **pension de retraite** pour la Tunisie, construit sur le moteur de
micro-simulation [OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia)
(package dédié `openfisca_tunisia_pension`), avec une interface
[Shiny for Python](https://shiny.posit.co/py/).

Régimes modélisés en premier : **RSNA** (privé, CNSS), **CNRPS** (public),
**RSA** (agricole). Les autres (RSAA, RTNS, RTTE, etc.) sont au backlog.

## Architecture

L'application **ne calcule rien elle-même** : elle envoie la carrière d'un
assuré à l'**API web d'OpenFisca-Tunisia** (country-package des pensions) et
affiche la pension renvoyée. OpenFisca reste le moteur unique.

```
Shiny (app/)  ──HTTP──▶  API openfisca_tunisia_pension  ──▶  moteur de calcul
```

En local, deux processus (voir [`app/README.md`](app/README.md)) :

```bash
uv run openfisca serve -c openfisca_tunisia_pension -p 5001   # l'API pension
uv run shiny run app/app.py --port 8101                       # l'app
```

> **Attention** : le simulateur de pension utilise le country-package
> `openfisca_tunisia_pension` (distinct d'`openfisca_tunisia`, celui de la paie),
> avec sa propre chaîne de variables préfixées par régime (`rsna_*`, `cnrps_*`,
> `rsa_*`). Il exige `numba` (extra `[pension]`).

## Chaîne de calcul (rappel)

Pour chaque régime (RSNA, CNRPS, RSA) :

```
*_salaire_de_base (mensuel)  +  *_duree_assurance (trimestres)  +  age  +  *_liquidation_date
      │
      ▼
*_salaire_de_reference  ──▶  *_taux_de_liquidation (barème d'annuités)
      │
      ▼
*_pension_brute = taux × salaire de référence
      │
      ▼
*_pension = éligible × borne(pension_minimale ≤ brute ≤ pension_maximale)
      │
      ▼
*_pension_servie (revalorisée depuis la date de liquidation)
```

## Principe de validation

Le **droit fait référence** (loi n° 85-12 pour la CNRPS, loi n° 60-30 et décret
n° 74-499 pour la CNSS, lois de finances récentes). Les simulateurs de pension en
ligne servent de **points de comparaison** : chaque cas chiffré devient un test
YAML OpenFisca.

Chaque divergence entre simulateurs — ou entre un simulateur et la loi — est
identifiée, documentée dans [`docs/notes/desaccords.md`](docs/notes/desaccords.md)
et tranchée par le texte légal.

> Les noms des simulateurs testés ne figurent pas dans le dépôt public. La
> correspondance « cas de test ↔ source » est tenue localement dans
> `sources_locales/` (dossier gitignoré).

## Structure

```
tests/pension/     Tests YAML OpenFisca (anonymisés, publics)
sources_locales/   Correspondance cas ↔ simulateur (GITIGNORÉ)
docs/notes/        Backlog, registre des désaccords, relais de passation
app/               Application Shiny
```
