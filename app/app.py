"""Simulateur de pension de retraite (Tunisie — régimes RSNA et CNRPS).

Interface Shiny for Python. Aucun calcul n'est fait ici : la carrière est
envoyée à l'API OpenFisca-Tunisia (package `openfisca_tunisia_pension`), qui
renvoie la pension.

Lancer l'API puis l'app, en local :
    openfisca serve -c openfisca_tunisia_pension -p 5001
    shiny run app/app.py --port 8101
"""

from __future__ import annotations

import httpx
from shiny import App, reactive, render, ui

from openfisca_client import (
    REGIMES,
    api_disponible,
    calculer_pension,
    construire_situation,
)

ANNEES = [str(a) for a in range(2015, 2027)]

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("regime", "Régime de retraite", REGIMES, selected="rsna"),
        ui.input_select("annee", "Année de liquidation", ANNEES, selected="2020"),
        ui.input_numeric("salaire_mensuel", "Salaire mensuel (DT)", 2000, min=0, step=100),
        ui.input_numeric("duree", "Durée d'assurance (années)", 30, min=0, max=50, step=1),
        ui.input_numeric("age", "Âge à la liquidation", 62, min=50, max=75, step=1),
        ui.hr(),
        ui.input_action_button("calculer", "Calculer la pension", class_="btn-primary"),
        width=330,
    ),
    ui.h3("Simulateur de pension — Tunisie"),
    ui.output_ui("statut_api"),
    ui.output_ui("resultat_ui"),
    ui.markdown(
        "Calculé par le moteur **OpenFisca-Tunisia** (package pension, via son "
        "API). Salaire supposé constant sur la carrière. Montants **annuels** "
        "(DT/an). RSNA : salaire de référence = 10 dernières années actualisées, "
        "taux 40 % + 2 %/an, plafond 80 %. CNRPS : dernier salaire, 2 %/an puis "
        "3 %/an, plafond 90 %, minimum 15 ans."
    ),
    title="Simulateur de pension Tunisie",
)


def _ligne(libelle: str, valeur, *, suffixe: str = " DT", fort: bool = False) -> ui.Tag:
    if valeur is None:
        texte = "—"
    elif suffixe == " %":
        texte = f"{valeur * 100:,.2f} %".replace(",", " ")
    else:
        texte = f"{valeur:,.3f}{suffixe}".replace(",", " ")
    style = "font-weight:700;" if fort else ""
    return ui.tags.tr(
        ui.tags.td(libelle, style=style),
        ui.tags.td(texte, style=f"text-align:right;{style}"),
    )


def server(input, output, session):
    @render.ui
    def statut_api():
        if api_disponible():
            return ui.TagList()
        return ui.div(
            ui.markdown(
                "⚠️ **API OpenFisca pension injoignable.** Démarrez-la en local :\n\n"
                "```\nopenfisca serve -c openfisca_tunisia_pension -p 5001\n```"
            ),
            class_="alert alert-warning",
        )

    @reactive.calc
    @reactive.event(input.calculer, ignore_none=False)
    def resultat():
        regime = str(input.regime())
        annee = int(input.annee())
        situation = construire_situation(
            regime=regime,
            annee_liquidation=annee,
            salaire_annuel=float(input.salaire_mensuel() or 0) * 12.0,
            duree_assurance_annees=float(input.duree() or 0),
            age=int(input.age() or 0),
        )
        try:
            return ("ok", calculer_pension(situation, regime=regime, annee_liquidation=annee))
        except httpx.HTTPError as erreur:
            return ("erreur", str(erreur))

    @render.ui
    def resultat_ui():
        statut, contenu = resultat()
        if statut == "erreur":
            return ui.div(
                ui.markdown(f"**Erreur de calcul :** {contenu}"),
                class_="alert alert-danger",
            )

        r = contenu
        pension_an = r["pension"] or 0.0
        pension_mois = pension_an / 12.0

        avert = ui.TagList()
        if pension_an == 0:
            avert = ui.div(
                ui.markdown(
                    "ℹ️ Pension nulle : durée d'assurance probablement inférieure "
                    "au minimum d'ouverture du droit (15 ans CNRPS, 10 ans RSNA)."
                ),
                class_="alert alert-info",
            )

        table = ui.tags.table(
            ui.tags.tbody(
                _ligne("Salaire de référence (annuel)", r["salaire_de_reference"]),
                _ligne("Taux de liquidation", r["taux_de_liquidation"], suffixe=" %"),
                _ligne("Pension brute (annuelle)", r["pension_brute"]),
                _ligne("Pension servie (annuelle)", pension_an, fort=True),
                _ligne("Pension servie (mensuelle, ÷12)", pension_mois, fort=True),
            ),
            class_="table table-sm",
        )

        return ui.TagList(
            avert,
            ui.card(ui.card_header(f"Pension — {REGIMES[str(input.regime())]}"), table),
        )


app = App(app_ui, server)
