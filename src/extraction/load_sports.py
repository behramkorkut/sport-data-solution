"""
Extraction et chargement des données sportives depuis le fichier Excel (local ou S3).
"""

import pandas as pd
import numpy as np

from src.utils.database import engine

# URL source S3 (OpenClassrooms)
SOURCE_URL = "https://s3.eu-west-1.amazonaws.com/course.oc-static.com/projects/922_Data+Engineer/1039_P12/Donne%CC%81es+Sportive.xlsx"
LOCAL_PATH = "data/raw/Donnees_Sportive.xlsx"


def load_donnees_sportives(filepath: str = None) -> int:
    """
    Lit le fichier Excel des sports et charge les données dans la table sports_pratiques.
    Tente d'abord la source S3, sinon utilise le fichier local.
    Retourne le nombre de lignes chargées.
    """
    source = filepath or LOCAL_PATH

    try:
        print("Tentative de lecture depuis S3...")
        df = pd.read_excel(SOURCE_URL, engine="openpyxl")
        print("✓ Données lues depuis S3")
    except Exception as e:
        print(f"⚠ S3 indisponible ({e}), lecture locale : {source}")
        df = pd.read_excel(source, engine="openpyxl")

    print(f"Colonnes détectées : {list(df.columns)}")
    print(f"Nombre de lignes : {len(df)}")

    # Renommer les colonnes
    column_mapping = {
        "ID salarié": "id_salarie",
        "Pratique d'un sport": "sport",
    }
    df = df.rename(columns=column_mapping)

    # Remplacer les NaN par None (NULL en base)
    df["sport"] = df["sport"].replace({np.nan: None})

    # Statistiques rapides
    nb_sportifs = df["sport"].notna().sum()
    nb_non_sportifs = df["sport"].isna().sum()
    print(f"  Sportifs déclarés : {nb_sportifs}")
    print(f"  Sans sport déclaré : {nb_non_sportifs}")

    # Chargement dans PostgreSQL
    df.to_sql("sports_pratiques", engine, if_exists="append", index=False)

    print(f"✓ {len(df)} enregistrements chargés dans la table 'sports_pratiques'")
    return len(df)


if __name__ == "__main__":
    load_donnees_sportives()
