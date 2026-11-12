"""Simulateur de pension de retraite (Tunisie — régimes RSNA et CNRPS).

Interface Shiny for Python. Aucun calcul n'est fait ici : la carrière est
envoyée à l'API OpenFisca-Tunisia (package `openfisca_tunisia_pension`), qui
renvoie les résultats.

Deux modes de saisie :
  - Simplifié : salaire mensuel constant + durée d'assurance.
  - Carrière détaillée : salaire et trimestres validés année par année (grille
    éditable), avec le détail par période de chaque variable pertinente.

L'âge à la liquidation est déduit de la date de naissance.

Lancer l'API puis l'app, en local :
    openfisca serve -c openfisca_tunisia_pension -p 5001
    shiny run app/app.py --port 8101
"""

from __future__ import annotations

import datetime

import httpx
import pandas as pd
from shiny import App, reactive, render, ui

from openfisca_client import (
    REGIMES,
    SORTIES,
    age_a_la_liquidation,
    api_disponible,
    calculer,
    carriere_constante,
    construire_situation,
    details_par_periode,
)

ANNEES_LIQ = [str(a) for a in range(2015, 2027)]


def _grille_carriere(annee_liquidation: int, nb_annees: int, salaire_annuel: float) -> pd.DataFrame:
    """Carrière initiale : nb_annees lignes se terminant à l'année de liquidation."""
    annees = list(range(annee_liquidation - nb_annees + 1, annee_liquidation + 1))
    return pd.DataFrame(
        {
            "Année": annees,
            "Salaire annuel (DT)": [float(salaire_annuel)] * len(annees),
            "Trimestres validés": [4] * len(annees),
        }
    )


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("regime", "Régime de retraite", REGIMES, selected="rsna"),
        ui.input_date(
            "naissance", "Date de naissance", value="1960-01-01",
            min="1930-01-01", max="2010-12-31", startview="decade",
        ),
        ui.input_select("annee_liq", "Année de liquidation", ANNEES_LIQ, selected="2020"),
        ui.input_radio_buttons(
            "mode", "Mode de saisie",
            {"simple": "Simplifié", "avance": "Carrière détaillée"},
            selected="simple",
        ),
        ui.panel_conditional(
            "input.mode === 'simple'",
            ui.input_numeric("salaire_mensuel", "Salaire mensuel (DT)", 2000, min=0, step=100),
            ui.input_numeric("duree", "Durée d'assurance (années)", 30, min=0, max=50, step=1),
        ),
        ui.panel_conditional(
            "input.mode === 'avance'",
            ui.input_numeric("nb_annees", "Nombre d'années de carrière", 30, min=1, max=50, step=1),
            ui.input_numeric("salaire_init", "Salaire annuel initial (DT)", 24000, min=0, step=1000),
            ui.input_action_button("generer", "Générer / réinitialiser la carrière", class_="btn-secondary btn-sm"),
        ),
        ui.hr(),
        ui.input_action_button("calculer", "Calculer la pension", class_="btn-primary"),
        width=340,
    ),
    ui.h3("Simulateur de pension — Tunisie"),
    ui.output_ui("statut_api"),
    ui.output_ui("entete"),
    ui.panel_conditional(
        "input.mode === 'avance'",
        ui.card(
            ui.card_header("Carrière (éditable : salaire et trimestres par année)"),
            ui.output_data_frame("grille"),
        ),
    ),
    ui.output_ui("resume"),
    ui.accordion(
        ui.accordion_panel(
            "Détails par période (toutes les variables pertinentes)",
            ui.output_data_frame("details"),
        ),
        open=False,
        id="acc_details",
    ),
    ui.markdown(
        "Calculé par le moteur **OpenFisca-Tunisia** (package pension). Montants "
        "**annuels** (DT/an). RSNA : salaire de référence = 10 dernières années "
        "actualisées, 40 % + 2 %/an, plafond 80 %, stage 10 ans, âge 60. CNRPS : "
        "dernier salaire, 2 %/an puis 3 %/an, plafond 90 %, minimum 15 ans, âge 62."
    ),
    title="Simulateur de pension Tunisie",
)


def _fmt(valeur, unite: str) -> str:
    if valeur is None:
        return "—"
    if unite == "bool":
        return "oui" if valeur else "non"
    if unite == "%":
        return f"{valeur * 100:,.2f} %".replace(",", " ")
    return f"{valeur:,.3f} DT".replace(",", " ")


def server(input, output, session):
    # État de la grille de carrière (mode avancé).
    carriere_rv = reactive.value(_grille_carriere(2020, 30, 24000.0))

    @reactive.effect
    @reactive.event(input.generer)
    def _regenere():
        carriere_rv.set(
            _grille_carriere(
                int(input.annee_liq()),
                int(input.nb_annees() or 1),
                float(input.salaire_init() or 0),
            )
        )

    @render.data_frame
    def grille():
        return render.DataGrid(carriere_rv(), editable=True, width="100%")

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

    def _age():
        return age_a_la_liquidation(input.naissance().year, int(input.annee_liq()))

    @render.ui
    def entete():
        age = _age()
        alerte = ""
        if age < 50:
            alerte = " ⚠️ âge très faible pour une liquidation"
        return ui.markdown(
            f"**Régime :** {REGIMES[input.regime()]} — **né en** {input.naissance().year} — "
            f"**liquidation** {input.annee_liq()} — **âge** {age} ans{alerte}."
        )

    @reactive.calc
    def _carriere_et_duree():
        """Retourne (dict{annee:salaire}, duree_annees) selon le mode."""
        annee_liq = int(input.annee_liq())
        if input.mode() == "avance":
            df = grille.data_view()  # inclut les éditions de l'utilisateur
            carriere = {
                int(r["Année"]): float(r["Salaire annuel (DT)"])
                for _, r in df.iterrows()
            }
            trimestres = float(df["Trimestres validés"].sum())
            return carriere, trimestres / 4.0
        salaire_annuel = float(input.salaire_mensuel() or 0) * 12.0
        duree = float(input.duree() or 0)
        return carriere_constante(salaire_annuel, annee_liq, int(duree) or 11), duree

    @reactive.calc
    @reactive.event(input.calculer, ignore_none=False)
    def resultat():
        regime = input.regime()
        annee_liq = int(input.annee_liq())
        carriere, duree = _carriere_et_duree()
        situation = construire_situation(
            regime=regime,
            annee_liquidation=annee_liq,
            carriere=carriere,
            duree_assurance_annees=duree,
            age=_age(),
        )
        try:
            res = calculer(situation, regime=regime, annee_liquidation=annee_liq)
            return ("ok", res, carriere)
        except httpx.HTTPError as erreur:
            return ("erreur", str(erreur), {})

    @render.ui
    def resume():
        statut, contenu, _ = resultat()
        if statut == "erreur":
            return ui.div(ui.markdown(f"**Erreur de calcul :** {contenu}"), class_="alert alert-danger")

        res = contenu
        pension_an = res.get("pension") or 0.0
        avert = ui.TagList()
        if not res.get("eligible"):
            avert = ui.div(
                ui.markdown(
                    "ℹ️ **Droit non ouvert** : durée d'assurance ou âge insuffisants "
                    "(RSNA : 10 ans et 60 ans ; CNRPS : 15 ans et 62 ans)."
                ),
                class_="alert alert-info",
            )

        lignes = []
        for cle, libelle, unite in SORTIES:
            fort = cle == "pension"
            style = "font-weight:700;" if fort else ""
            lignes.append(
                ui.tags.tr(
                    ui.tags.td(libelle, style=style),
                    ui.tags.td(_fmt(res.get(cle), unite), style=f"text-align:right;{style}"),
                )
            )
        lignes.append(
            ui.tags.tr(
                ui.tags.td("Pension servie (mensuelle, ÷12)", style="font-weight:700;"),
                ui.tags.td(_fmt(pension_an / 12.0, "DT"), style="text-align:right;font-weight:700;"),
            )
        )
        return ui.TagList(
            avert,
            ui.card(
                ui.card_header(f"Résultat — {REGIMES[input.regime()]}"),
                ui.tags.table(ui.tags.tbody(*lignes), class_="table table-sm"),
            ),
        )

    @render.data_frame
    def details():
        statut, contenu, carriere = resultat()
        if statut != "ok":
            return render.DataGrid(pd.DataFrame({"Info": ["Aucun calcul"]}))
        lignes = details_par_periode(
            regime=input.regime(),
            carriere=carriere,
            annee_liquidation=int(input.annee_liq()),
            resultats=contenu,
        )
        df = pd.DataFrame(
            [
                {
                    "Variable": l["variable"],
                    "Libellé": l["libelle"],
                    "Période": l["periode"],
                    "Valeur": _fmt(l["valeur"], l["unite"]),
                }
                for l in lignes
            ]
        )
        return render.DataGrid(df, width="100%", height="420px")


app = App(app_ui, server)
