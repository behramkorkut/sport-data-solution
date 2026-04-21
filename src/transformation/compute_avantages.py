"""
Calcul des avantages sportifs pour chaque salarié.
- Prime sportive : 5% du salaire brut si déplacement sportif validé
- 5 journées bien-être : si >= 15 activités physiques sur 12 mois
"""

import pandas as pd

from src.utils.database import engine

SEUIL_ACTIVITES = 15
TAUX_PRIME = 0.05


def compute_avantages():
    """Calcule les avantages pour tous les salariés et sauvegarde les résultats."""

    # ---- 1. Prime sportive ----
    print("=" * 60)
    print("CALCUL DE LA PRIME SPORTIVE (5% salaire brut)")
    print("=" * 60)

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
    df_prime = pd.read_sql(query_prime, engine)

    # Éligibilité prime : déplacement sportif ET distance validée
    modes_sportifs = ["Marche/running", "Vélo/Trottinette/Autres"]
    df_prime["eligible_prime"] = df_prime["moyen_deplacement"].isin(modes_sportifs) & (
        df_prime["is_valid"].astype(bool)
    )
    df_prime["montant_prime"] = df_prime.apply(
        lambda row: (
            round(row["salaire_brut"] * TAUX_PRIME, 2) if row["eligible_prime"] else 0
        ),
        axis=1,
    )

    nb_eligible_prime = df_prime["eligible_prime"].sum()
    cout_total_prime = df_prime["montant_prime"].sum()

    print(f"  Salariés éligibles : {nb_eligible_prime} / {len(df_prime)}")
    print(f"  Coût total primes  : {cout_total_prime:,.2f} €")
    print(
        f"  Prime moyenne      : {cout_total_prime / nb_eligible_prime:,.2f} €"
        if nb_eligible_prime > 0
        else ""
    )

    # ---- 2. Journées bien-être ----
    print()
    print("=" * 60)
    print("CALCUL DES JOURNÉES BIEN-ÊTRE (5 jours si >= 15 activités)")
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
    df_bienetre["eligible_bienetre"] = df_bienetre["nb_activites"] >= SEUIL_ACTIVITES
    df_bienetre["jours_bienetre"] = df_bienetre["eligible_bienetre"].apply(
        lambda x: 5 if x else 0
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
            f"Prime: {int(row['eligible_prime']):2d} élig. ({row['cout_primes']:>10,.2f} €) | "
            f"Bien-être: {int(row['eligible_bienetre']):2d} élig. ({int(row['total_jours_bienetre']):3d} jours)"
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
