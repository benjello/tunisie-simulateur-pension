# AGENTS.md

Instructions et profils d'agents pour ce dépôt, lisibles par n'importe quel
opérateur d'agent (Claude Code, opencode, Cursor, pi…).

## Le projet

Simulateur de **pension de retraite** pour la Tunisie, construit sur le moteur
[OpenFisca-Tunisia](https://github.com/openfisca/openfisca-tunisia) — package
dédié `openfisca_tunisia_pension` — et une interface
[Shiny for Python](https://shiny.posit.co/py/). Régimes visés en premier :
**RSNA** (privé CNSS), **CNRPS** (public), **RSA** (agricole).

**L'application ne calcule rien elle-même** : elle poste la carrière d'un assuré
à l'API web d'OpenFisca-Tunisia (country-package des pensions) et affiche la
pension. OpenFisca est le moteur unique.

> ⚠️ Deux country-packages distincts : `openfisca_tunisia` (paie, autre dépôt)
> et `openfisca_tunisia_pension` (pensions, ce dépôt). Ne pas les confondre.
> Le package pension exige `numba` (`pip install 'openfisca-tunisia[pension]'`).

## Règles de travail

- **Le droit fait référence** (loi n° 85-12 CNRPS, loi n° 60-30 / décret
  n° 74-499 CNSS, lois de finances). Les simulateurs de pension en ligne sont des
  points de comparaison, pas la vérité.
- Chaque divergence est **identifiée, documentée et tranchée par le texte** dans
  `docs/notes/desaccords.md`. Un simulateur peut n'être exact que pour certaines
  années ou réformes : le cas de test est calé sur l'année/réforme valide.
- **Confidentialité des sources** : les noms des simulateurs testés ne figurent
  pas dans le dépôt public. La correspondance « cas ↔ source » est tenue dans
  `sources_locales/` (gitignoré).
- Les tests YAML (`tests/pension/`) sont exécutés par le moteur :
  `openfisca test tests/pension/ -c openfisca_tunisia_pension`.

## Modèle pension (mémo)

- Package séparé `openfisca_tunisia_pension/` avec son propre
  `TunisiaPensionTaxBenefitSystem` (devise « DT »).
- Les classes `regimes/*.py` sont transformées en variables préfixées
  (`rsna_*`, `cnrps_*`, `rsa_*`) par AST au chargement
  (`scripts_ast/script_ast.py`). Paramètres dans l'arbre commun
  `openfisca_tunisia/parameters/retraite/` (+ `marche_travail`).
- Chaîne (`regimes/regime.py`, `AbstractRegimeEnAnnuites`) : entrées
  `*_salaire_de_base` (mensuel), `*_duree_assurance` (trimestres), `age`,
  `*_liquidation_date`, `regime_securite_sociale` →
  `*_salaire_de_reference` → `*_taux_de_liquidation` → `*_pension_brute`
  (= taux × salaire réf) → `*_pension` (borné min/max si éligible) →
  `*_pension_servie` (revalorisée depuis la liquidation).
- Enum `TypesRegimeSecuriteSociale` dans `variables/data.py`.
- **Régimes avec classe régime réelle** : RSNA, CNRPS, RSA. Les autres (rsaa,
  rtns, rtte, raci, re, rtfr, pensionne_cnrps) ont des paramètres mais pas de
  classe → lacune (backlog).
- API : `openfisca serve --country-package openfisca_tunisia_pension`.

## Profils d'agents disponibles

Ces profils existent en versions natives dans `.pi/agents/`, `.claude/agents/`
et `.opencode/agent/`. Tout opérateur qui ne lit pas ces dossiers peut les
reproduire à partir des descriptions ci-dessous.

### `analyste-openfisca` — analyse du modèle (lecture seule, économe)

- **But** : répondre à des questions précises sur le code et les paramètres du
  package `openfisca_tunisia_pension` — variables préfixées par régime, barèmes
  d'annuités, enchaînement du calcul de pension.
- **Outils** : lecture seule (read, grep, find, ls, bash en lecture).
- **Modèle conseillé** : petit/rapide (p. ex. Haiku).
- **Exigence clé** : **vérifier les chiffres par le calcul** via le venv
  `openfisca-tunisia/.venv` (SimulationBuilder sur `TunisiaPensionTaxBenefitSystem`),
  et **sourcer** chaque valeur. Signaler les reports/lacunes.

### `juriste-fiscal-tn` — droit de la retraite tunisien

- **But** : établir ce que dit la loi (CNRPS loi 85-12, CNSS loi 60-30 / décret
  74-499, LF récentes) pour trancher les écarts de calcul de pension.
- **Outils** : lecture seule + recherche web (web_search, web_fetch).
- **Modèle conseillé** : intermédiaire (p. ex. Sonnet).
- **Exigence clé** : citer article + date d'effet ; distinguer salaire de
  référence (10 dernières années CNSS vs dernier salaire CNRPS), taux d'annuité
  et plafonds ; ne jamais inventer un chiffre ; fournir un bloc « à documenter
  dans desaccords.md » prêt à coller.
