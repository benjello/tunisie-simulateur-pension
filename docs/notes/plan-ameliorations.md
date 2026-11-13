# Plan d'améliorations avancées — simulateur de pension

Plan issu de trois audits croisés (2026-11-12) :
1. **Veille Tunisie** (secu.tn, 22.tn, retraite.tn, ihsibly.com, CNSS/CNRPS).
2. **Veille internationale** (France info-retraite/M@rel, SSA, DRV, mypension.be,
   mijnpensioenoverzicht, Canada, OCDE *Pensions at a Glance*, Banque mondiale).
3. **Audit du moteur** `openfisca_tunisia_pension` (capacités déjà codées mais non
   exposées, vérifiées par le calcul).

## 1. Positionnement stratégique

**Notre avantage unique** : l'app s'appuie sur OpenFisca, donc sur une carrière
**année par année** et les règles réglementaires exactes (actualisation des
salaires, plafonds, planchers, barèmes datés). **Aucun** simulateur tunisien ne
fait ça : tous partent d'un « salaire moyen » approximatif.

**Angles morts du marché tunisien** (donc différenciateurs) :
- Coordination **carrière mixte privé↔public** (CNSS↔CNRPS) — absente de tous.
- **Réversion / survivants** — absente de tous.
- **Taux de remplacement** (pension / dernier salaire) — affiché par personne.
- **Optimisation de l'âge de départ** (courbe décote/bonification) — à peine
  esquissée (ihsibly compare 62/65 ponctuellement).
- **Projection prospective** avec hypothèses (inflation, revalorisation).

**Ce que secu.tn fait et qu'on doit au moins égaler** (sinon perçu incomplet) :
brut **et** net avec détail des retenues, plafond 6×SMIG, plancher 2/3 SMIG,
actualisation des salaires, décote anticipée, bonifications, régime exceptionnel
57 ans, fiscalité (IRPP/CSS).

## 2. Ce que le moteur sait DÉJÀ faire (non exposé) — vérifié par calcul

| Capacité | État moteur | Variables | Effort app |
|---|---|---|---|
| Bonifications CNRPS (cadre actif, militaire) | ✅ fonctionnel | `cnrps_bonifications` (entrées `duree_service_cadre_actif`, `duree_service_militaire`) | Faible |
| Départ anticipé CNRPS (mères 3 enf., astreignant, invalidité, sur demande) | ✅ (agit sur âge/durée requis) | `cnrps_age_requis`, `cnrps_duree_requise_annees` | Faible |
| **Coordination CNRPS + CNSS** (carrière mixte) | ✅ (prorata + taux) | entrée `cnss_duree_assurance_annuelle` → `cnrps_pension_brute/taux/eligible` | Faible |
| Indemnités familiales + indemnité revenu unique (CNRPS) | ✅ (barèmes datés) | `cnrps_indemnites_familiales`, `cnrps_indemnite_revenu_unique` | Faible |
| Réversion conjoint (CNRPS/RSNA/RSA) | ✅ (période MENSUELLE) | `*_pension_de_reversion`, `*_taux_reversion` | Moyen |
| Pensions d'orphelins + capital-décès CNRPS | ✅ | `*_pension_orphelins_totale`, `cnrps_capital_deces` | Moyen |
| Régimes spéciaux gouverneurs / députés | ✅ | `gouverneur_pension_brute`, `depute_pension_brute` | Moyen |

**Cassé / non modélisé (ne pas exposer tel quel)** :
- `*_pension_servie` / revalorisation : **CASSÉ** (dépend de `*_pension_au_31_decembre`, variable jamais définie).
- **RSA** : CASSÉ (`regimes/rsa.py` référence des symboles indéfinis `duree_assurance`/`sal_ref`/`age`/`n` ; paramètres absents `marche_travail.smag` → existe sous `smag_journalier`, `retraite.rsa.bareme_annuite` manquant).
- **Décote « convenance personnelle −0,5 %/trim »** : enum RSNA présent mais **aucune formule** de minoration.
- **rsaa / rtns / rtte / re / rtfr / raci** : paramètres riches, **aucune classe de calcul**.
- Départ anticipé **côté RSNA** : énuméré mais non branché (asymétrie avec CNRPS).

## 3. Plan par vagues (impact × effort)

> **Statut 2026-11-13** — **Vague 1 LIVRÉE** (taux de remplacement, explication du
> taux + base légale, comparaison d'âges de départ + graphique, bonifications
> CNRPS, départ anticipé CNRPS, coordination CNRPS+CNSS, indemnités familiales +
> IRU, détails par période enrichis). **Vague 2 PARTIELLE** : livrés = survivants
> (réversion + orphelins), objectif inverse (dichotomie), graphique. Restent :
> net fiscal IRPP+CSS (cross-package), scénarios inflation, projection carrière,
> CAVIS, bilingue FR/AR, export PDF. Déployé sur shinyapps via CD.


### Vague 1 — Quick wins (moteur prêt, effort faible, impact fort)

- [ ] **Taux de remplacement brut** (`pension / dernier salaire annuel`) affiché en évidence. *(trivial)*
- [ ] **Explication du taux en clair** + **base légale** à côté de chaque chiffre (décret 74-499 art. 15/17 ; loi 85-12 art. 36/38/39) + tooltips façon DRV. *(faible)*
- [ ] **Détail actualisé du salaire de référence** : par année retenue, salaire nominal + coefficient d'actualisation + salaire actualisé. *(faible — données déjà calculées)*
- [ ] **Comparaison automatique de plusieurs âges de départ** (anticipé / taux plein / majoré) : boucle sur l'âge, tableau + courbe. *(faible — OpenFisca calcule déjà par scénario)*
- [ ] **Bonifications CNRPS** : 2 entrées (`duree_service_cadre_actif`, `duree_service_militaire`) → `cnrps_bonifications` (se répercute sur durée/taux/pension). *(faible)*
- [ ] **Départ anticipé CNRPS** : cases (mère 3 enfants, fonction astreignante, invalidité, sur demande) → `cnrps_age_requis` + `cnrps_duree_requise_annees`, explique l'éligibilité anticipée. *(faible)*
- [ ] **Coordination CNRPS + CNSS** (carrière mixte) : entrée `cnss_duree_assurance_annuelle` → prorata/taux. **Différenciateur majeur, effort faible.** *(faible)*
- [ ] **Indemnités familiales + IRU (CNRPS)** : entrées `nombre_enfants_charge`, `conjoint_sans_revenu`. *(faible)*
- [ ] **Jauges « il vous manque X »** : années pour le taux plein (80/90 %), âge minimal d'ouverture. *(faible)*

### Vague 2 — Effort moyen, impact fort

- [ ] **Onglet « Survivants »** : réversion conjoint + orphelins + capital-décès (période mensuelle, entrées « décès » dédiées). Angle mort total du marché. *(moyen)*
- [ ] **Scénarios bas / central / haut** sur inflation et revalorisation (incertitude lisible, façon mijnpensioenoverzicht). *(moyen)*
- [ ] **Projection de carrière ajustable** (temps partiel, évolution salariale future). *(moyen)*
- [ ] **Objectif inverse** : « quelle durée/salaire pour telle pension » (résolution par dichotomie, façon calculateur canadien). *(moyen)*
- [ ] **Fiscalité de la pension** (IRPP + CSS) → **net réel**. Réutiliser le modèle `openfisca_tunisia` (paie) : dépendance cross-package à cadrer. *(moyen)*
- [ ] **Retraite complémentaire CAVIS** intégrée au total (assiette > 6×SMIG). *(moyen — paramétrage à vérifier)*
- [ ] **Bilingue arabe / français**, **export PDF** du scénario, **accessibilité** (WCAG). *(moyen — i18n Shiny réutilisable depuis la paie)*
- [ ] **Graphiques** : décomposition brut→net, taux de remplacement, pension vs âge. *(moyen)*

### Vague 3 — Chantiers modèle (upstream openfisca-tunisia, code + sourcing légal)

- [ ] **Corriger RSA** : `marche_travail.smag`→`smag_journalier`, écrire le barème d'annuités agricole (ou brancher `taux_annuite_base/supplementaire` au lieu de `bareme_annuite`), corriger les symboles indéfinis de `regimes/rsa.py`, dédoublonner les formules. Puis exposer RSA = **3 régimes**. *(élevé, à valider juridiquement)*
- [ ] **Décote convenance personnelle −0,5 %/trim** (RSNA) : règle à **implémenter** (non modélisée). *(moyen)*
- [ ] **Revalorisation / pension servie** : définir `*_pension_au_31_decembre` et réparer `*_pension_servie`. *(moyen/élevé)*
- [ ] **Départ anticipé RSNA** (mère 3 enfants, usure, licenciement éco) : brancher les formules. *(moyen)*
- [ ] **Modéliser rsaa / rtns / rtte / re / rtfr / raci** : chacun = **projet** (classe de régime + sourcing légal). *(élevé, plusieurs sessions)*
- [ ] Vérifier/compléter le **régime exceptionnel 57 ans (2022-2024/2027)** et le **cumul emploi-retraite** (non simulé par le marché). *(moyen)*

## 4. Différenciateurs à mettre en avant (marketing produit)

1. Carrière **année par année** → actualisation exacte (vs « salaire moyen »).
2. **Coordination privé↔public** (polypensionnés) — unique en Tunisie.
3. **Réversion / survivants** — unique en Tunisie.
4. **Optimisation de l'âge de départ** avec décote/bonification.
5. **Taux de remplacement** net et brut (référence OCDE).
6. **Transparence** : chaque chiffre relié à l'article de loi et au code OpenFisca.

## 5. Dépendances & risques techniques

- **Réversion/survivants** en période **MENSUELLE** → jeu d'entrées distinct (onglet séparé conseillé).
- **Fiscalité nette** : nécessite d'appeler aussi `openfisca_tunisia` (paie) → 2 country-packages dans la même app (API ou in-process).
- **Démarrage à froid numba** (mode local shinyapps) : à pré-chauffer.
- **Asymétrie RSNA/CNRPS** sur le départ anticipé : à signaler clairement à l'utilisateur tant que RSNA n'est pas branché.
- **i18n FR/AR** : réutiliser `i18n.py` de la paie.

## 6. Recommandation de séquencement

Commencer par la **Vague 1** (tout est prêt côté moteur, impact immédiat et
visible : taux de remplacement, explication, comparaison d'âges, bonifications,
départ anticipé, **coordination**). Puis **Vague 2** (survivants, scénarios,
net fiscal, bilingue). La **Vague 3** (corrections/modélisations upstream) se
mène en parallèle côté `openfisca-tunisia`, chaque item en PR dédiée avec tests.

> Sources détaillées des trois audits : voir les rapports d'agents de la session
> (veille Tunisie, veille internationale, audit moteur) — résumés ci-dessus.
