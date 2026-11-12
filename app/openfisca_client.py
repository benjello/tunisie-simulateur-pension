"""Client de l'API web OpenFisca-Tunisia — package des pensions.

L'app Shiny ne calcule rien elle-même : elle construit la carrière d'un assuré,
la poste à l'API OpenFisca-Tunisia (country-package `openfisca_tunisia_pension`),
et lit la pension dans la réponse. OpenFisca reste le seul moteur de calcul.

En local, lancer l'API avec :
    openfisca serve -c openfisca_tunisia_pension -p 5001
"""

from __future__ import annotations

import os

import httpx

# URL de l'API OpenFisca pension. Surchargée par OPENFISCA_API_URL.
# Port 5001 par défaut pour cohabiter avec l'API paie (5000).
API_URL = os.environ.get("OPENFISCA_API_URL", "http://localhost:5001")

# Régimes exposés (clé openfisca -> libellé UI). RSA n'est pas exposé : son
# barème d'annuités n'est pas paramétré aux années récentes (voir backlog).
REGIMES = {
    "rsna": "Privé non agricole (CNSS — RSNA)",
    "cnrps": "Secteur public (CNRPS)",
}

# Variables de sortie demandées au moteur, par régime (préfixe ajouté).
SORTIES = [
    "salaire_de_reference",
    "taux_de_liquidation",
    "pension_brute",
    "pension",
]


def construire_situation(
    *,
    regime: str,
    annee_liquidation: int,
    salaire_annuel: float,
    duree_assurance_annees: float,
    age: int,
    annees_carriere: int = 12,
) -> dict:
    """Construit la situation JSON OpenFisca pour un assuré au régime donné.

    - `salaire_annuel` : salaire de base annuel (DT/an), supposé constant sur la
      carrière (suffisant pour remplir la fenêtre de référence des 10 dernières
      années en RSNA, et pour fixer le dernier salaire en CNRPS).
    - `duree_assurance_annees` : convertie en trimestres (× 4).
    - La pension est calculée sur l'année de liquidation.
    """
    prefixe = regime  # "rsna" ou "cnrps"
    an = str(annee_liquidation)

    # Historique de salaire annuel constant sur les `annees_carriere` dernières
    # années (fenêtre de référence RSNA = 10 ans ; marge de sécurité à 12).
    historique = {
        str(annee_liquidation - k): salaire_annuel
        for k in range(max(annees_carriere, 11))
    }

    individu: dict = {
        f"{prefixe}_salaire_de_base": historique,
        f"{prefixe}_duree_assurance": {an: int(round(duree_assurance_annees * 4))},
        "age": {an: age},
    }
    for sortie in SORTIES:
        individu[f"{prefixe}_{sortie}"] = {an: None}

    return {
        "individus": {"ind0": individu},
        "menages": {"m0": {"personne_de_reference": ["ind0"]}},
    }


def calculer_pension(
    situation: dict,
    *,
    regime: str,
    annee_liquidation: int,
    timeout: float = 30.0,
) -> dict:
    """Poste la situation à l'API et renvoie les sorties pension (dict plat).

    Lève httpx.HTTPError si l'API ne répond pas ou renvoie une erreur.
    """
    an = str(annee_liquidation)
    reponse = httpx.post(f"{API_URL}/calculate", json=situation, timeout=timeout)
    reponse.raise_for_status()
    individu = reponse.json()["individus"]["ind0"]

    resultat = {}
    for sortie in SORTIES:
        valeur = individu.get(f"{regime}_{sortie}", {}).get(an)
        resultat[sortie] = valeur
    return resultat


def api_disponible(timeout: float = 3.0) -> bool:
    """Teste si l'API OpenFisca pension répond (message clair dans l'UI)."""
    try:
        return httpx.get(f"{API_URL}/spec", timeout=timeout).status_code == 200
    except httpx.HTTPError:
        return False
