"""
Script de démonstration live : insère une activité sportive
et envoie la notification Slack correspondante.
"""

import os
from datetime import datetime

import pandas as pd
import requests
from dotenv import load_dotenv
from sqlalchemy import text

from src.utils.database import engine

load_dotenv()

SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")
ENTREPRISE = "Sport Data Solution"


def insert_and_notify():
    # 1. Choisir un salarié existant (sportif)
    salarie = pd.read_sql(
        """
        SELECT s.id_salarie, s.nom, s.prenom, sp.sport
        FROM salaries s
        JOIN sports_pratiques sp ON s.id_salarie = sp.id_salarie
        WHERE sp.sport IS NOT NULL
        LIMIT 1 OFFSET 12
        """,
        engine,
    ).iloc[0]

    # 2. Créer l'activité — une course de 7 km ce matin
    now = datetime.now()
    activity = {
        "id_salarie": int(salarie["id_salarie"]),
        "date_debut": now,
        "sport_type": "RUNNING ",
        "distance_m": 6500.0,
        "temps_ecoule_s": 2600,
        "commentaire": "Demo live soutenance — 6.5 km matinal !",
    }

    # 3. Insérer dans PostgreSQL
    df = pd.DataFrame([activity])
    df.to_sql("activites", engine, if_exists="append", index=False)

    # Récupérer le nouvel ID
    with engine.connect() as conn:
        result = conn.execute(text("SELECT MAX(id) FROM activites"))
        new_id = result.scalar()

    print(f"✓ Activité #{new_id} insérée : {salarie['prenom']} {salarie['nom']}")
    print("  Sport : Course à pied | Distance : 6.5 km | Temps : 43 min 25 s")
    print(f"  Date : {now.strftime('%d/%m/%Y %H:%M')}")

    # 4. Compter les activités du salarié (pour montrer l'éligibilité)
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT COUNT(*) FROM activites WHERE id_salarie = :id"),
            {"id": int(salarie["id_salarie"])},
        )
        total = result.scalar()
    print(f"  Total activités de ce salarié : {total} (seuil bien-être = 15)")

    # 5. Notification Slack
    distance_km = activity["distance_m"] / 1000
    duree_min = activity["temps_ecoule_s"] // 60
    allure = activity["temps_ecoule_s"] / 60 / distance_km

    message = {
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"🏃 Nouvelle activité — {salarie['prenom']} {salarie['nom']}",
                },
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": "*Sport :* Course à pied"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Distance :* {distance_km:.1f} km",
                    },
                    {"type": "mrkdwn", "text": f"*Durée :* {duree_min} min"},
                    {
                        "type": "mrkdwn",
                        "text": f"*Allure :* {allure:.1f} min/km",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Date :* {now.strftime('%d/%m/%Y %H:%M')}",
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Activités totales :* {total}",
                    },
                ],
            },
            {
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": f"📌 _{activity['commentaire']}_ | {ENTREPRISE}",
                    }
                ],
            },
        ]
    }

    response = requests.post(SLACK_WEBHOOK_URL, json=message, timeout=10)
    if response.status_code == 200:
        print("✓ Notification Slack envoyée !")
    else:
        print(f"✗ Erreur Slack : {response.status_code} — {response.text}")

    # 6. Re-calculer les avantages pour refléter la nouvelle activité
    print("\n→ Recalcul des avantages...")
    from src.transformation.compute_avantages import compute_avantages

    compute_avantages()

    # 7. Re-exporter pour Power BI
    print("\n→ Export Power BI mis à jour...")
    from src.utils.export_powerbi import export_all

    export_all()

    print("\n✅ Démo terminée — vérifiez Slack et Power BI !")


if __name__ == "__main__":
    insert_and_notify()
