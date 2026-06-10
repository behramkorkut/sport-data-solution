"""
Calcul des avantages sportifs pour chaque salarié.
- Prime sportive : 5% du salaire brut si déplacement sportif validé
- 5 journées bien-être : si >= 15 activités physiques sur 12 mois

La logique métier (éligibilité, montants) est centralisée dans
``src.transformation.avantages_rules`` — fonctions pures couvertes par
``tests/unit/test_avantages_rules.py``. Ce module ne fait que
l'orchestration I/O : lecture base, application des règles, sauvegarde.
"""

import pandas as pd
from sqlalchemy import text

from src.transformation.avantages_rules import (
    JOURS_BIENETRE,
    SEUIL_ACTIVITES,
    TAUX_PRIME,
    calcul_jours_bienetre,
    calcul_montant_prime,
    est_eligible_bienetre,
    est_eligible_prime,
)
from src.utils.database import engine


def table_exists(table_name: str) -> bool:
    """Vérifie si une table existe dans la base de données."""
    query = text(
        "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :t)"
    )
    with engine.connect() as conn:
        return conn.execute(query, {"t": table_name}).scalar()


def _to_nullable_bool(value):
    """Convertit une valeur pandas (NaN/None/bool/0/1) en True/False/None.

    Indispensable : ``NaN.astype(bool)`` vaut ``True`` en pandas, ce qui
    rendrait éligible un salarié dont la validation de distance a échoué.
    """
    if pd.isna(value):
        return None
    return bool(value)


def compute_avantages():
    """Calcule les avantages pour tous les salariés et sauvegarde les résultats."""

    # ---- 1. Prime sportive ----
    print("=" * 60)
    print(f"CALCUL DE LA PRIME SPORTIVE ({TAUX_PRIME:.0%} salaire brut)")
    print("=" * 60)

    # Vérifier si la table validation_distances existe
    has_validation = table_exists("validation_distances")

    if has_validation:
        query_prime = """
            SELECT
                s.id_salarie,
                s.nom,
                s.prenom,
                s.bu,
                s.salaire_brut,
                s.moyen_deplacement,
                s.type_contrat,
                v.distance_km,
                v.is_valid
            FROM salaries s
            LEFT JOIN validation_distances v ON s.id_salarie = v.id_salarie
        """
    else:
        print(
            "  ⚠ Table validation_distances absente — éligibilité basée "
            "sur le mode de déplacement uniquement"
        )
        query_prime = """
            SELECT
                s.id_salarie,
                s.nom,
                s.prenom,
                s.bu,
                s.salaire_brut,
                s.moyen_deplacement,
                s.type_contrat,
                NULL as distance_km,
                NULL as is_valid
            FROM salaries s
        """

    df_prime = pd.read_sql(query_prime, engine)

    # Éligibilité et montant : règles métier centralisées (avantages_rules)
    df_prime["eligible_prime"] = df_prime.apply(
        lambda row: est_eligible_prime(
            row["moyen_deplacement"],
            is_valid=_to_nullable_bool(row["is_valid"]),
        ),
        axis=1,
    )
    df_prime["montant_prime"] = df_prime.apply(
        lambda row: calcul_montant_prime(row["salaire_brut"], row["eligible_prime"]),
        axis=1,
    )

    # Visibilité : salariés sportifs dont la validation est inconnue (API en échec)
    if has_validation:
        nb_inconnus = df_prime[
            df_prime["eligible_prime"] & df_prime["is_valid"].isna()
        ].shape[0]
        if nb_inconnus > 0:
            print(
                f"  ⚠ {nb_inconnus} salarié(s) éligible(s) sans validation de "
                "distance (statut API inconnu) — à vérifier manuellement"
            )

    nb_eligible_prime = df_prime["eligible_prime"].sum()
    cout_total_prime = df_prime["montant_prime"].sum()

    print(f"  Salariés éligibles : {nb_eligible_prime} / {len(df_prime)}")
    print(f"  Coût total primes  : {cout_total_prime:,.2f} €")
    if nb_eligible_prime > 0:
        print(f"  Prime moyenne      : {cout_total_prime / nb_eligible_prime:,.2f} €")

    # ---- 2. Journées bien-être ----
    print()
    print("=" * 60)
    print(
        f"CALCUL DES JOURNÉES BIEN-ÊTRE "
        f"({JOURS_BIENETRE} jours si >= {SEUIL_ACTIVITES} activités)"
    )
    print("=" * 60)

    query_activites = """
        SELECT
            id_salarie,
            COUNT(*) as nb_activites
        FROM activites
        GROUP BY id_salarie
    """
    df_activites = pd.read_sql(query_activites, engine)

    # Jointure avec les salariés
    df_bienetre = pd.merge(
        df_prime[["id_salarie", "nom", "prenom", "bu", "type_contrat", "salaire_brut"]],
        df_activites,
        on="id_salarie",
        how="left",
    )
    df_bienetre["nb_activites"] = df_bienetre["nb_activites"].fillna(0).astype(int)
    df_bienetre["eligible_bienetre"] = df_bienetre["nb_activites"].apply(
        est_eligible_bienetre
    )
    df_bienetre["jours_bienetre"] = df_bienetre["eligible_bienetre"].apply(
        calcul_jours_bienetre
    )

    nb_eligible_bienetre = df_bienetre["eligible_bienetre"].sum()
    total_jours = df_bienetre["jours_bienetre"].sum()

    print(f"  Salariés éligibles   : {nb_eligible_bienetre} / {len(df_bienetre)}")
    print(f"  Total jours accordés : {total_jours}")

    # ---- 3. Tableau récapitulatif ----
    print()
    print("=" * 60)
    print("TABLEAU RÉCAPITULATIF")
    print("=" * 60)

    df_recap = pd.merge(
        df_prime[
            [
                "id_salarie",
                "nom",
                "prenom",
                "bu",
                "type_contrat",
                "salaire_brut",
                "moyen_deplacement",
                "eligible_prime",
                "montant_prime",
            ]
        ],
        df_bienetre[
            ["id_salarie", "nb_activites", "eligible_bienetre", "jours_bienetre"]
        ],
        on="id_salarie",
        how="left",
    )
    df_recap["nb_activites"] = df_recap["nb_activites"].fillna(0).astype(int)
    df_recap["eligible_bienetre"] = df_recap["eligible_bienetre"].fillna(False)
    df_recap["jours_bienetre"] = df_recap["jours_bienetre"].fillna(0).astype(int)

    # Sauvegarder en base
    df_recap.to_sql("avantages_salaries", engine, if_exists="replace", index=False)
    print(f"  ✓ Table 'avantages_salaries' créée ({len(df_recap)} lignes)")

    # Export CSV
    df_recap.to_csv("data/processed/avantages_salaries.csv", index=False)
    print("  ✓ Export CSV : data/processed/avantages_salaries.csv")

    # ---- 4. Résumé par BU ----
    print()
    print("=" * 60)
    print("IMPACT PAR BUSINESS UNIT")
    print("=" * 60)

    summary_bu = (
        df_recap.groupby("bu")
        .agg(
            nb_salaries=("id_salarie", "count"),
            eligible_prime=("eligible_prime", "sum"),
            cout_primes=("montant_prime", "sum"),
            eligible_bienetre=("eligible_bienetre", "sum"),
            total_jours_bienetre=("jours_bienetre", "sum"),
        )
        .reset_index()
    )

    summary_bu.to_sql("avantages_par_bu", engine, if_exists="replace", index=False)

    for _, row in summary_bu.iterrows():
        print(
            f"  {row['bu']:12s} | {int(row['nb_salaries']):3d} sal. | "
            f"Prime: {int(row['eligible_prime']):2d} élig. "
            f"({row['cout_primes']:>10,.2f} €) | "
            f"Bien-être: {int(row['eligible_bienetre']):2d} élig. "
            f"({int(row['total_jours_bienetre']):3d} jours)"
        )

    # ---- 5. Résumé global ----
    print()
    print("=" * 60)
    print("IMPACT FINANCIER GLOBAL")
    print("=" * 60)
    print(f"  Coût total primes sportives : {cout_total_prime:>12,.2f} €")
    print(f"  Total jours bien-être       : {total_jours:>12d} jours")
    print(f"  Nombre de salariés          : {len(df_recap):>12d}")

    return df_recap


if __name__ == "__main__":
    compute_avantages()
