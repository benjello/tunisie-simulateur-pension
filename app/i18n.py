"""Traductions FR/AR du simulateur de pension (socle i18n).

Mécanique `t(cle, lang)` + sélecteur de langue + RTL : voir
`docs/notes/i18n-cablage.md`. Ce module porte les libellés ; le câblage dans
`app.py` (sélecteur, RTL, `ui.update_*`, sorties dynamiques) reste à faire.

Les clés reprennent les libellés en dur de `app.py` : pour internationaliser,
remplacer chaque chaîne littérale par `t("cle", lang)`.
"""

from __future__ import annotations

LANGUES = {"fr": "Français", "ar": "العربية"}

TRADUCTIONS: dict[str, dict[str, str]] = {
    # — Général / titres —
    "titre_app": {"fr": "Simulateur de pension — Tunisie", "ar": "محاكي جراية التقاعد — تونس"},
    "langue": {"fr": "Langue", "ar": "اللغة"},
    "ma_situation": {"fr": "Ma situation", "ar": "وضعيتي"},
    "options_facultatives": {
        "fr": "Options facultatives — n'ouvrez une rubrique que si elle vous concerne.",
        "ar": "خيارات اختيارية — لا تفتح قسماً إلّا إن كان يعنيك."},

    # — Régimes —
    "regime": {"fr": "Dans quel régime cotisez-vous ?", "ar": "في أيّ نظام تساهم؟"},
    "regime_rsna": {"fr": "Privé non agricole (CNSS — RSNA)",
                    "ar": "القطاع الخاص غير الفلاحي (الصندوق الوطني للضمان الاجتماعي)"},
    "regime_cnrps": {"fr": "Secteur public (CNRPS)",
                     "ar": "القطاع العام (الصندوق الوطني للتقاعد والحيطة الاجتماعية)"},

    # — Situation de base —
    "naissance": {"fr": "Votre date de naissance", "ar": "تاريخ ولادتك"},
    "annee_liq": {"fr": "Année de départ à la retraite", "ar": "سنة الإحالة على التقاعد"},
    "mode": {"fr": "Comment décrire vos revenus ?", "ar": "كيف تصف مداخيلك؟"},
    "mode_simple": {"fr": "Salaire moyen (simple)", "ar": "أجر متوسّط (مبسّط)"},
    "mode_avance": {"fr": "Carrière année par année", "ar": "المسار المهني سنة بسنة"},
    "salaire_mensuel": {"fr": "Votre salaire mensuel actuel (DT)", "ar": "أجرك الشهري الحالي (دينار)"},
    "duree": {"fr": "Combien d'années avez-vous cotisé ?", "ar": "كم سنة ساهمت؟"},
    "nb_annees": {"fr": "Nombre d'années de carrière", "ar": "عدد سنوات المسار المهني"},
    "salaire_init": {"fr": "Salaire annuel de départ (DT)", "ar": "الأجر السنوي عند الانطلاق (دينار)"},
    "generer": {"fr": "Générer la grille de carrière", "ar": "إنشاء جدول المسار المهني"},
    "aide_grille": {"fr": "Éditez ensuite le salaire et les trimestres année par année dans le tableau à droite.",
                    "ar": "ثمّ عدّل الأجر والثلاثيات سنة بسنة في الجدول على اليمين."},
    "calculer": {"fr": "Calculer ma pension", "ar": "احسب جرايتي"},

    # — Options CNRPS —
    "acc_cnrps": {"fr": "Secteur public (CNRPS) : bonifications, départ anticipé…",
                  "ar": "القطاع العام: التدعيمات، الإحالة المبكرة على التقاعد…"},
    "cnrps_only": {"fr": "Ces options concernent le régime CNRPS (secteur public). "
                         "Choisissez CNRPS ci-dessus pour les renseigner.",
                   "ar": "تخصّ هذه الخيارات نظام القطاع العام. اختر هذا النظام أعلاه لتعبئتها."},
    "cadre_actif": {"fr": "Années de service en cadre actif", "ar": "سنوات الخدمة في السلك الفعلي"},
    "militaire": {"fr": "Années de service militaire", "ar": "سنوات الخدمة العسكرية"},
    "cnss_annees": {"fr": "Années aussi cotisées à la CNSS (carrière mixte)",
                    "ar": "سنوات المساهمة أيضاً في الضمان الاجتماعي (مسار مختلط)"},
    "mere3": {"fr": "Êtes-vous mère de 3 enfants ?", "ar": "هل أنت أمّ لثلاثة أبناء؟"},
    "astreignant": {"fr": "Fonction astreignante ?", "ar": "وظيفة شاقّة؟"},
    "sur_demande": {"fr": "Départ anticipé sur demande ?", "ar": "إحالة مبكرة بطلب؟"},
    "invalidite": {"fr": "Invalidité physique ?", "ar": "عجز بدني؟"},
    "nb_enfants": {"fr": "Enfants à charge", "ar": "الأبناء المكفولون"},
    "conjoint_sans_revenu": {"fr": "Conjoint sans revenu ?", "ar": "القرين دون دخل؟"},

    # — Survivants / objectif —
    "acc_survivants": {"fr": "En cas de décès : pensions de survivants",
                       "ar": "في صورة الوفاة: جرايات الباقين على قيد الحياة"},
    "conjoint_survivant": {"fr": "Avez-vous un conjoint survivant ?", "ar": "هل لديك قرين باقٍ على قيد الحياة؟"},
    "nb_orphelins": {"fr": "Nombre d'enfants orphelins", "ar": "عدد الأبناء اليتامى"},
    "acc_objectif": {"fr": "Aller plus loin : objectif de pension", "ar": "لمزيد التعمّق: جراية مستهدفة"},
    "pension_cible": {"fr": "Quelle pension mensuelle visez-vous ? (DT, 0 = ignorer)",
                      "ar": "ما الجراية الشهرية التي تستهدفها؟ (دينار، 0 = تجاهل)"},

    # — En-tête / base légale —
    "ne_en": {"fr": "né en", "ar": "من مواليد"},
    "liquidation": {"fr": "liquidation", "ar": "التصفية"},
    "age": {"fr": "âge", "ar": "السنّ"},
    "ans": {"fr": "ans", "ar": "سنة"},
    "base_legale": {"fr": "Base légale", "ar": "السند القانوني"},

    # — Résultat —
    "resultat": {"fr": "Résultat", "ar": "النتيجة"},
    "salaire_de_reference": {"fr": "Salaire de référence (annuel)", "ar": "الأجر المرجعي (سنوي)"},
    "taux_de_liquidation": {"fr": "Taux de liquidation", "ar": "نسبة التصفية"},
    "pension_brute": {"fr": "Pension brute (annuelle)", "ar": "الجراية الخام (سنوية)"},
    "pension_minimale": {"fr": "Pension minimale garantie (annuelle)", "ar": "الجراية الدنيا المضمونة (سنوية)"},
    "pension": {"fr": "Pension servie (annuelle)", "ar": "الجراية المصروفة (سنوية)"},
    "pension_mensuelle": {"fr": "Pension servie (mensuelle, ÷12)", "ar": "الجراية المصروفة (شهرية، ÷12)"},
    "eligible": {"fr": "Droit ouvert (éligibilité)", "ar": "الحقّ مفتوح (الاستحقاق)"},
    "tr_brut": {"fr": "Taux de remplacement brut (pension / dernier salaire)",
                "ar": "نسبة التعويض الخام (الجراية / آخر أجر)"},
    "irpp": {"fr": "IRPP (abattement pension 25 %)", "ar": "الضريبة على الدخل (طرح 25٪ على الجراية)"},
    "css": {"fr": "CSS (contribution solidarité)", "ar": "المساهمة الاجتماعية التضامنية"},
    "pension_nette": {"fr": "Pension NETTE (annuelle)", "ar": "الجراية الصافية (سنوية)"},
    "pension_nette_mensuelle": {"fr": "Pension NETTE (mensuelle, ÷12)", "ar": "الجراية الصافية (شهرية، ÷12)"},
    "tr_net": {"fr": "Taux de remplacement NET", "ar": "نسبة التعويض الصافية"},
    "droit_non_ouvert": {
        "fr": "Droit non ouvert : durée d'assurance ou âge insuffisants "
              "(RSNA : 10 ans et 60 ans ; CNRPS : 15 ans et 62 ans, sauf départ anticipé).",
        "ar": "الحقّ غير مفتوح: مدّة التأمين أو السنّ غير كافية "
              "(القطاع الخاص: 10 سنوات و60 سنة؛ القطاع العام: 15 سنة و62 سنة، إلّا في الإحالة المبكرة)."},

    # — Compléments CNRPS —
    "complements_cnrps": {"fr": "Compléments CNRPS", "ar": "ملحقات القطاع العام"},
    "age_requis": {"fr": "Âge requis pour le départ", "ar": "السنّ المطلوبة للإحالة"},
    "duree_requise_annees": {"fr": "Durée requise (années)", "ar": "المدّة المطلوبة (سنوات)"},
    "bonifications": {"fr": "Bonifications (trimestres)", "ar": "التدعيمات (ثلاثيات)"},
    "duree_assurance": {"fr": "Durée d'assurance totale (trimestres)", "ar": "مدّة التأمين الجملية (ثلاثيات)"},
    "indemnites_familiales": {"fr": "Indemnités familiales (mensuel)", "ar": "المنح العائلية (شهري)"},
    "indemnite_revenu_unique": {"fr": "Indemnité de revenu unique (mensuel)", "ar": "منحة الدخل الوحيد (شهري)"},

    # — Survivants (sortie) —
    "survivants_titre": {"fr": "Survivants (en cas de décès de l'assuré)",
                         "ar": "الباقون على قيد الحياة (في صورة وفاة المؤمَّن)"},
    "pension_de_reversion": {"fr": "Pension de réversion du conjoint (mensuel)",
                             "ar": "الجراية المنقولة للقرين (شهري)"},
    "pension_orphelins": {"fr": "Pensions d'orphelins — total (mensuel)", "ar": "جرايات اليتامى — المجموع (شهري)"},
    "survivants_note": {"fr": "Calculé sur la pension simulée comme pension de référence du défunt.",
                        "ar": "محسوب على الجراية المقدّرة باعتبارها الجراية المرجعية للمتوفّى."},

    # — Objectif inverse —
    "objectif_atteignable": {"fr": "Pour une pension de {cible} DT/mois, il faut {duree} ans d'assurance "
                                   "(vs {actuel} actuellement), à salaire constant.",
                             "ar": "لجراية بـ{cible} دينار/شهر، تلزم {duree} سنة تأمين "
                                   "(مقابل {actuel} حالياً)، بأجر ثابت."},
    "objectif_non_atteignable": {"fr": "La cible de {cible} DT/mois n'est pas atteignable à ce salaire "
                                       "(max ≈ {max} DT/mois à {duree} ans).",
                                 "ar": "الهدف {cible} دينار/شهر غير قابل للتحقيق بهذا الأجر "
                                       "(أقصى ≈ {max} دينار/شهر عند {duree} سنة)."},

    # — Comparaison des âges —
    "comparaison_titre": {"fr": "Comparaison selon l'âge de départ (hypothèse : travail jusqu'à l'âge testé)",
                          "ar": "مقارنة حسب سنّ الإحالة (بافتراض العمل حتى السنّ المختبَرة)"},
    "graphe_titre": {"fr": "Pension mensuelle selon l'âge de départ", "ar": "الجراية الشهرية حسب سنّ الإحالة"},
    "col_age": {"fr": "Âge de départ", "ar": "سنّ الإحالة"},
    "col_duree": {"fr": "Durée (ans)", "ar": "المدّة (سنوات)"},
    "col_taux": {"fr": "Taux", "ar": "النسبة"},
    "col_droit": {"fr": "Droit ouvert", "ar": "الحقّ مفتوح"},
    "col_pension_an": {"fr": "Pension (DT/an)", "ar": "الجراية (دينار/سنة)"},
    "col_pension_mois": {"fr": "Pension (DT/mois)", "ar": "الجراية (دينار/شهر)"},
    "oui": {"fr": "oui", "ar": "نعم"},
    "non": {"fr": "non", "ar": "لا"},

    # — Détails —
    "details_titre": {"fr": "Détails par période (toutes les variables pertinentes)",
                      "ar": "التفاصيل حسب الفترة (كلّ المتغيّرات المعنيّة)"},
    "col_variable": {"fr": "Variable", "ar": "المتغيّر"},
    "col_libelle": {"fr": "Libellé", "ar": "التسمية"},
    "col_periode": {"fr": "Période", "ar": "الفترة"},
    "col_valeur": {"fr": "Valeur", "ar": "القيمة"},

    # — Note de bas de page —
    "note_moteur": {
        "fr": "Calculé par le moteur OpenFisca-Tunisia (package pension). Montants "
              "annuels (DT/an) sauf mention. Le droit fait référence.",
        "ar": "محسوب بمحرّك OpenFisca-Tunisia (حزمة الجرايات). المبالغ سنوية (دينار/سنة) "
              "ما لم يُذكر خلاف ذلك. القانون هو المرجع."},
}


def t(cle: str, lang: str = "fr") -> str:
    """Traduction de `cle` pour `lang` (repli fr, puis la clé)."""
    entree = TRADUCTIONS.get(cle)
    if entree is None:
        return cle
    return entree.get(lang) or entree.get("fr") or cle
