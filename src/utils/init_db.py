"""
Initialisation de la base de données — Création des tables.
"""

from src.utils.database import engine, Base


def init_database():
    """Crée toutes les tables dans la base de données."""
    print("Création des tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables créées avec succès !")

    # Affiche les tables créées
    for table_name in Base.metadata.tables:
        print(f"  ✓ {table_name}")


if __name__ == "__main__":
    init_database()
