"""
Extraction et chargement des données RH depuis le fichier Excel (local ou S3).
"""

import pandas as pd
from sqlalchemy import text

from src.utils.database import engine

# URL source S3 (OpenClassrooms)
SOURCE_URL = "https://s3.eu-west-1.amazonaws.com/course.oc-static.com/projects/922_Data+Engineer/1039_P12/Donne%CC%81es+RH.xlsx"
LOCAL_PATH = "data/raw/Donnee_RH.xlsx"


def load_donnees_rh(filepath: str = None) -> int:
    """
    Lit le fichier Excel RH et charge les données dans la table salaries.
    Tente d'abord la source S3, sinon utilise le fichier local.
    Retourne le nombre de lignes chargées.
    """
    source = filepath or LOCAL_PATH

    # Tenter le chargement depuis S3 d'abord
    try:
        print("Tentative de lecture depuis S3...")
        df = pd.read_excel(SOURCE_URL, engine="openpyxl")
        print("✓ Données lues depuis S3")
    except Exception as e:
        print(f"⚠ S3 indisponible ({e}), lecture locale : {source}")
        df = pd.read_excel(source, engine="openpyxl")

    print(f"Colonnes détectées : {list(df.columns)}")
    print(f"Nombre de lignes : {len(df)}")

    # Renommer les colonnes pour correspondre au modèle de données
    column_mapping = {
        "ID salarié": "id_salarie",
        "Nom": "nom",
        "Prénom": "prenom",
        "Date de naissance": "date_naissance",
        "BU": "bu",
        "Date d'embauche": "date_embauche",
        "Salaire brut": "salaire_brut",
        "Type de contrat": "type_contrat",
        "Nombre de jours de CP": "nb_jours_cp",
        "Adresse du domicile": "adresse_domicile",
        "Moyen de déplacement": "moyen_deplacement",
    }
    df = df.rename(columns=column_mapping)

    # Conversion des dates
    df["date_naissance"] = pd.to_datetime(df["date_naissance"]).dt.date
    df["date_embauche"] = pd.to_datetime(df["date_embauche"]).dt.date

    # Vider les tables avant rechargement (si elles contiennent des données)
    with engine.begin() as conn:
        for table in ["activites", "sports_pratiques", "salaries"]:
            conn.execute(text(f"DELETE FROM {table}"))

    df.to_sql("salaries", engine, if_exists="append", index=False)

    print(f"✓ {len(df)} salariés chargés dans la table 'salaries'")
    return len(df)


if __name__ == "__main__":
    load_donnees_rh()
