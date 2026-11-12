# Registre des désaccords et décisions — pension

Format par entrée : **constat** (ce que fait un simulateur ou le modèle) →
**droit** (ce que dit le texte) → **décision** (règle retenue + cas de test calé
dessus). Le droit fait référence ; les simulateurs sont des indices.

Sources primaires vérifiées (recherche juridique 2026-11-12) :
- Décret n° 74-499 (CNSS/RSNA), art. 14-19, mod. décret n° 94-1429 (30/06/1994),
  décret n° 82-1030, décret n° 2007-2148 —
  <https://www.jurisitetunisie.com/tunisie/codes/vieillesse/1974-0499_1010.htm>
- Loi n° 85-12 du 5 mars 1985 (CNRPS, pensions civiles et militaires), art. 22,
  36, 38, 39 —
  <https://legislation-securite.tn/latest-laws/loi-n-85-12-du-5-mars-1985-portant-regime-des-pensions-civiles-et-militaires-de-retraite-et-des-survivants-dans-le-secteur-public/>
- Décret présidentiel n° 2022-542 du 13 juin 2022 (départ anticipé 57 ans) —
  <https://legislation-securite.tn/latest-laws/decret-presidentiel-n-2022-542-du-13-juin-2022-fixant-les-categories-concernees-les-procedures-les-modalites-et-les-delais-dapplication-du-programme-specifique-pour-la-mise-a-la-retr/>

## Décisions tranchées

### D-1 — Salaire de référence CNSS/RSNA = 10 dernières années (pas « meilleures »)

- **Constat** : secu.tn/22.tn prennent la moyenne des 10 dernières années
  actualisées, plafonnée à 6×SMIG ; retraite.tn parle de « meilleures années ».
- **Droit** : décret n° 74-499, art. 18 (nouveau) mod. décret n° 94-1429
  (30/06/1994) : montée en charge 5 ans (1/7/1994) → 7 ans (1/7/1995) →
  **10 ans à partir du 1/7/1996** ; art. 19 : moyenne = 1/120ᵉ des 120 derniers
  mois pris dans l'ordre **chronologique**, chaque salaire **actualisé par un
  barème fixé annuellement par arrêté** du ministre des affaires sociales ;
  plafond **6× le SMIG** (régime 48 h rapporté à 2400 h/an).
- **Décision** : retenir les **10 dernières années chronologiques** actualisées,
  plafond 6×SMIG. La lecture « meilleures années » est **rejetée** (non conforme).
  → Cohérent avec `rsna_salaire_de_reference` du modèle (test `rsna.yaml` : salaire
  constant 24000 → SR 31205,568, soit la moyenne actualisée des 10 dernières
  années).

### D-2 — Barème d'annuités CNSS : palier 40 % aux 10 ans, +0,5 %/trimestre, plafond 80 %

- **Constat** : certains simulateurs appliquent 2 %/an linéaire dès la 1ʳᵉ année
  (omission du palier).
- **Droit** : décret n° 74-499, art. 17 (nouveau) mod. décret n° 82-1030 puis
  décret n° 2007-2148 : **40 %** du salaire moyen de référence une fois réalisée
  la condition de **120 mois**, puis **+0,5 % par période de 3 mois** (2 %/an)
  au-delà, **plafond 80 %** ; stage minimum **120 mois = 10 ans** (art. 15).
- **Décision** : palier 40 % à 10 ans + 0,5 %/trimestre, plafond 80 %, minimum
  10 ans. Les simulateurs « 2 %/an linéaire » sont **non conformes**.
  → Confirmé par le modèle : `rsna_taux_de_liquidation` donne 0,40 à 40 trim,
  0,46 à 52 trim, 0,80 au plafond (tests `rsna.yaml`).

### D-3 — CNRPS : dernier salaire (retenues ≥ 3 ans), barème 2/3/2 %, plafond 90 %, min 15 ans

- **Constat** : simulateurs prennent « le dernier salaire » ; clause d'ancienneté ?
- **Droit** : loi n° 85-12 — art. 36 : liquidation sur **la dernière rémunération**
  ayant subi des retenues **pendant ≥ 3 ans** ; art. 38 : **2 %/an (10 premières),
  3 %/an (10 suivantes), 2 %/an au-delà**, plafond **90 %** ; art. 22 : minimum
  **15 ans** (10 ans pour ouvriers occasionnels) ; art. 39 : plancher **2/3 SMIG**
  (2400 h/an).
- **Décision** : tous les paramètres confirmés par le texte.
  → Confirmé par le modèle : `cnrps_taux_de_liquidation` 0,20 (40 trim) / 0,52
  (84 trim) / 0,90 (plafond) ; pension nulle à 10 ans, non nulle à 15 ans
  (tests `cnrps.yaml`).

### D-4 — Réformes récentes

- **(a) SMIG 2025** : SMIG régime 48 h = **528,320 DT/mois** au 1/1/2025
  (régime 40 h : 448,238 DT). Impacte le plancher CNSS (2/3 SMIG) et le plafond
  salaire (6×SMIG). *À vérifier : une seconde revalorisation mi-2025.*
- **(b) Départ anticipé 57 ans CNRPS** : décret présidentiel n° 2022-542 du
  13/06/2022 (JORT n° 68), pour l'art. 14 du décret-loi n° 2021-21 (LF 2022) :
  agents ≥ 57 ans **entre le 1/1/2022 et le 31/12/2024**, ≥ 15 ans de service,
  bonification = années restant jusqu'à 62 ans. **La fenêtre est 2022-2024**
  (« 2022-2028 » du relais = non sourcé). Une prolongation jusqu'à fin 2027
  figurerait au **PLF 2025** (à confirmer au texte promulgué).

## Questions ouvertes résiduelles (reports)

- **R-1** : table numérique des coefficients d'actualisation RSNA — publiée par
  arrêté annuel, non récupérée en source primaire. Le modèle openfisca en porte
  une version (à confronter au JORT si besoin de précision).
- **R-2** : base primaire du **minimum CNSS = 2/3 SMIG** non localisée dans le
  décret 74-499 (art. 39 de la loi 85-12 l'établit pour la CNRPS). À sourcer.
- **R-3** : seconde tranche SMIG 2025 (mi-année) à vérifier.
- **R-4** : extension du régime 57 ans jusqu'à 2027 — confirmer au JORT (LF 2025).
- **R-5** : le modèle expose un **plancher** (`*_pension_minimale` ≈ 2751,11 DT/an
  en 2020) ; sa correspondance exacte avec 2/3 SMIG de l'année reste à vérifier.
- **R-6 — écart modèle/loi sur l'ouverture du droit RSNA (inégalité stricte)** :
  `rsna_eligible` teste `duree_assurance > 4 × stage_requis` (strict), avec
  `stage_requis = 10 ans = 40 trimestres`. Conséquence : **10 ans pile (120 mois,
  40 trimestres) ne donne aucune pension** ; il faut 10 ans + 1 trimestre
  (41 trim → 12 638 DT/an en 2020). Or le décret 74-499 art. 15 b) exige
  « 120 mois de cotisations », donc les 120 mois **exacts** devraient ouvrir le
  droit (`≥`, pas `>`). À corriger dans openfisca-tunisia
  (`openfisca_tunisia_pension/variables/rsna.py`, condition `duree_stage_accomplie`).
  L'éligibilité exige aussi `age ≥ age_legal` (60 RSNA / 62 CNRPS) : un âge
  inférieur met aussi la pension à 0. Pour la CNRPS, le minimum **15 ans**
  (loi 85-12 art. 22) rend 0 à 10 ans conforme.
