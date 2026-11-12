# Tests de validation — pension

Tests YAML au format OpenFisca, exécutables avec le package **pension**
`openfisca_tunisia_pension` (distinct d'`openfisca_tunisia`, celui de la paie).

## Lancer les tests

Depuis un environnement où `openfisca-tunisia[pension]` est installé (numba
requis) :

```bash
openfisca test tests/pension/ -c openfisca_tunisia_pension
```

## Organisation

- `pension/rsna.yaml`  — pension RSNA (privé CNSS) : taux de liquidation et
  pension brute selon durée d'assurance et salaire de référence.
- `pension/cnrps.yaml` — pension CNRPS (public) : taux de liquidation et
  éligibilité (minimum d'années).
- `pension/rsa.yaml`   — pension RSA (agricole), si couvert par le modèle.

Les valeurs attendues sont celles du **moteur OpenFisca-Tunisia** (package
pension), vérifiées par le calcul. Les cas sont comparés — hors dépôt — à des
simulateurs de pension en ligne (correspondance dans `sources_locales/`, non
publiée). Les décisions tranchant les divergences sont dans
[`../docs/notes/desaccords.md`](../docs/notes/desaccords.md).

## Entrées typiques d'un cas pension

Variables préfixées par régime (`rsna_*`, `cnrps_*`, `rsa_*`) :

- `*_salaire_de_base` (mensuel), `*_duree_assurance` (trimestres), `age`,
  `*_liquidation_date`, `regime_securite_sociale`.
- Sorties : `*_salaire_de_reference`, `*_taux_de_liquidation`, `*_pension_brute`,
  `*_pension`, `*_pension_servie`.
