# Relais de session — 2026-11-13 (point d'arrêt)

> ⚠️ **GIT BLOQUÉ** pendant cette session : tout le travail ci-dessous vit
> **uniquement dans le working tree (sur disque), NON COMMITÉ**. Première action
> de la prochaine session : `/toggle-allow-git`, puis committer/pousser (le CD
> GitHub redéploie l'app).

## 0. LISTE EXACTE DES FICHIERS NON COMMITÉS (working tree)

```
 M app/app.py                      # net fiscal + refonte UX entonnoir
 M app/openfisca_client.py         # calculer_net_fiscal()
 M deploy/shinyapps/requirements.txt  # repin >=0.165 (fait)
 M docs/notes/backlog.md           # pointeur vers ce relais
 M pyproject.toml                  # openfisca-tunisia[pension]>=0.165 (fait)
 M uv.lock                         # 0.165
 ?? docs/notes/en-attente-2026-11-13.md   # ce relais
 ?? docs/notes/i18n-cablage.md            # déposé par session paie (bilingue)
 ?? docs/notes/i18n_base.py.txt           # idem
 ?? app/i18n.py                           # module traductions FR/AR (84 clés) — câblage à faire
```
Tout committer d'un coup après `/toggle-allow-git` (le CD redéploie). Suggestion :
un commit `NEW: net fiscal + refonte UX entonnoir + pin openfisca 0.165`.

## 1. À COMMITTER EN PRIORITÉ (déjà sur disque, testé)

### a) Net fiscal IRPP + CSS (fonctionnel, testé en local)
Fichiers modifiés **non commités** : `app/openfisca_client.py`, `app/app.py`.
- `calculer_net_fiscal(pension_annuelle_brute, annee)` dans le client : applique
  l'IRPP (abattement pension **25 %**, art. 26-II ; → 30/40/50 % en 2027-29) et la
  **CSS** via le package fiscal `openfisca_tunisia` **in-process** (TBS fiscal
  chargé paresseusement, indépendant d'OPENFISCA_MODE).
- Le résumé de l'app affiche : IRPP, CSS, **pension NETTE** (annuelle + mensuelle),
  **taux de remplacement NET**.
- Vérifié : pension 16 800/an → IRPP 1400, CSS 63, **net 15 337**.
- Message de commit suggéré : `NEW: net fiscal (IRPP + CSS) sur la pension + taux de remplacement net`.

### b) Repin dépendance — ✅ FAIT (sur disque, à committer)
`deploy/shinyapps/requirements.txt` → `openfisca-tunisia[pension]>=0.165` (git-ref
@master retiré). `pyproject.toml` → `>=0.165`. `uv sync` fait, **0.165 installé**.

## 2. Refonte UX « entonnoir » — ✅ FAIT (sur disque, à committer)

Appliqué dans `app/app.py` (bloc `ui.sidebar`) : essentiel visible (libellés en
questions : « Dans quel régime cotisez-vous ? », « Combien d'années avez-vous
cotisé ? »…), bouton Calculer juste après l'essentiel, puis **accordions repliés**
(`multiple=False` → un seul ouvert) : (1) Secteur public CNRPS
(`panel_conditional` regime==cnrps, sinon message), (2) Survivants, (3) Objectif
de pension. Import `app:app` vérifié OK. Reste possible : alléger le calcul au
chargement (la comparaison lance 9 simulations ; la déclencher au clic/ouverture).

### Plan initial (pour référence) :

- **Essentiel visible** (libellés en questions) : régime (« Dans quel régime
  cotisez-vous ? »), date de naissance, année de départ, et en mode simple
  salaire mensuel + années cotisées.
- **Accordéons repliés** (`ui.accordion(..., open=False, id=..., multiple=False)`
  pour n'en ouvrir qu'un à la fois), un panneau chacun :
  1. « Préciser ma carrière » (sélecteur mode simple/détaillé + grille).
  2. « Spécificités secteur public (CNRPS) » — `panel_conditional` regime==cnrps
     (bonifications, départ anticipé, coordination CNSS, famille) ; sinon message
     « ces options concernent la CNRPS ».
  3. « En cas de décès (survivants) » (conjoint survivant, orphelins).
  4. « Aller plus loin » (objectif inverse : pension mensuelle visée).
- **Garder les mêmes `id` d'inputs** (regime, naissance, annee_liq, mode,
  salaire_mensuel, duree, nb_annees, salaire_init, generer, cadre_actif,
  militaire, cnss_annees, mere3, astreignant, sur_demande, invalidite, nb_enfants,
  conjoint_sans_revenu, conjoint_survivant, nb_orphelins, pension_cible, calculer)
  pour ne pas toucher au `server`.
- Côté **main** : envisager d'afficher d'abord le résultat cœur, puis les cartes
  avancées (comparaison, survivants, objectif) en sections repliables, et ajouter
  des aides courtes / info-bulles. Réduire le calcul au chargement (la comparaison
  = 9 simulations ; envisager de ne la lancer qu'au clic / à l'ouverture).

## 3. DÉJÀ LIVRÉ ET DÉPLOYÉ (committé, poussé, en ligne)

App : **https://benjello.shinyapps.io/simulateur-pension-tunisie/** (app-id
shinyapps **18429443** ; CD GitHub à chaque push touchant `app/**` ou
`deploy/shinyapps/**`).

- **Vague 1 complète** : taux de remplacement, explication du taux + base légale,
  comparaison d'âges de départ (table + graphique matplotlib), bonifications CNRPS,
  départ anticipé CNRPS, coordination CNRPS+CNSS, indemnités familiales + IRU,
  détails par période enrichis.
- **Vague 2 (partielle)** : survivants (réversion conjoint + orphelins), objectif
  inverse (dichotomie), graphique. **+ net fiscal (point 1, à committer)**.

Plan complet et priorisé : `docs/notes/plan-ameliorations.md`.

## 4. RESTE À FAIRE

### Vague 2 (reste)
- **Scénarios inflation** bas/central/haut (revalorisation) — NB `*_pension_servie`
  est cassé côté moteur (dépend de `*_pension_au_31_decembre` non défini).
- **Projection de carrière** ajustable (temps partiel, évolution salariale).
- **Retraite complémentaire CAVIS** (assiette > 6×SMIG, paramétrage à vérifier).
- **Bilingue FR/AR** : **module `app/i18n.py` CRÉÉ** (sur disque, non commité) —
  **84 clés FR/AR** couvrant tous les libellés de l'app (champs, titres, sorties,
  messages, colonnes). `t(cle, lang)` + `LANGUES` + repli testés. **Reste le
  CÂBLAGE dans `app.py`** (suivre `docs/notes/i18n-cablage.md`) : (1) ajouter le
  sélecteur `ui.input_select("lang", t("langue"), LANGUES)` en tête du sidebar ;
  (2) `@reactive.effect` posant `dir=rtl/ltr` + `lang` sur `<html>` et appelant
  `ui.update_select/numeric/checkbox/...` pour TOUS les inputs avec `t(cle, lang)` ;
  (3) rendre les titres/notes statiques via `ui.output_ui` et traduire les sorties
  (`@render.ui`/`@render.data_frame`) avec `t()`. ⚠️ À vérifier EN NAVIGATEUR
  (rendu RTL + arabe + déclenchement des `update_*`) — ne pas faire à l'aveugle.
  Limites connues (notes paie) : libellés d'onglets non renommables après création ;
  PDF arabe nécessite `arabic-reshaper`+`python-bidi`. Référence complète
  fonctionnelle : `tunisie-simulateur-paie/app/{i18n.py,app.py}`.
- **Export PDF** du scénario (rmarkdown/reportlab ou via navigateur).

### Vague 3 (upstream openfisca-tunisia, PR dédiées + sourcing légal)
- **RSA cassé** : `marche_travail.smag`→`smag_journalier`, barème d'annuités
  agricole (remplacer `retraite.rsa.bareme_annuite` absent par
  `taux_annuite_base/supplementaire`), symboles indéfinis dans `regimes/rsa.py`.
- **Décote « convenance personnelle −0,5 %/trim »** (RSNA) : non modélisée.
- **`*_pension_servie` / revalorisation** : définir `*_pension_au_31_decembre`.
- **Départ anticipé RSNA** (mère 3 enfants, usure, licenciement éco) : non branché.
- **Modéliser rsaa/rtns/rtte/re/rtfr/raci** : chacun = projet (classe + loi).

## 5. INFRA / DÉPLOIEMENT — rappels

- **CD GitHub** opérationnel (`.github/workflows/deploy.yml`, `--app-id 18429443`).
  Secrets `SHINYAPPS_*` posés. ⚠️ Le secret du `.env` avait été **tronqué d'1
  caractère** (39 au lieu de 40) → corrigé depuis `~/.rsconnect-python/servers.json`.
- **openfisca-tunisia** : PR #527 (éligibilité 120 mois, 0.164) et #528 (lecture
  seule, 0.165) **mergées** ; 0.165 publié sur PyPI.
- **Doublons shinyapps** : `simulateur-pension-tunisie1` et `simulateur-paie-tunisie1`
  (sleeping) à archiver depuis le dashboard (l'API refuse de supprimer un app `sleeping`).
- **App locale** tournait sur `:8101` (`OPENFISCA_MODE=local`) ; API pension sur
  `:5001` (mode api). Logs : `/tmp/pension_shiny.log`.

## 6. TODOs actives (liste de session)

- #12 « Vague 2 (reste) » : net fiscal **fait (à committer)** ; reste scénarios
  inflation, projection, CAVIS, bilingue, PDF.
- Nouveau : **refonte UX entonnoir** (point 2 ci-dessus).
