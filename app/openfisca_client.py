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


def construire_situation(
    *,
    regime: str,
    annee_liquidation: int,
    carriere: dict[int, float],
    duree_assurance_annees: float,
    age: int,
) -> dict:
    """Construit la situation JSON OpenFisca.

    - `carriere` : {année: salaire annuel (DT)} — saisie année par année.
    - `duree_assurance_annees` : convertie en trimestres (× 4).
    - La pension est calculée sur l'année de liquidation.
    """
    prefixe = regime
    an = str(annee_liquidation)

    individu: dict = {
        f"{prefixe}_salaire_de_base": {str(a): float(s) for a, s in carriere.items()},
        f"{prefixe}_duree_assurance": {an: int(round(duree_assurance_annees * 4))},
        "age": {an: int(age)},
    }
    for cle in SORTIES_CLES:
        individu[f"{prefixe}_{cle}"] = {an: None}

    return {
        "individus": {"ind0": individu},
        "menages": {"m0": {"personne_de_reference": ["ind0"]}},
    }


def calculer(
    situation: dict, *, regime: str, annee_liquidation: int, timeout: float = 30.0
) -> dict:
    """Calcule la situation (API ou local) et renvoie les sorties à la liquidation."""
    an = str(annee_liquidation)
    data = _calculate(situation, timeout=timeout)
    individu = data["individus"]["ind0"]
    return {cle: individu.get(f"{regime}_{cle}", {}).get(an) for cle in SORTIES_CLES}


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
    return lignes


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
