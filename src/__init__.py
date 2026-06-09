"""Initialisation du package ``src``.

Charge le fichier ``.env`` situé à la racine du projet AVANT l'import de
tout sous-module, via un chemin ABSOLU — donc indépendant du répertoire
d'exécution (terminal, ``uv run``, VSCode, conteneur Airflow).

Note : ``load_dotenv`` n'écrase pas les variables déjà présentes dans
l'environnement (override=False). C'est volontaire : le conteneur Airflow
impose ``POSTGRES_HOST=postgres`` et doit garder la priorité.
"""

from pathlib import Path

from dotenv import load_dotenv

_ENV_PATH = Path(__file__).resolve().parents[1] / ".env"
load_dotenv(_ENV_PATH)
