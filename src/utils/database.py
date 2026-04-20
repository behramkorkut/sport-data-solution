
"""
Configuration et connexion à la base de données PostgreSQL.
Compatible SQLAlchemy 1.4+ et 2.0+.
"""

import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Compatibilité SQLAlchemy 1.4 / 2.0
try:
    from sqlalchemy.orm import DeclarativeBase
    class Base(DeclarativeBase):
        pass
except ImportError:
    from sqlalchemy.orm import declarative_base
    Base = declarative_base()

# Lecture de la configuration
DB_USER = os.getenv("POSTGRES_USER", "sport_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "sport_secret_2026")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "sport_data")

# Choix du driver : psycopg (v3, local) ou psycopg2 (conteneur Airflow)
DRIVER = "psycopg2" if os.getenv("POSTGRES_HOST") == "postgres" else "psycopg"
DATABASE_URL = f"postgresql+{DRIVER}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)


def get_session():
    """Fournit une session de base de données."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_connection():
    """Teste la connexion à la base de données."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print(f"Connexion à PostgreSQL réussie ! (driver: {DRIVER})")
        return True
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return False


if __name__ == "__main__":
    test_connection()
