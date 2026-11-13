"""Client OpenFisca-Tunisia — package des pensions.

L'app Shiny ne calcule rien elle-même : elle construit la carrière d'un assuré
(salaire année par année, durée d'assurance, âge déduit de la date de naissance),
puis demande les résultats au moteur `openfisca_tunisia_pension`. OpenFisca reste
le seul moteur de calcul.

Deux modes, selon la variable d'environnement OPENFISCA_MODE :
- "api" (défaut) : poste la situation à l'API web sur OPENFISCA_API_URL
  (développement local, API séparée).
- "local" : calcule en direct, dans le même process, via
  TunisiaPensionTaxBenefitSystem. Utilisé en déploiement (shinyapps.io) où un
  seul service tourne.

Les deux modes consomment le MÊME format de situation JSON.

En mode api local, lancer l'API avec :
    openfisca serve -c openfisca_tunisia_pension -p 5001
"""

from __future__ import annotations

import os

import httpx

# URL de l'API OpenFisca pension. Surchargée par OPENFISCA_API_URL.
API_URL = os.environ.get("OPENFISCA_API_URL", "http://localhost:5001")

# Mode de calcul : "api" (HTTP) ou "local" (moteur in-process).
MODE = os.environ.get("OPENFISCA_MODE", "api").lower()

# TaxBenefitSystem chargé paresseusement en mode local (coûteux à l'import,
# exige numba).
_TBS = None


def _get_tbs():
    global _TBS
    if _TBS is None:
        from openfisca_tunisia_pension import CountryTaxBenefitSystem

        _TBS = CountryTaxBenefitSystem()
    return _TBS


def _calculate_local(situation: dict) -> dict:
    """Calcule en direct via SimulationBuilder et renvoie le résultat au format API.

    Toutes les variables à `None` dans la situation sont calculées et remplies,
    pour chaque période demandée ; on imite la structure de réponse de l'API.
    """
    from openfisca_core.simulations import SimulationBuilder

    tbs = _get_tbs()
    builder = SimulationBuilder()
    simulation = builder.build_from_entities(tbs, situation)

    resultat = {k: {} for k in situation}
    for collection, entites in situation.items():
        for ident, variables in entites.items():
            resultat[collection][ident] = {}
            for variable, periodes in variables.items():
                if not isinstance(periodes, dict):
                    resultat[collection][ident][variable] = periodes
                    continue
                resultat[collection][ident][variable] = {}
                for periode, valeur in periodes.items():
                    if valeur is None:
                        valeur = float(simulation.calculate(variable, periode)[0])
                    resultat[collection][ident][variable][periode] = valeur
    return resultat


def _calculate(situation: dict, *, timeout: float = 30.0) -> dict:
    """Route le calcul vers l'API HTTP ou le moteur local selon OPENFISCA_MODE."""
    if MODE == "local":
        return _calculate_local(situation)
    reponse = httpx.post(f"{API_URL}/calculate", json=situation, timeout=timeout)
    reponse.raise_for_status()
    return reponse.json()

# Régimes exposés (clé openfisca -> libellé UI). RSA n'est pas exposé : son
# barème d'annuités n'est pas paramétré aux années récentes (voir backlog).
REGIMES = {
    "rsna": "Privé non agricole (CNSS — RSNA)",
    "cnrps": "Secteur public (CNRPS)",
}

# Variables de sortie demandées au moteur (préfixe de régime ajouté à l'appel).
# (clé technique -> libellé lisible, unité)
SORTIES = [
    ("eligible", "Droit ouvert (éligibilité)", "bool"),
    ("salaire_de_reference", "Salaire de référence (annuel)", "DT"),
    ("taux_de_liquidation", "Taux de liquidation", "%"),
    ("pension_brute", "Pension brute (annuelle)", "DT"),
    ("pension_minimale", "Pension minimale garantie (annuelle)", "DT"),
    ("pension", "Pension servie (annuelle)", "DT"),
]
SORTIES_CLES = [cle for cle, _, _ in SORTIES]


def age_a_la_liquidation(annee_naissance: int, annee_liquidation: int) -> int:
    """Âge atteint dans l'année de liquidation (approximation annuelle)."""
    return int(annee_liquidation) - int(annee_naissance)


def carriere_constante(
    salaire_annuel: float, annee_liquidation: int, nb_annees: int
) -> dict[int, float]:
    """Carrière à salaire constant sur les `nb_annees` années précédant la
    liquidation (fenêtre de référence RSNA = 10 ans ; marge à 11 minimum)."""
    n = max(int(nb_annees), 11)
    return {annee_liquidation - k: float(salaire_annuel) for k in range(n)}


# Sorties supplémentaires propres à la CNRPS (le moteur les calcule déjà).
# (clé technique sans préfixe -> libellé, unité, période "an"/"mois")
EXTRAS_CNRPS = [
    ("age_requis", "Âge requis pour le départ", "an_val", "an"),
    ("duree_requise_annees", "Durée requise (années)", "an_val", "an"),
    ("bonifications", "Bonifications (trimestres)", "trim", "an"),
    ("duree_assurance", "Durée d'assurance totale (trimestres)", "trim", "an"),
    ("indemnites_familiales", "Indemnités familiales (mensuel)", "DT", "mois"),
    ("indemnite_revenu_unique", "Indemnité de revenu unique (mensuel)", "DT", "mois"),
]


def construire_situation(
    *,
    regime: str,
    annee_liquidation: int,
    carriere: dict[int, float],
    duree_assurance_annees: float,
    age: int,
    # Options CNRPS (ignorées pour RSNA) ----------------------------------
    duree_cadre_actif: int = 0,
    duree_militaire: int = 0,
    mere_3_enfants: bool = False,
    fonction_astreignante: bool = False,
    depart_sur_demande: bool = False,
    invalidite: bool = False,
    cnss_duree_annees: float = 0.0,
    nombre_enfants_charge: int = 0,
    conjoint_sans_revenu: bool = False,
) -> dict:
    """Construit la situation JSON OpenFisca.

    - `carriere` : {année: salaire annuel (DT)} — saisie année par année.
    - `duree_assurance_annees` : durée de service de base, en années (× 4 = trim).
    - Pour la CNRPS, les bonifications (cadre actif, militaire) et la
      coordination avec la CNSS s'ajoutent à cette durée de base ; le départ
      anticipé modifie l'âge/la durée requis.
    """
    an = str(annee_liquidation)
    mois = f"{annee_liquidation}-01"
    trim = int(round(duree_assurance_annees * 4))

    individu: dict = {
        f"{regime}_salaire_de_base": {str(a): float(s) for a, s in carriere.items()},
        "age": {an: int(age)},
    }
    for cle in SORTIES_CLES:
        individu[f"{regime}_{cle}"] = {an: None}

    if regime == "cnrps":
        # Durée de base annuelle ; les bonifications s'y ajoutent via le moteur.
        individu["cnrps_duree_assurance_annuelle"] = {an: trim}
        if duree_cadre_actif:
            individu["duree_service_cadre_actif"] = {an: int(duree_cadre_actif)}
        if duree_militaire:
            individu["duree_service_militaire"] = {an: int(duree_militaire)}
        if mere_3_enfants:
            individu["mere_3_enfants"] = {an: True}
        if fonction_astreignante:
            individu["fonction_astreignante"] = {an: True}
        if depart_sur_demande:
            individu["depart_anticipe_sur_demande"] = {an: True}
        if invalidite:
            individu["invalidite_physique"] = {an: True}
        if cnss_duree_annees:
            individu["cnss_duree_assurance_annuelle"] = {an: int(round(cnss_duree_annees * 4))}
        if nombre_enfants_charge:
            individu["nombre_enfants_charge"] = {mois: int(nombre_enfants_charge)}
        if conjoint_sans_revenu:
            individu["conjoint_sans_revenu"] = {mois: True}
        for cle, _lib, _u, per in EXTRAS_CNRPS:
            cle_per = mois if per == "mois" else an
            individu[f"cnrps_{cle}"] = {cle_per: None}
    else:
        individu["rsna_duree_assurance"] = {an: trim}

    return {
        "individus": {"ind0": individu},
        "menages": {"m0": {"personne_de_reference": ["ind0"]}},
    }


def calculer(
    situation: dict, *, regime: str, annee_liquidation: int, timeout: float = 30.0
) -> dict:
    """Calcule la situation (API ou local) et renvoie les sorties à la liquidation.

    Renvoie les sorties de base, plus les extras CNRPS si applicables.
    """
    an = str(annee_liquidation)
    mois = f"{annee_liquidation}-01"
    data = _calculate(situation, timeout=timeout)
    individu = data["individus"]["ind0"]
    res = {cle: individu.get(f"{regime}_{cle}", {}).get(an) for cle in SORTIES_CLES}
    if regime == "cnrps":
        for cle, _lib, _u, per in EXTRAS_CNRPS:
            cle_per = mois if per == "mois" else an
            res[cle] = individu.get(f"cnrps_{cle}", {}).get(cle_per)
    return res


def taux_de_remplacement(pension_annuelle, dernier_salaire_annuel):
    """Pension / dernier salaire (None si indisponible)."""
    if not pension_annuelle or not dernier_salaire_annuel:
        return None
    return pension_annuelle / dernier_salaire_annuel


def comparer_ages(
    *, regime, annee_liquidation, carriere, duree_assurance_annees, age_base,
    ages, options=None, timeout=30.0,
):
    """Compare la pension selon l'âge de départ.

    Hypothèse : l'assuré travaille jusqu'à l'âge testé → la durée augmente d'une
    année par année supplémentaire travaillée (approximation lisible).
    """
    options = options or {}
    lignes = []
    for a in ages:
        duree = max(0.0, duree_assurance_annees + (a - age_base))
        sit = construire_situation(
            regime=regime, annee_liquidation=annee_liquidation, carriere=carriere,
            duree_assurance_annees=duree, age=int(a), **options,
        )
        r = calculer(sit, regime=regime, annee_liquidation=annee_liquidation, timeout=timeout)
        lignes.append({
            "age": int(a),
            "duree_annees": round(duree, 2),
            "taux": r.get("taux_de_liquidation"),
            "eligible": bool(r.get("eligible")),
            "pension": r.get("pension"),
        })
    return lignes


def details_par_periode(
    *, regime: str, carriere: dict[int, float], annee_liquidation: int, resultats: dict
) -> list[dict]:
    """Construit les lignes de détail (variable, période, valeur) pour l'UI.

    - Le salaire de base est détaillé année par année (entrée de carrière).
    - Les variables calculées sont rapportées à l'année de liquidation.
    """
    lignes: list[dict] = []
    for annee in sorted(carriere):
        lignes.append(
            {
                "variable": f"{regime}_salaire_de_base",
                "libelle": "Salaire de base (annuel)",
                "periode": str(annee),
                "valeur": carriere[annee],
                "unite": "DT",
            }
        )
    for cle, libelle, unite in SORTIES:
        lignes.append(
            {
                "variable": f"{regime}_{cle}",
                "libelle": libelle,
                "periode": str(annee_liquidation),
                "valeur": resultats.get(cle),
                "unite": unite,
            }
        )
    if regime == "cnrps":
        for cle, libelle, unite, per in EXTRAS_CNRPS:
            if resultats.get(cle) is None:
                continue
            lignes.append(
                {
                    "variable": f"cnrps_{cle}",
                    "libelle": libelle,
                    "periode": f"{annee_liquidation}-01" if per == "mois" else str(annee_liquidation),
                    "valeur": resultats.get(cle),
                    "unite": unite,
                }
            )
    return lignes


# Sorties « survivants » (période mensuelle).
SURVIVANTS = [
    ("pension_de_reversion", "Pension de réversion du conjoint (mensuel)", "DT"),
    ("pension_orphelins_totale", "Pensions d'orphelins — total (mensuel)", "DT"),
]


def calculer_survivants(
    *, regime, annee_liquidation, pension_reference_mensuelle,
    conjoint_eligible, nb_orphelins, nb_orphelins_pere_mere=0, timeout=30.0,
):
    """Pensions de survivants en cas de décès de l'assuré.

    `pension_reference_mensuelle` = pension mensuelle du défunt (on branche
    la pension simulée). Variables du moteur en période MENSUELLE.
    """
    mois = f"{annee_liquidation}-01"
    ind = {
        "age_deces": {mois: 65},
        f"{regime}_pension_reference_deces": {mois: float(pension_reference_mensuelle)},
        "conjoint_survivant_eligible": {mois: bool(conjoint_eligible)},
        "nombre_orphelins_eligibles": {mois: int(nb_orphelins)},
        "nombre_orphelins_pere_et_mere_eligibles": {mois: int(nb_orphelins_pere_mere)},
    }
    for cle, _lib, _u in SURVIVANTS:
        ind[f"{regime}_{cle}"] = {mois: None}
    sit = {"individus": {"ind0": ind}, "menages": {"m0": {"personne_de_reference": ["ind0"]}}}
    g = _calculate(sit, timeout=timeout)["individus"]["ind0"]
    return {cle: g.get(f"{regime}_{cle}", {}).get(mois) for cle, _lib, _u in SURVIVANTS}


def objectif_inverse(
    *, regime, annee_liquidation, carriere, age, pension_cible_annuelle,
    options=None, timeout=30.0, duree_max=45,
):
    """Durée d'assurance (années) nécessaire pour atteindre une pension cible,
    par dichotomie, à carrière/salaire donnés."""
    options = options or {}

    def pension_pour(duree):
        sit = construire_situation(
            regime=regime, annee_liquidation=annee_liquidation, carriere=carriere,
            duree_assurance_annees=duree, age=age, **options)
        return calculer(sit, regime=regime, annee_liquidation=annee_liquidation,
                        timeout=timeout).get("pension") or 0.0

    cible = float(pension_cible_annuelle)
    hi = float(duree_max)
    if pension_pour(hi) < cible:
        return {"atteignable": False, "duree": hi, "pension": pension_pour(hi)}
    lo = 0.0
    for _ in range(24):
        mid = (lo + hi) / 2
        if pension_pour(mid) >= cible:
            hi = mid
        else:
            lo = mid
    return {"atteignable": True, "duree": round(hi, 2), "pension": pension_pour(hi)}


def api_disponible(timeout: float = 3.0) -> bool:
    """Teste la disponibilité du moteur (message clair dans l'UI).

    En mode local, le moteur est toujours disponible (calcul in-process).
    """
    if MODE == "local":
        return True
    try:
        return httpx.get(f"{API_URL}/spec", timeout=timeout).status_code == 200
    except httpx.HTTPError:
        return False
