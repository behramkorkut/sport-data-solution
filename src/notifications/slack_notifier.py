
"""
Notification Slack — Envoie un message pour chaque nouvelle activité sportive.
Génère des messages motivants comme demandé dans la note de cadrage.
"""

import os
import random

import requests
import pandas as pd
from dotenv import load_dotenv

from src.utils.database import engine

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

# Templates de messages par type de sport
MESSAGE_TEMPLATES = {
    "Course à pied": [
        "Bravo {prenom} {nom} ! Tu viens de courir {distance_km} km en {duree} ! Quelle énergie ! 🔥🏅",
        "Superbe run {prenom} {nom} ! {distance_km} km avalés en {duree} ! Continue comme ça ! 🏃‍♂️💪",
        "{prenom} {nom} enchaîne avec {distance_km} km en {duree} ! Rien ne t'arrête ! 🚀",
    ],
    "Randonnée": [
        "Magnifique {prenom} {nom} ! Une randonnée de {distance_km} km terminée et un nouveau spot à découvrir ! 🌄 {commentaire} 🏕",
        "Belle rando pour {prenom} {nom} ! {distance_km} km de pure nature ! 🥾🌿 {commentaire}",
        "{prenom} {nom} a parcouru {distance_km} km en randonnée ! Les jambes sont solides ! ⛰️ {commentaire}",
    ],
    "Tennis": [
        "Beau match pour {prenom} {nom} ! {duree} sur le court aujourd'hui ! 🎾🔥",
        "{prenom} {nom} a passé {duree} sur les courts ! Le revers s'affine ! 🎾💪",
    ],
    "Football": [
        "Gros match pour {prenom} {nom} ! {distance_km} km parcourus sur le terrain ! ⚽🔥",
        "{prenom} {nom} a tout donné sur le terrain ! {duree} de jeu intense ! ⚽💪",
    ],
    "Natation": [
        "Splendide {prenom} {nom} ! {distance_km} km dans l'eau en {duree} ! 🏊‍♂️💦",
        "{prenom} {nom} a nagé {distance_km} km ! Quelle endurance aquatique ! 🌊🏅",
    ],
    "Badminton": [
        "{prenom} {nom} a smashé pendant {duree} ! Belle session de badminton ! 🏸💥",
        "Super séance de bad pour {prenom} {nom} ! {duree} d'échanges intenses ! 🏸🔥",
    ],
    "Escalade": [
        "{prenom} {nom} a grimpé pendant {duree} ! Toujours plus haut ! 🧗‍♂️🏔️",
        "Belle session d'escalade pour {prenom} {nom} ! {duree} de grimpe ! 💪🪨",
    ],
    "Voile": [
        "{prenom} {nom} a navigué {distance_km} km ! Le vent était au rendez-vous ! ⛵🌊",
        "Belle sortie en mer pour {prenom} {nom} ! {distance_km} km parcourus ! 🚤💨",
    ],
    "Triathlon": [
        "Incroyable {prenom} {nom} ! {distance_km} km en triathlon en {duree} ! Tu es une machine ! 🏊‍♂️🚴🏃‍♂️🏅",
        "{prenom} {nom} a bouclé un triathlon de {distance_km} km ! Respect total ! 💪🔥",
    ],
    "Basketball": [
        "{prenom} {nom} a joué {duree} de basket ! Quel dunk ! 🏀🔥",
        "Belle session de basket pour {prenom} {nom} ! {duree} sur le parquet ! 🏀💪",
    ],
    "Boxe": [
        "{prenom} {nom} a boxé pendant {duree} ! K.O. technique ! 🥊🔥",
        "Session de boxe intense pour {prenom} {nom} ! {duree} de combat ! 🥊💪",
    ],
    "Judo": [
        "{prenom} {nom} a pratiqué le judo pendant {duree} ! Ippon ! 🥋🔥",
        "Belle séance de judo pour {prenom} {nom} ! {duree} sur le tatami ! 🥋💪",
    ],
    "Rugby": [
        "{prenom} {nom} a tout donné au rugby ! {distance_km} km parcourus en {duree} ! 🏉💪",
        "Gros match de rugby pour {prenom} {nom} ! {duree} d'engagement total ! 🏉🔥",
    ],
    "Tennis de table": [
        "{prenom} {nom} a joué au ping-pong pendant {duree} ! Smash ! 🏓🔥",
        "Belle session de tennis de table pour {prenom} {nom} ! {duree} d'échanges ! 🏓💪",
    ],
    "Équitation": [
        "{prenom} {nom} a chevauché {distance_km} km ! Belle balade à cheval ! 🐴🌿",
        "Superbe sortie équestre pour {prenom} {nom} ! {distance_km} km parcourus ! 🏇💨",
    ],
}


def format_duration(seconds: int) -> str:
    """Formate une durée en secondes vers un format lisible."""
    if seconds is None:
        return "un bon moment"
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours}h{minutes:02d}"
    return f"{minutes} min"


def build_slack_message(activity: dict) -> str:
    """Construit le message Slack pour une activité."""
    sport_type = activity["sport_type"]
    templates = MESSAGE_TEMPLATES.get(sport_type, ["{prenom} {nom} a fait du {sport_type} ! 💪🔥"])

    template = random.choice(templates)

    distance_km = ""
    if activity.get("distance_m") and pd.notna(activity["distance_m"]):
        distance_km = f"{activity['distance_m'] / 1000:.1f}"

    duree = format_duration(activity.get("temps_ecoule_s"))

    commentaire = ""
    if activity.get("commentaire") and pd.notna(activity["commentaire"]):
        commentaire = f'("{activity["commentaire"]}")'

    message = template.format(
        prenom=activity["prenom"],
        nom=activity["nom"],
        distance_km=distance_km,
        duree=duree,
        commentaire=commentaire,
        sport_type=sport_type,
    )

    return message


def send_slack_message(message: str) -> bool:
    """Envoie un message via le webhook Slack."""
    if not SLACK_WEBHOOK_URL:
        print("⚠ SLACK_WEBHOOK_URL non définie")
        return False

    payload = {"text": message}

    try:
        response = requests.post(SLACK_WEBHOOK_URL, json=payload, timeout=10)
        return response.status_code == 200
    except Exception as e:
        print(f"Erreur Slack : {e}")
        return False


def send_recent_activities(limit: int = 5):
    """
    Envoie les N dernières activités sur Slack.
    Utilisé pour la démonstration live.
    """
    query = """
        SELECT a.*, s.nom, s.prenom
        FROM activites a
        JOIN salaries s ON a.id_salarie = s.id_salarie
        ORDER BY a.date_debut DESC
        LIMIT %(limit)s
    """
    df = pd.read_sql(query, engine, params={"limit": limit})

    print(f"Envoi de {len(df)} activités sur Slack...")

    for _, activity in df.iterrows():
        message = build_slack_message(activity.to_dict())
        success = send_slack_message(message)
        status = "✓" if success else "✗"
        print(f"  {status} {activity['prenom']} {activity['nom']} - {activity['sport_type']}")

    print("Terminé !")


if __name__ == "__main__":
    send_recent_activities(5)

