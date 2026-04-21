"""
Génération de données simulées d'activités sportives (type Strava).
Couvre les 12 derniers mois avec des paramètres réalistes par sport.
"""

import random
from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy import text

from src.utils.database import engine

# Plage de dates : 12 derniers mois
DATE_FIN = datetime(2026, 4, 20)
DATE_DEBUT = DATE_FIN - timedelta(days=365)

# Paramètres réalistes par sport
# (distance_min_m, distance_max_m, vitesse_min_kmh, vitesse_max_kmh, distance_applicable)
SPORT_PARAMS = {
    "Runing": {
        "type_activite": "Course à pied",
        "distance_range": (3000, 21000),
        "vitesse_range": (7, 14),  # km/h
        "has_distance": True,
    },
    "Randonnée": {
        "type_activite": "Randonnée",
        "distance_range": (5000, 25000),
        "vitesse_range": (3, 5.5),
        "has_distance": True,
    },
    "Tennis": {
        "type_activite": "Tennis",
        "distance_range": None,
        "vitesse_range": None,
        "has_distance": False,
        "duree_range": (2400, 5400),  # 40 min à 1h30 en secondes
    },
    "Football": {
        "type_activite": "Football",
        "distance_range": (5000, 12000),
        "vitesse_range": (6, 10),
        "has_distance": True,
    },
    "Natation": {
        "type_activite": "Natation",
        "distance_range": (500, 4000),
        "vitesse_range": (1.5, 3.5),
        "has_distance": True,
    },
    "Badminton": {
        "type_activite": "Badminton",
        "distance_range": None,
        "vitesse_range": None,
        "has_distance": False,
        "duree_range": (1800, 4200),
    },
    "Escalade": {
        "type_activite": "Escalade",
        "distance_range": None,
        "vitesse_range": None,
        "has_distance": False,
        "duree_range": (3600, 7200),
    },
    "Voile": {
        "type_activite": "Voile",
        "distance_range": (5000, 30000),
        "vitesse_range": (8, 20),
        "has_distance": True,
    },
    "Triathlon": {
        "type_activite": "Triathlon",
        "distance_range": (20000, 60000),
        "vitesse_range": (15, 30),
        "has_distance": True,
    },
    "Basketball": {
        "type_activite": "Basketball",
        "distance_range": None,
        "vitesse_range": None,
        "has_distance": False,
        "duree_range": (2400, 4800),
    },
    "Boxe": {
        "type_activite": "Boxe",
        "distance_range": None,
        "vitesse_range": None,
        "has_distance": False,
        "duree_range": (1800, 4200),
    },
    "Judo": {
        "type_activite": "Judo",
        "distance_range": None,
        "vitesse_range": None,
        "has_distance": False,
        "duree_range": (2700, 5400),
    },
    "Rugby": {
        "type_activite": "Rugby",
        "distance_range": (4000, 10000),
        "vitesse_range": (5, 9),
        "has_distance": True,
    },
    "Tennis de table": {
        "type_activite": "Tennis de table",
        "distance_range": None,
        "vitesse_range": None,
        "has_distance": False,
        "duree_range": (1200, 3600),
    },
    "Équitation": {
        "type_activite": "Équitation",
        "distance_range": (3000, 20000),
        "vitesse_range": (5, 15),
        "has_distance": True,
    },
}

# Commentaires réalistes par type de sport
COMMENTAIRES = {
    "Course à pied": [
        "Belle sortie matinale, bon rythme !",
        "Fractionné ce matin, ça pique !",
        "Reprise tranquille après une semaine de repos",
        "Nouveau record personnel sur 10 km !",
        "Sortie au bord du Lez, magnifique",
        "Session avec les collègues, bonne ambiance",
        "Préparation semi-marathon en cours",
        None,
        None,
        None,
        None,
        None,
    ],
    "Randonnée": [
        "Randonnée de St Guilhem le désert, je vous la conseille c'est top",
        "Pic Saint-Loup, la vue est incroyable !",
        "Balade dans les Gorges de l'Hérault",
        "Sortie en famille au Salagou",
        "Sentier des douaniers à Sète, superbe",
        "Les crêtes de Mourèze, dépaysement total",
        None,
        None,
        None,
        None,
    ],
    "Tennis": [
        "Match serré, victoire en 3 sets !",
        "Entraînement au club, bon service aujourd'hui",
        "Double avec les collègues",
        None,
        None,
        None,
        None,
    ],
    "Football": [
        "Match du jeudi soir, victoire 3-1 !",
        "Entraînement collectif, bonne séance",
        "Tournoi inter-entreprises ce weekend",
        None,
        None,
        None,
    ],
    "Natation": [
        "50 longueurs ce matin, bon cardio",
        "Séance technique crawl",
        "Nage en mer à Palavas, eau parfaite",
        "Aquagym avec l'équipe !",
        None,
        None,
        None,
        None,
    ],
    "Badminton": [
        "Tournoi au club, demi-finale atteinte !",
        "Session intense, beaucoup de déplacements",
        None,
        None,
        None,
    ],
    "Escalade": [
        "Voie 6a réussie en tête !",
        "Session bloc à la salle, progression !",
        "Falaise de Claret, conditions parfaites",
        None,
        None,
        None,
    ],
    "Voile": [
        "Sortie au large de Palavas, vent idéal",
        "Régate du dimanche, belle 3ème place",
        "Navigation vers Sète, journée parfaite",
        None,
        None,
        None,
    ],
    "Triathlon": [
        "Enchaînement natation-vélo, bonnes sensations",
        "Préparation triathlon de Montpellier",
        "Brick run après le vélo, jambes lourdes !",
        None,
        None,
        None,
    ],
    "Basketball": [
        "Match du mercredi, belle victoire !",
        "Entraînement shoots, 70% de réussite",
        None,
        None,
        None,
    ],
    "Boxe": [
        "Sparring au club, bonne session",
        "Entraînement sac de frappe, défouloir !",
        "Travail technique avec le coach",
        None,
        None,
        None,
    ],
    "Judo": [
        "Randori du mardi, 3 ippons !",
        "Stage technique ce weekend",
        "Préparation compétition départementale",
        None,
        None,
        None,
    ],
    "Rugby": [
        "Match du dimanche, gros combat devant",
        "Entraînement du mardi, travail des touches",
        None,
        None,
        None,
    ],
    "Tennis de table": [
        "Tournoi interne au club, belle finale",
        "Entraînement top spin, ça progresse",
        None,
        None,
        None,
    ],
    "Équitation": [
        "Balade en garrigue, cheval au top",
        "Cours de dressage, bonne séance",
        "Randonnée équestre dans l'arrière-pays",
        None,
        None,
        None,
    ],
}


def random_datetime_between(start: datetime, end: datetime) -> datetime:
    """Génère une date/heure aléatoire entre deux bornes."""
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    dt = start + timedelta(seconds=random_seconds)
    # Heures réalistes : entre 6h et 20h
    hour = random.choices(
        range(6, 21),
        weights=[3, 8, 10, 8, 5, 3, 5, 8, 10, 10, 8, 5, 3, 2, 1],
        k=1,
    )[0]
    minute = random.randint(0, 59)
    return dt.replace(hour=hour, minute=minute, second=0)


def generate_activity(id_salarie: int, sport: str) -> dict:
    """Génère une activité sportive réaliste pour un salarié."""
    params = SPORT_PARAMS[sport]
    type_activite = params["type_activite"]

    date_debut = random_datetime_between(DATE_DEBUT, DATE_FIN)

    # Calcul distance et durée
    if params["has_distance"]:
        distance_m = round(random.uniform(*params["distance_range"]), 1)
        vitesse_kmh = random.uniform(*params["vitesse_range"])
        temps_ecoule_s = int((distance_m / 1000) / vitesse_kmh * 3600)
    else:
        distance_m = None
        temps_ecoule_s = random.randint(*params["duree_range"])

    # Commentaire aléatoire
    commentaire = random.choice(COMMENTAIRES.get(type_activite, [None]))

    return {
        "id_salarie": id_salarie,
        "date_debut": date_debut,
        "sport_type": type_activite,
        "distance_m": distance_m,
        "temps_ecoule_s": temps_ecoule_s,
        "commentaire": commentaire,
    }


def generate_all_activities() -> int:
    """
    Génère l'historique complet des activités pour tous les sportifs.
    Retourne le nombre d'activités générées.
    """
    random.seed(42)  # Reproductibilité

    # Récupérer les salariés sportifs
    query = """
        SELECT sp.id_salarie, sp.sport
        FROM sports_pratiques sp
        WHERE sp.sport IS NOT NULL
    """
    sportifs = pd.read_sql(query, engine)
    print(f"Nombre de sportifs : {len(sportifs)}")

    all_activities = []

    for _, row in sportifs.iterrows():
        id_salarie = row["id_salarie"]
        sport = row["sport"]

        if sport not in SPORT_PARAMS:
            print(f"  ⚠ Sport inconnu ignoré : {sport} (salarié {id_salarie})")
            continue

        # Nombre d'activités : entre 8 et 40 (certains sous le seuil de 15)
        nb_activites = random.randint(8, 40)

        for _ in range(nb_activites):
            activity = generate_activity(id_salarie, sport)
            all_activities.append(activity)

    df_activities = pd.DataFrame(all_activities)

    # Trier par date
    df_activities = df_activities.sort_values("date_debut").reset_index(drop=True)

    print(f"Total activités générées : {len(df_activities)}")
    print(
        f"Période : {df_activities['date_debut'].min()} → {df_activities['date_debut'].max()}"
    )

    # Charger dans PostgreSQL
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE activites"))

    df_activities.to_sql("activites", engine, if_exists="append", index=False)

    print(f"✓ {len(df_activities)} activités chargées dans la table 'activites'")

    # Statistiques
    print("\nRépartition par sport :")
    stats = df_activities["sport_type"].value_counts()
    for sport, count in stats.items():
        print(f"  {sport}: {count}")

    return len(df_activities)


if __name__ == "__main__":
    generate_all_activities()
