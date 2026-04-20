
"""
Validation des distances domicile-entreprise via l'API Google Maps.
Vérifie la cohérence entre le mode de déplacement déclaré et la distance réelle.
"""

import os
import time

import googlemaps
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import text

from src.utils.database import engine

# Charger les variables d'environnement
load_dotenv()

# Configuration
ADRESSE_ENTREPRISE = "1362 Avenue des Platanes, 34970 Lattes"
API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")

# Règles de distance maximale (en km)
REGLES_DISTANCE = {
    "Marche/running": 15,
    "Vélo/Trottinette/Autres": 25,
}

# Modes Google Maps correspondants
MODES_GOOGLE = {
    "Marche/running": "walking",
    "Vélo/Trottinette/Autres": "bicycling",
}


def get_distance_km(gmaps_client, origin: str, destination: str, mode: str) -> dict:
    """
    Calcule la distance entre deux adresses via Google Maps Distance Matrix API.
    Retourne un dict avec distance_km, duree_min et le statut.
    """
    try:
        result = gmaps_client.distance_matrix(
            origins=[origin],
            destinations=[destination],
            mode=mode,
            language="fr",
        )

        element = result["rows"][0]["elements"][0]
        status = element["status"]

        if status == "OK":
            distance_km = round(element["distance"]["value"] / 1000, 2)
            duree_min = round(element["duration"]["value"] / 60, 1)
            return {
                "status": "OK",
                "distance_km": distance_km,
                "duree_min": duree_min,
            }
        else:
            return {"status": status, "distance_km": None, "duree_min": None}

    except Exception as e:
        return {"status": f"ERREUR: {str(e)}", "distance_km": None, "duree_min": None}


def validate_all_distances():
    """
    Valide les distances pour tous les salariés ayant un mode de déplacement sportif.
    """
    if not API_KEY:
        print("ERREUR : GOOGLE_MAPS_API_KEY non définie dans .env")
        return

    gmaps = googlemaps.Client(key=API_KEY)

    # Récupérer les salariés avec un déplacement sportif
    query = """
        SELECT id_salarie, nom, prenom, adresse_domicile, moyen_deplacement
        FROM salaries
        WHERE moyen_deplacement IN ('Marche/running', 'Vélo/Trottinette/Autres')
        ORDER BY id_salarie
    """
    df = pd.read_sql(query, engine)
    print(f"Salariés avec déplacement sportif à valider : {len(df)}")

    results = []

    for idx, row in df.iterrows():
        id_salarie = row["id_salarie"]
        moyen = row["moyen_deplacement"]
        adresse = row["adresse_domicile"]
        mode_google = MODES_GOOGLE[moyen]
        distance_max = REGLES_DISTANCE[moyen]

        print(f"  [{idx + 1}/{len(df)}] {row['prenom']} {row['nom']} ({moyen})...", end=" ")

        result = get_distance_km(gmaps, adresse, ADRESSE_ENTREPRISE, mode_google)

        is_valid = None
        if result["distance_km"] is not None:
            is_valid = result["distance_km"] <= distance_max

        status_label = "✓" if is_valid else "✗ ANOMALIE" if is_valid is False else "? INCONNU"
        distance_str = f"{result['distance_km']} km" if result['distance_km'] else result['status']
        print(f"{distance_str} → {status_label}")

        results.append({
            "id_salarie": id_salarie,
            "nom": row["nom"],
            "prenom": row["prenom"],
            "adresse_domicile": adresse,
            "moyen_deplacement": moyen,
            "distance_km": result["distance_km"],
            "duree_min": result["duree_min"],
            "distance_max_km": distance_max,
            "is_valid": is_valid,
            "status_api": result["status"],
        })

        # Pause pour respecter les rate limits de l'API
        time.sleep(0.2)

    df_results = pd.DataFrame(results)

    # Sauvegarder les résultats dans PostgreSQL
    df_results.to_sql("validation_distances", engine, if_exists="replace", index=False)
    print(f"\n✓ Résultats sauvegardés dans la table 'validation_distances'")

    # Résumé
    nb_valides = df_results["is_valid"].sum()
    nb_anomalies = (~df_results["is_valid"]).sum() if df_results["is_valid"].notna().any() else 0
    nb_inconnus = df_results["is_valid"].isna().sum()

    print(f"\n{'='*60}")
    print(f"RÉSUMÉ DE LA VALIDATION")
    print(f"{'='*60}")
    print(f"  Total salariés vérifiés : {len(df_results)}")
    print(f"  ✓ Conformes            : {nb_valides}")
    print(f"  ✗ Anomalies détectées  : {nb_anomalies}")
    print(f"  ? Statut inconnu       : {nb_inconnus}")

    # Détail des anomalies
    anomalies = df_results[df_results["is_valid"] == False]
    if len(anomalies) > 0:
        print(f"\n{'='*60}")
        print(f"DÉTAIL DES ANOMALIES")
        print(f"{'='*60}")
        for _, a in anomalies.iterrows():
            print(f"  ✗ {a['prenom']} {a['nom']} (ID: {a['id_salarie']})")
            print(f"    Adresse : {a['adresse_domicile']}")
            print(f"    Mode : {a['moyen_deplacement']}")
            print(f"    Distance : {a['distance_km']} km (max autorisé : {a['distance_max_km']} km)")
            print()

    # Export CSV pour traçabilité
    df_results.to_csv("data/processed/validation_distances.csv", index=False)
    print("✓ Export CSV : data/processed/validation_distances.csv")

    return df_results


if __name__ == "__main__":
    validate_all_distances()

