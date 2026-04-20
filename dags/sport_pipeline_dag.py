
"""
DAG Airflow — Pipeline Sport Data Solution
Orchestre l'ensemble du pipeline : extraction, génération, validation, calcul et notification.
"""

from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator

import sys
import os

# Ajouter le chemin du projet pour les imports
sys.path.insert(0, "/opt/airflow")


# ---- Fonctions des tâches ----

def task_load_rh(**kwargs):
    """Charge les données RH depuis le fichier Excel."""
    from src.extraction.load_rh import load_donnees_rh
    count = load_donnees_rh("data/raw/Donnee_RH.xlsx")
    return f"{count} salariés chargés"


def task_load_sports(**kwargs):
    """Charge les données sportives depuis le fichier Excel."""
    from src.extraction.load_sports import load_donnees_sportives
    count = load_donnees_sportives("data/raw/Donnees_Sportive.xlsx")
    return f"{count} sports chargés"


def task_generate_activities(**kwargs):
    """Génère les activités simulées sur 12 mois."""
    from src.generation.generate_activities import generate_all_activities
    count = generate_all_activities()
    return f"{count} activités générées"


def task_validate_distances(**kwargs):
    """Valide les distances domicile-entreprise via Google Maps."""
    from src.transformation.validate_distances import validate_all_distances
    df = validate_all_distances()
    nb_anomalies = (df["is_valid"] == False).sum() if df is not None else -1
    return f"Validation terminée - {nb_anomalies} anomalie(s)"


def task_compute_avantages(**kwargs):
    """Calcule les avantages sportifs (primes et journées bien-être)."""
    from src.transformation.compute_avantages import compute_avantages
    df = compute_avantages()
    return f"Avantages calculés pour {len(df)} salariés"


def task_notify_slack(**kwargs):
    """Envoie les 3 dernières activités sur Slack."""
    from src.notifications.slack_notifier import send_recent_activities
    send_recent_activities(3)
    return "Notifications Slack envoyées"


# ---- Définition du DAG ----

default_args = {
    "owner": "sport-data-solution",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="sport_data_pipeline",
    default_args=default_args,
    description="Pipeline complet Sport Data Solution — POC Avantages Sportifs",
    schedule=None,  # Déclenchement manuel pour le POC
    start_date=datetime(2025, 4, 20),
    catchup=False,
    tags=["sport", "poc", "etl"],
) as dag:

    # Tâche 1 : Charger les données RH
    t_load_rh = PythonOperator(
        task_id="load_donnees_rh",
        python_callable=task_load_rh,
    )

    # Tâche 2 : Charger les données sportives
    t_load_sports = PythonOperator(
        task_id="load_donnees_sportives",
        python_callable=task_load_sports,
    )

    # Tâche 3 : Générer les activités simulées
    t_generate = PythonOperator(
        task_id="generate_activities",
        python_callable=task_generate_activities,
    )

    # Tâche 4 : Valider les distances Google Maps
    t_validate = PythonOperator(
        task_id="validate_distances",
        python_callable=task_validate_distances,
    )

    # Tâche 5 : Calculer les avantages
    t_compute = PythonOperator(
        task_id="compute_avantages",
        python_callable=task_compute_avantages,
    )

    # Tâche 6 : Tests de qualité Soda
    t_soda = BashOperator(
        task_id="run_soda_tests",
        bash_command="cd /opt/airflow && soda scan -d sport_data -c tests/soda/configuration.yml tests/soda/checks.yml",
    )

    # Tâche 7 : Notifications Slack
    t_slack = PythonOperator(
        task_id="notify_slack",
        python_callable=task_notify_slack,
    )

    # ---- Dépendances ----
    # Les données RH doivent être chargées avant les sports (clé étrangère)
    t_load_rh >> t_load_sports >> t_generate >> t_validate >> t_compute >> t_soda >> t_slack

