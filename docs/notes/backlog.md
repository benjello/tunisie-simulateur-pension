# Backlog durable — simulateur de pension

Reports et pistes à suivre, versés ici pour ne pas vivre uniquement dans une
conversation. Origine : relais de la session « fiche de paie »
(`docs/notes/relais-pension.md`).

## État du chantier

**Fait** :
- Dépôt scaffolé sur le modèle de `tunisie-simulateur-paie` (structure,
  `.gitignore`, `AGENTS.md`, agents portables `.pi/.claude/.opencode`,
  `pyproject.toml` uv, `docs/notes/`, `sources_locales/`).
- Agents `analyste-openfisca` (Haiku, lecture seule) et `juriste-fiscal-tn`
  (Sonnet, web) adaptés au package pension.

- **Modèle vérifié par le calcul** (2026-11-12, venv openfisca-tunisia) : chaîne
  `taux_de_liquidation → pension_brute → pension` confirmée pour RSNA et CNRPS.
- **Tests YAML écrits et validés** : `tests/pension/{rsna,cnrps}.yaml`,
  **19/19 passés** avec `openfisca test tests/pension -c openfisca_tunisia_pension`.
- **App Shiny écrite et testée end-to-end** contre l'API réelle depuis l'env du
  dépôt (`uv run openfisca serve -c openfisca_tunisia_pension`) : RSNA 40 ans →
  24964,455 ; CNRPS 30 ans (sal. 2000/mois) → 16800 ; CNRPS 10 ans → 0.
  `app.py` se charge sous Shiny, `api_disponible()` = True.
- **Env uv installé** (`uv sync`) : shiny 1.9, httpx, openfisca_tunisia_pension,
  numba 0.68.1. `uv.lock` généré.
- **Décisions juridiques tranchées** (D-1..D-4 dans `desaccords.md`, sources
  primaires décret 74-499 et loi 85-12) : salaire réf RSNA = 10 dernières années
  (pas « meilleures ») ; palier 40 %/10 ans confirmé ; CNRPS dernier salaire +
  clause 3 ans, barme 2/3/2 %, min 15 ans ; fenêtre 57 ans = 2022-2024.
- **`git init` fait + 19 fichiers stagés** (`sources_locales/` ignoré). Commit
  en attente (lancer `/commit`).
- **Test du plancher** (pension minimale CNRPS ≈ 2751,11 DT/an 2020) ajouté →
  **20/20 tests passés**.

**À faire (reste)** :
- **Committer** (`/commit`) puis créer le repo public GitHub
  `benjello/tunisie-simulateur-pension` et pousser.
- Confronter les cas aux simulateurs en ligne (`sources_locales/`) et relier
  chaque test à sa source.
- Reports juridiques résiduels R-1..R-5 (`desaccords.md`) : coefficients
  d'actualisation RSNA, base du minimum CNSS 2/3 SMIG, 2e tranche SMIG 2025,
  extension 57 ans à 2027, correspondance plancher modèle ↔ 2/3 SMIG.
- **Lacunes modèle** (dans openfisca-tunisia, autre dépôt) : RSA non paramétré,
  `pension_servie` cassée — à corriger là-bas, pas ici.

## Modèle openfisca pension (hérité du relais, à vérifier)

- Package séparé `openfisca_tunisia_pension/` avec son propre
  `TunisiaPensionTaxBenefitSystem` (devise « DT »). Exige `numba`
  (`pip install 'openfisca-tunisia[pension]'`).
- Classes `regimes/*.py` → variables préfixées (`rsna_*`, `cnrps_*`, `rsa_*`)
  par AST (`scripts_ast/script_ast.py`). Paramètres dans
  `openfisca_tunisia/parameters/retraite/` (+ `marche_travail`).
- Chaîne (`regimes/regime.py`, `AbstractRegimeEnAnnuites`) : entrées
  `*_salaire_de_base` (MONTH), `*_duree_assurance` (trimestres), `age`,
  `*_liquidation_date`, `regime_securite_sociale` → `*_salaire_de_reference` →
  `*_taux_de_liquidation` (= `bareme_annuite.calc`) → `*_pension_brute`
  (= taux × salaire réf) → `*_pension` (= éligible × borne min/max) →
  `*_pension_servie` (revalorisée depuis la liquidation).
- Régimes avec classe réelle : **RSNA, CNRPS, RSA**. Autres (rsaa, rtns, rtte,
  raci, re, rtfr, pensionne_cnrps) = paramètres mais pas de classe → lacune.
- API : `openfisca serve --country-package openfisca_tunisia_pension`.

### Cas chiffrés openfisca (oracles de test, hérités — à reconfirmer par calcul)

- `tests_pension/formulas/rsna/pension.yaml` : 12000 DT/an, 50 trimestres,
  2011 → taux 45 %, `rsna_pension` = 6416,94 DT (sal_ref 14259,86).
- `tests_pension/formulas/cnrps/taux_de_liquidation.yaml` : 20 trim → 0,10 ;
  40 trim → 0,20 ; 84 trim → 0,52.
- `tests_pension/formulas/cnrps/pension.yaml` : 3 ans → 0 (inéligible) ;
  7 ans → 0,5 × 235,04 × 12 ; 17 ans → 0,66666 × 235,04 × 12.

### Reports / lacunes modèle (CONFIRMÉS par le calcul 2026-11-12)

- **RSA non exploitable aux années récentes** : `retraite.rsa.bareme_annuite`
  introuvable à 2020 (`ParameterNotFoundError`) → RSA **exclu de l'app et des
  tests**. À reparamétrer dans `openfisca_tunisia/parameters/retraite/rsa/`.
- **`pension_servie` cassée** : dépend de `*_pension_au_31_decembre`, absente du
  système chargé (`VariableNotFound`). Donc impossible d'exposer la pension
  revalorisée post-liquidation. Utiliser `*_pension` (pension de l'année de
  liquidation). À corriger dans le modèle.
- **`pension_maximale` = +inf** en 2020 : le plafond (80 % RSNA / 90 % CNRPS) est
  porté par le **taux**, pas par un plafond de pension. OK, mais à garder en tête.
- **Plancher (pension_minimale)** : ~2751,11 DT/an en 2020 ; domine quand le
  salaire de référence est faible (c'est pourquoi les tests "formule" utilisent
  un SR élevé). Un test dédié au plancher reste à écrire.
- Régimes rsaa, rtns, rtte, re, rtfr, raci, pensionne_cnrps non modélisés.
- `salaire_de_reference` RSNA 1990-09-23→1994-06-30 : `NotImplementedError`
  volontaire (texte non tranché).
- `duree_assurance` de base : pas de formule active (entrée directe).
- numba 0.67.0 installé dans le venv openfisca-tunisia (import OK).

## Simulateurs en ligne (recensement hérité)

- **secu.tn** (CNSS/CNRPS/complémentaire CAVIS — le plus détaillé), **22.tn**
  (CNSS+CNRPS, cas chiffrés), **retraite.tn**, **ihsibly.com** (React, non
  extractibles en statique). CNSS/CNRPS officiels : pas de simulateur public.
  Noms à garder dans `sources_locales/` (gitignoré).

### Méthode des simulateurs (à confronter à la loi)

- **Privé CNSS/RSNA** : salaire de référence = moyenne des 10 dernières années
  actualisées, plafonnée à 6×SMIG. Taux 40 % (10 premières années) puis +2 %/an
  (0,5 %/trimestre), plafond 80 %. Min 10 ans. Âge 60 (55 pénibles). Minoration
  départ anticipé −0,5 %/trimestre. Mini 2/3 SMIG.
- **Public CNRPS** : salaire réf = dernier salaire (≥3 ans), sans plafond. Taux
  2 %/an (10 premières), 3 %/an (10 suivantes), 2 %/an au-delà, plafond 90 %.
  Min 15 ans. Âge 62.

### Cas chiffrés de référence (anonymiser la source)

- CNSS 25 ans, moyenne 1305 D → 70 % → brut 913,5 D.
- CNSS 25 ans, moyenne 4480 D plafonnée 2760 D → 70 % → brut 1932 D.
- CNSS dernier salaire 2000 D, 25 ans → 70 % → brut 1400 D.
- CNRPS dernier salaire 2000 D, 30 ans → 70 % → brut 1400 D.
- Taux : CNSS 19 ans = 58 %, 41,25 ans = 80 % ; CNRPS 19 ans = 47 %,
  41,25 ans = 90 %.

## Questions ouvertes (accumulées, à trancher par la loi)

1. Salaire de référence CNSS : « 10 dernières années » (secu.tn/22.tn) vs
   « meilleures années » (retraite.tn) — trancher par décret 74-499.
2. retraite.tn omet le palier 40 %/10 ans CNSS — simplification probablement
   fausse ?
3. CNRPS : « dernier salaire » vs clause des 3 ans — préciser.
4. Réformes récentes (SMIG 2025, régime exceptionnel CNRPS 57 ans 2022-2028) :
   intégrées au modèle openfisca ?
5. Coefficients d'actualisation CNSS et barème exact : non collectés (page
   secu.tn dédiée à exploiter, ou simulateurs React via navigateur).

## Architecture / déploiement (hérité de la paie)

- **API OpenFisca en local uniquement** pour l'instant (`-p 5001` suggéré pour
  la pension, afin de cohabiter avec la paie sur 5000).
- **GitHub Pages / WebAssembly écarté** : pendulum/numexpr/psutil absents de
  Pyodide. Mode client/serveur.
- **Piste MCP** : exposer openfisca via un serveur MCP à terme.
