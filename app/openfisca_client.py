"""Client de l'API web OpenFisca-Tunisia — package des pensions.

L'app Shiny ne calcule rien elle-même : elle construit la carrière d'un assuré
(salaire année par année, durée d'assurance, âge déduit de la date de naissance),
la poste à l'API OpenFisca-Tunisia (country-package `openfisca_tunisia_pension`),
et lit les résultats dans la réponse. OpenFisca reste le seul moteur de calcul.

En local, lancer l'API avec :
    openfisca serve -c openfisca_tunisia_pension -p 5001
"""

from __future__ import annotations

import os

import httpx

# URL de l'API OpenFisca pension. Surchargée par OPENFISCA_API_URL.
API_URL = os.environ.get("OPENFISCA_API_URL", "http://localhost:5001")

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
    """Poste la situation et renvoie les sorties pension à la liquidation."""
    an = str(annee_liquidation)
    reponse = httpx.post(f"{API_URL}/calculate", json=situation, timeout=timeout)
    reponse.raise_for_status()
    individu = reponse.json()["individus"]["ind0"]
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
    """Teste si l'API OpenFisca pension répond (message clair dans l'UI)."""
    try:
        return httpx.get(f"{API_URL}/spec", timeout=timeout).status_code == 200
    except httpx.HTTPError:
        return False
