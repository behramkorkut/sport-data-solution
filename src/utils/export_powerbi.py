
"""
Export des données pour Power BI.
Génère les fichiers CSV nécessaires au dashboard.
"""

import pandas as pd
from src.utils.database import engine


def export_all():
    """Exporte toutes les tables utiles en CSV pour Power BI."""

    exports = {
        "salaries": "SELECT * FROM salaries",
        "sports_pratiques": "SELECT * FROM sports_pratiques",
        "activites": "SELECT * FROM activites",
        "avantages_salaries": "SELECT * FROM avantages_salaries",
        "avantages_par_bu": "SELECT * FROM avantages_par_bu",
        "validation_distances": "SELECT * FROM validation_distances",
    }

    # Vue enrichie : activités avec noms des salariés
    exports["activites_enrichies"] = """
        SELECT
            a.id,
            a.id_salarie,
            s.nom,
            s.prenom,
            s.bu,
            a.date_debut,
            a.sport_type,
            a.distance_m,
            a.temps_ecoule_s,
            a.commentaire,
            EXTRACT(MONTH FROM a.date_debut) AS mois,
            EXTRACT(YEAR FROM a.date_debut) AS annee,
            CASE WHEN a.distance_m IS NOT NULL
                 THEN ROUND(CAST(a.distance_m / 1000.0 AS numeric), 2)
                 ELSE NULL END AS distance_km,
            CASE WHEN a.temps_ecoule_s IS NOT NULL
                 THEN ROUND(CAST(a.temps_ecoule_s / 60.0 AS numeric), 1)
                 ELSE NULL END AS duree_min
        FROM activites a
        JOIN salaries s ON a.id_salarie = s.id_salarie
        ORDER BY a.date_debut
    """

    # Vue résumé par salarié
    exports["resume_par_salarie"] = """
        SELECT
            s.id_salarie,
            s.nom,
            s.prenom,
            s.bu,
            s.type_contrat,
            s.salaire_brut,
            s.moyen_deplacement,
            sp.sport AS sport_declare,
            av.eligible_prime,
            av.montant_prime,
            av.nb_activites,
            av.eligible_bienetre,
            av.jours_bienetre,
            vd.distance_km AS distance_domicile_km,
            vd.is_valid AS distance_valide
        FROM salaries s
        LEFT JOIN sports_pratiques sp ON s.id_salarie = sp.id_salarie
        LEFT JOIN avantages_salaries av ON s.id_salarie = av.id_salarie
        LEFT JOIN validation_distances vd ON s.id_salarie = vd.id_salarie
        ORDER BY s.nom, s.prenom
    """

    print("Export des données pour Power BI...")
    print("=" * 50)

    for name, query in exports.items():
        df = pd.read_sql(query, engine)
        filepath = f"dashboards/{name}.csv"
        df.to_csv(filepath, index=False, encoding="utf-8-sig")
        print(f"  ✓ {filepath} ({len(df)} lignes)")

    print("=" * 50)
    print("Export terminé ! Les fichiers sont dans le dossier 'dashboards/'")


if __name__ == "__main__":
    export_all()
