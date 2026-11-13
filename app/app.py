"""Simulateur de pension de retraite (Tunisie — régimes RSNA et CNRPS).

Interface Shiny for Python. Aucun calcul n'est fait ici : la carrière est
envoyée au moteur OpenFisca-Tunisia (package `openfisca_tunisia_pension`), via
l'API ou en direct (OPENFISCA_MODE=local).

Fonctionnalités (vague 1) :
  - Modes simplifié / carrière détaillée (grille éditable) ; âge via date de naissance.
  - Taux de remplacement, explication du taux + base légale, détails par période.
  - CNRPS : bonifications (cadre actif, militaire), départ anticipé (mères 3 enfants,
    fonction astreignante, invalidité, sur demande), coordination avec la CNSS
    (carrière mixte), indemnités familiales et de revenu unique.
  - Comparaison de la pension selon l'âge de départ.

Lancer en local :
    openfisca serve -c openfisca_tunisia_pension -p 5001
    shiny run app/app.py --port 8101
"""

from __future__ import annotations

import httpx
import pandas as pd
from shiny import App, reactive, render, ui

from openfisca_client import (
    EXTRAS_CNRPS,
    REGIMES,
    SORTIES,
    age_a_la_liquidation,
    api_disponible,
    calculer,
    carriere_constante,
    comparer_ages,
    construire_situation,
    details_par_periode,
    taux_de_remplacement,
)

ANNEES_LIQ = [str(a) for a in range(2015, 2027)]

BASE_LEGALE = {
    "rsna": "Décret n° 74-499, art. 15 (stage 120 mois, âge 60) et art. 17 "
            "(40 % au terme du stage, +0,5 %/trimestre, plafond 80 %).",
    "cnrps": "Loi n° 85-12, art. 36 (dernier salaire, ≥ 3 ans), art. 38 "
             "(2 %/an puis 3 %/an puis 2 %/an, plafond 90 %), art. 22 (min 15 ans), "
             "art. 39 (plancher 2/3 SMIG).",
}


def _grille_carriere(annee_liquidation: int, nb_annees: int, salaire_annuel: float) -> pd.DataFrame:
    annees = list(range(annee_liquidation - nb_annees + 1, annee_liquidation + 1))
    return pd.DataFrame({
        "Année": annees,
        "Salaire annuel (DT)": [float(salaire_annuel)] * len(annees),
        "Trimestres validés": [4] * len(annees),
    })


def _expliquer_taux(regime: str, duree_annees: float, taux) -> str:
    if taux is None:
        return ""
    pct = f"{taux * 100:.1f} %"
    d = duree_annees
    if regime == "rsna":
        if d <= 10:
            calc = "40 % acquis au terme du stage de 10 ans"
        else:
            calc = f"40 % (10 premières années) + 2 %/an × {d - 10:.1f} ans"
        return f"Taux **{pct}** : {calc}, plafonné à 80 %."
    # cnrps
    parts = []
    reste = d
    for tranche, taux_an, label in [(10, 2, "10 premières années"), (10, 3, "10 suivantes"), (99, 2, "au-delà")]:
        if reste <= 0:
            break
        n = min(reste, tranche)
        parts.append(f"{taux_an} %/an × {n:.1f} ({label})")
        reste -= n
    return f"Taux **{pct}** : " + " + ".join(parts) + ", plafonné à 90 %."


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_select("regime", "Régime de retraite", REGIMES, selected="rsna"),
        ui.input_date("naissance", "Date de naissance", value="1960-01-01",
                      min="1930-01-01", max="2010-12-31", startview="decade"),
        ui.input_select("annee_liq", "Année de liquidation", ANNEES_LIQ, selected="2020"),
        ui.input_radio_buttons("mode", "Mode de saisie",
                               {"simple": "Simplifié", "avance": "Carrière détaillée"},
                               selected="simple"),
        ui.panel_conditional(
            "input.mode === 'simple'",
            ui.input_numeric("salaire_mensuel", "Salaire mensuel (DT)", 2000, min=0, step=100),
            ui.input_numeric("duree", "Durée d'assurance (années)", 30, min=0, max=50, step=1),
        ),
        ui.panel_conditional(
            "input.mode === 'avance'",
            ui.input_numeric("nb_annees", "Nombre d'années de carrière", 30, min=1, max=50, step=1),
            ui.input_numeric("salaire_init", "Salaire annuel initial (DT)", 24000, min=0, step=1000),
            ui.input_action_button("generer", "Générer / réinitialiser la carrière",
                                   class_="btn-secondary btn-sm"),
        ),
        # Options propres à la CNRPS -----------------------------------------
        ui.panel_conditional(
            "input.regime === 'cnrps'",
            ui.hr(),
            ui.h6("Options CNRPS"),
            ui.input_numeric("cadre_actif", "Service en cadre actif (années)", 0, min=0, max=45, step=1),
            ui.input_numeric("militaire", "Service militaire (années)", 0, min=0, max=45, step=1),
            ui.input_numeric("cnss_annees", "Durée cotisée à la CNSS (années, carrière mixte)", 0, min=0, max=45, step=1),
            ui.input_checkbox("mere3", "Mère de 3 enfants"),
            ui.input_checkbox("astreignant", "Fonction astreignante"),
            ui.input_checkbox("sur_demande", "Départ anticipé sur demande"),
            ui.input_checkbox("invalidite", "Invalidité physique"),
            ui.input_numeric("nb_enfants", "Enfants à charge", 0, min=0, max=10, step=1),
            ui.input_checkbox("conjoint_sans_revenu", "Conjoint sans revenu"),
        ),
        ui.hr(),
        ui.input_action_button("calculer", "Calculer la pension", class_="btn-primary"),
        width=360,
    ),
    ui.h3("Simulateur de pension — Tunisie"),
    ui.output_ui("statut_api"),
    ui.output_ui("entete"),
    ui.panel_conditional(
        "input.mode === 'avance'",
        ui.card(ui.card_header("Carrière (éditable : salaire et trimestres par année)"),
                ui.output_data_frame("grille")),
    ),
    ui.output_ui("resume"),
    ui.card(
        ui.card_header("Comparaison selon l'âge de départ (hypothèse : travail jusqu'à l'âge testé)"),
        ui.output_data_frame("comparaison"),
    ),
    ui.accordion(
        ui.accordion_panel("Détails par période (toutes les variables pertinentes)",
                            ui.output_data_frame("details")),
        open=False, id="acc_details",
    ),
    ui.markdown(
        "Calculé par le moteur **OpenFisca-Tunisia** (package pension). Montants "
        "**annuels** (DT/an) sauf mention. Le droit fait référence ; chaque règle "
        "est tranchée par le texte (voir base légale ci-dessus)."
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
    if unite == "an_val":
        return "—" if valeur == 0 else f"{valeur:,.0f} ans".replace(",", " ")
    if unite == "trim":
        return f"{valeur:,.0f} trim".replace(",", " ")
    return f"{valeur:,.3f} DT".replace(",", " ")


def server(input, output, session):
    carriere_rv = reactive.value(_grille_carriere(2020, 30, 24000.0))

    @reactive.effect
    @reactive.event(input.generer)
    def _regenere():
        carriere_rv.set(_grille_carriere(int(input.annee_liq()), int(input.nb_annees() or 1),
                                         float(input.salaire_init() or 0)))

    @render.data_frame
    def grille():
        return render.DataGrid(carriere_rv(), editable=True, width="100%")

    @render.ui
    def statut_api():
        if api_disponible():
            return ui.TagList()
        return ui.div(ui.markdown(
            "⚠️ **Moteur injoignable.** En mode API, démarrez-le :\n\n"
            "```\nopenfisca serve -c openfisca_tunisia_pension -p 5001\n```"),
            class_="alert alert-warning")

    def _age():
        return age_a_la_liquidation(input.naissance().year, int(input.annee_liq()))

    @render.ui
    def entete():
        return ui.markdown(
            f"**Régime :** {REGIMES[input.regime()]} — **né en** {input.naissance().year} — "
            f"**liquidation** {input.annee_liq()} — **âge** {_age()} ans.  \n"
            f"*Base légale :* {BASE_LEGALE[input.regime()]}")

    def _carriere_et_duree():
        annee_liq = int(input.annee_liq())
        if input.mode() == "avance":
            df = grille.data_view()
            carriere = {int(r["Année"]): float(r["Salaire annuel (DT)"]) for _, r in df.iterrows()}
            duree = float(df["Trimestres validés"].sum()) / 4.0
            return carriere, duree
        salaire_annuel = float(input.salaire_mensuel() or 0) * 12.0
        duree = float(input.duree() or 0)
        return carriere_constante(salaire_annuel, annee_liq, int(duree) or 11), duree

    def _options_cnrps():
        if input.regime() != "cnrps":
            return {}
        return dict(
            duree_cadre_actif=int(input.cadre_actif() or 0),
            duree_militaire=int(input.militaire() or 0),
            cnss_duree_annees=float(input.cnss_annees() or 0),
            mere_3_enfants=bool(input.mere3()),
            fonction_astreignante=bool(input.astreignant()),
            depart_sur_demande=bool(input.sur_demande()),
            invalidite=bool(input.invalidite()),
            nombre_enfants_charge=int(input.nb_enfants() or 0),
            conjoint_sans_revenu=bool(input.conjoint_sans_revenu()),
        )

    @reactive.calc
    @reactive.event(input.calculer, ignore_none=False)
    def resultat():
        regime, annee_liq = input.regime(), int(input.annee_liq())
        carriere, duree = _carriere_et_duree()
        options = _options_cnrps()
        sit = construire_situation(regime=regime, annee_liquidation=annee_liq,
                                   carriere=carriere, duree_assurance_annees=duree,
                                   age=_age(), **options)
        try:
            res = calculer(sit, regime=regime, annee_liquidation=annee_liq)
            return ("ok", res, carriere, duree, options)
        except httpx.HTTPError as e:
            return ("erreur", str(e), {}, 0, {})

    @render.ui
    def resume():
        statut, contenu, carriere, duree, _opt = resultat()
        if statut == "erreur":
            return ui.div(ui.markdown(f"**Erreur de calcul :** {contenu}"), class_="alert alert-danger")
        res = contenu
        pension_an = res.get("pension") or 0.0
        dernier_salaire = carriere[max(carriere)] if carriere else 0.0
        tr = taux_de_remplacement(pension_an, dernier_salaire)

        avert = ui.TagList()
        if not res.get("eligible"):
            avert = ui.div(ui.markdown(
                "ℹ️ **Droit non ouvert** : durée d'assurance ou âge insuffisants "
                "(RSNA : 10 ans et 60 ans ; CNRPS : 15 ans et 62 ans, sauf départ anticipé)."),
                class_="alert alert-info")

        lignes = []
        for cle, libelle, unite in SORTIES:
            fort = cle == "pension"
            style = "font-weight:700;" if fort else ""
            lignes.append(ui.tags.tr(ui.tags.td(libelle, style=style),
                                     ui.tags.td(_fmt(res.get(cle), unite), style=f"text-align:right;{style}")))
        lignes.append(ui.tags.tr(
            ui.tags.td("Pension servie (mensuelle, ÷12)", style="font-weight:700;"),
            ui.tags.td(_fmt(pension_an / 12.0, "DT"), style="text-align:right;font-weight:700;")))
        if tr is not None:
            lignes.append(ui.tags.tr(
                ui.tags.td("Taux de remplacement (pension / dernier salaire)", style="font-weight:700;"),
                ui.tags.td(_fmt(tr, "%"), style="text-align:right;font-weight:700;")))

        extras = ui.TagList()
        if input.regime() == "cnrps":
            sous = []
            for cle, libelle, unite, _per in EXTRAS_CNRPS:
                if res.get(cle) is None:
                    continue
                sous.append(ui.tags.tr(ui.tags.td(libelle),
                                       ui.tags.td(_fmt(res.get(cle), unite), style="text-align:right;")))
            if sous:
                extras = ui.TagList(
                    ui.tags.h6("Compléments CNRPS", style="margin-top:0.6rem;"),
                    ui.tags.table(ui.tags.tbody(*sous), class_="table table-sm"))

        return ui.TagList(
            avert,
            ui.card(
                ui.card_header(f"Résultat — {REGIMES[input.regime()]}"),
                ui.tags.table(ui.tags.tbody(*lignes), class_="table table-sm"),
                ui.markdown(_expliquer_taux(input.regime(), duree, res.get("taux_de_liquidation"))),
                extras,
            ),
        )

    @render.data_frame
    def comparaison():
        statut, contenu, carriere, duree, options = resultat()
        if statut != "ok":
            return render.DataGrid(pd.DataFrame({"Info": ["Aucun calcul"]}))
        age = _age()
        ages = sorted({a for a in [age - 2, age, 55, 57, 60, 62, 65, 67] if 50 <= a <= 70})
        comp = comparer_ages(regime=input.regime(), annee_liquidation=int(input.annee_liq()),
                             carriere=carriere, duree_assurance_annees=duree, age_base=age,
                             ages=ages, options=options)
        df = pd.DataFrame([{
            "Âge de départ": l["age"],
            "Durée (ans)": l["duree_annees"],
            "Taux": _fmt(l["taux"], "%"),
            "Droit ouvert": "oui" if l["eligible"] else "non",
            "Pension (DT/an)": _fmt(l["pension"], "DT"),
            "Pension (DT/mois)": _fmt((l["pension"] or 0) / 12.0, "DT"),
        } for l in comp])
        return render.DataGrid(df, width="100%")

    @render.data_frame
    def details():
        statut, contenu, carriere, _duree, _opt = resultat()
        if statut != "ok":
            return render.DataGrid(pd.DataFrame({"Info": ["Aucun calcul"]}))
        lignes = details_par_periode(regime=input.regime(), carriere=carriere,
                                     annee_liquidation=int(input.annee_liq()), resultats=contenu)
        df = pd.DataFrame([{
            "Variable": l["variable"], "Libellé": l["libelle"],
            "Période": l["periode"], "Valeur": _fmt(l["valeur"], l["unite"]),
        } for l in lignes])
        return render.DataGrid(df, width="100%", height="420px")


app = App(app_ui, server)
