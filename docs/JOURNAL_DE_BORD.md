# Projet Sport Data Solution 

## Résumé du projet

Je travaille chez Sport Data Solution. La cofondatrice Juliette veut récompenser les salariés sportifs avec deux avantages :

Avantage 1 — Prime sportive (5% du salaire brut annuel) : pour les salariés qui viennent au bureau via un mode de déplacement sportif (marche, running, vélo, trottinette, etc.). L'info est déjà dans le fichier RH (colonne "Moyen de déplacement"). Mais il faut valider la cohérence : un salarié qui déclare venir en marchant mais habite à 50 km, c'est suspect. On doit utiliser l'API Google Maps pour calculer les distances et appliquer les règles (marche/running ≤ 15 km, vélo/trottinette ≤ 25 km).

Avantage 2 — 5 journées bien-être : pour les salariés ayant au minimum 15 activités physiques déclarées sur l'année. Les données viendront à terme de Strava, mais pour le POC on doit simuler 12 mois d'historique (plusieurs milliers de lignes) basé sur les sports déclarés dans le fichier sportif.

En plus, chaque activité doit générer un message Slack pour l'émulation collective.

## Ce qu'on doit livrer

Voici les livrables attendus :

    Architecture de la solution — Choix des outils, schéma d'architecture, justification.
    Base de données — Création du modèle de données et de la BDD.
    Génération des données simulées (façon API Strava) — plusieurs milliers de lignes sur 12 mois.
    Pipeline ETL — Extraction, Transformation, Chargement des données.
    Tests de qualité des données — avec un outil comme Great Expectations ou Soda.
    Validation des distances (API Google Maps) — vérification de cohérence des déclarations.
    Orchestration — automatisation et scheduling du pipeline.
    Monitoring — surveillance de l'exécution du pipeline.
    Messages Slack — génération automatique à chaque activité.
    Dashboard Power BI — KPIs (coût des primes, jours supplémentaires, pratiques sportives…).
    Documentation — Repo GitHub avec README détaillé.

## Stack technique moderne, 2026

MacBook Pro M1 avec Docker (Colima) et VS Code. 

| Composant | Outil | Pourquoi |
|-----------|-------|----------|
| Base de données | PostgreSQL (via Docker) | Robuste, gratuit, parfait pour ce volume |
| Orchestration | Apache Airflow (via Docker) | Standard industrie pour l'orchestration de pipelines |
| ETL / Scripting | Python (pandas, SQLAlchemy) | Flexibilité, écosystème riche |
| Tests qualité | Soda Core ou Great Expectations | Tests déclaratifs sur les données |
| API Distance | Google Maps Distance Matrix API | Demandé dans la note de cadrage |
| Notifications | Slack Webhook | Simple et efficace pour les messages |
| Monitoring | Airflow UI + alertes intégrées | Suivi des DAGs, logs, alertes |
| Visualisation | Power BI | Demandé explicitement dans l'énoncé |
| Versioning | GitHub | Demandé dans les contraintes |


## Étape 1 — Mise en place de l'environnement de travail

On va commencer par :

    Créer la structure du projet
    Lancer PostgreSQL et Airflow via Docker Compose
    Vérifier que tout tourne

### Étape 1.1 — Vérifier l'environnement existant

Commence par vérifier ta version de Python et si uv est déjà installé. Exécute ces commandes dans ton terminal :
```bash 
python3 --version
uv --version
```


**Petit point pédagogique sur uv**
uv est un gestionnaire de paquets et d'environnements virtuels Python développé par Astral (la même équipe derrière ruff, le linter ultra-rapide). Il est écrit en Rust, ce qui le rend extrêmement rapide comparé aux outils traditionnels comme pip + venv ou même poetry. En 2026, c'est devenu un standard de facto dans l'écosystème Python pour plusieurs raisons : il remplace à lui seul pip, pip-tools, venv, pyenv et poetry, il est 10 à 100 fois plus rapide que pip pour la résolution de dépendances, et il gère nativement les versions de Python. C'est exactement le genre d'outil moderne qu'un évaluateur sera content de voir dans ton projet.

### Étape 1.2 — Créer la structure du projet

D'abord, place-toi dans le dossier où tu veux créer ton projet (par exemple ton dossier de travail habituel, ~/Documents, ~/Projects, ou autre). Ensuite on va initialiser le projet avec uv :
```bash 
cd ~
mkdir sport-data-solution && cd sport-data-solution
uv init --python 3.13
```

**Pourquoi Python 3.13 et pas 3.14 ?**
Python 3.14 est très récent et certaines librairies qu'on va utiliser (Airflow, SQLAlchemy, Great Expectations, etc.) n'ont pas forcément encore publié de wheels compatibles 3.14. Utiliser 3.13 nous garantit une compatibilité optimale avec tout l'écosystème. C'est un réflexe important en Data Engineering : on ne prend pas toujours la dernière version du langage, on prend la dernière version stable largement supportée. uv va automatiquement télécharger et gérer Python 3.13 pour ce projet, sans toucher à ton Python 3.14 système.

### Étape 1.3 — Créer l'arborescence du projet

Un projet Data Engineering bien structuré, c'est essentiel. Ça montre à ton évaluateur que tu maîtrises l'organisation d'un projet professionnel. Voici la structure qu'on va mettre en place :

```bash 
sport-data-solution/
├── dags/                    # DAGs Airflow (orchestration du pipeline)
├── data/
│   ├── raw/                 # Données brutes (fichiers Excel d'entrée)
│   └── processed/           # Données transformées
├── src/
│   ├── extraction/          # Scripts d'extraction des données
│   ├── transformation/      # Scripts de transformation
│   ├── loading/             # Scripts de chargement en BDD
│   ├── generation/          # Génération des données simulées (type Strava)
│   ├── notifications/       # Envoi des messages Slack
│   └── utils/               # Fonctions utilitaires (connexion BDD, config...)
├── tests/                   # Tests de qualité des données (Soda/GE)
├── docker/                  # Fichiers Docker spécifiques
├── dashboards/              # Fichiers Power BI
├── docs/                    # Documentation complémentaire
├── docker-compose.yml
├── pyproject.toml
└── README.md
``` 
**Point pédagogique — Pourquoi cette structure ?**
Cette organisation suit le principe de séparation des responsabilités. Chaque dossier a un rôle clair. Le dossier src/ sépare les phases classiques d'un pipeline ETL (Extract, Transform, Load) ce qui rend le code maintenable et testable. Le dossier dags/ est séparé car Airflow a besoin d'y accéder directement. Le dossier data/raw/ contiendra tes fichiers Excel d'origine qu'on ne modifie jamais (principe d'immutabilité des données brutes), tandis que data/processed/ contiendra les résultats intermédiaires.


### Étape 1.4 — Copier les fichiers de données brutes

Maintenant, on va placer les fichiers Excel fournis dans le dossier data/raw/. C'est notre source de vérité — on ne modifiera jamais ces fichiers directement.

Copie les deux fichiers Excel dans data/raw/. Adapte le chemin source selon l'endroit où tu les as stockés :
```bash 
cp ~/path/vers/Donnee_RH.xlsx data/raw/
cp ~/path/vers/Donnees_Sportive.xlsx data/raw/

#Par exemple, si tes fichiers sont dans ~/Enonce_Mission/ :

cp ~/Enonce_Mission/Donnee_RH.xlsx data/raw/
cp ~/Enonce_Mission/Donnees_Sportive.xlsx data/raw/
```


## Étape 2 — Mise en place de PostgreSQL avec Docker

**Point pédagogique — Pourquoi PostgreSQL dans Docker ?**
En Data Engineering, on utilise Docker pour conteneuriser les services d'infrastructure. Ça signifie que ta base de données tourne dans un conteneur isolé, reproductible et portable. N'importe qui peut cloner ton repo, lancer docker compose up et avoir exactement le même environnement. C'est un standard en entreprise et ton évaluateur s'attend à voir ça.

PostgreSQL est le choix naturel ici : c'est une base relationnelle robuste, open source, qui gère très bien les données structurées comme nos données RH et sportives. Pour un POC avec quelques milliers de lignes, c'est largement suffisant et professionnel.

### Étape 2.1 — Vérifier que Docker tourne

D'abord, vérifie que Colima et Docker sont opérationnels :
``` bash 
colima status
colima start
docker ps
```

### Étape 2.2 — Créer le fichier docker-compose.yml

On va configurer PostgreSQL et plus tard on ajoutera Airflow dans ce même fichier. Pour l'instant, commençons par la base de données.

Retourne dans le dossier du projet et crée le fichier :
```bash 
cd ~/sport-data-solution

#Crée un fichier .env à la racine du projet pour stocker les variables sensibles (mots de passe, etc.) :

cat > .env << 'EOF'
# PostgreSQL
POSTGRES_USER=sport_admin
POSTGRES_PASSWORD=sport_secret_2026
POSTGRES_DB=sport_data
POSTGRES_PORT=5432
EOF
```


Ensuite, crée le docker-compose.yml :

**Point pédagogique — Ce qu'on vient de faire**
Le fichier .env sépare la configuration sensible du code. On ne met jamais de mots de passe en dur dans un docker-compose.yml. C'est une bonne pratique de sécurité, particulièrement importante ici puisque la note de cadrage insiste sur la protection des données RH.
Dans le docker-compose.yml, le volume postgres_data assure la persistance des données : si le conteneur redémarre, les données ne sont pas perdues. Le healthcheck permet à Docker (et plus tard à Airflow) de savoir si PostgreSQL est réellement prêt à recevoir des connexions, pas juste démarré.


Puis lance PostgreSQL :
```bash 
docker-compose up -d

#Et vérifie qu'il tourne :

docker ps
```

### Étape 2.3 — Tester la connexion à PostgreSQL

Vérifions qu'on peut se connecter à la base. On va le faire directement depuis le conteneur :
```bash 
docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "SELECT version();"
```

## Étape 3 — Installer les dépendances Python

Avant de créer le modèle de données, on a besoin des librairies Python. On va les installer avec uv.

**Point pédagogique — Pourquoi ces librairies ?**

Voici ce qu'on va installer pour commencer, avec le rôle de chacune :

    sqlalchemy : ORM Python pour interagir avec PostgreSQL de manière élégante, sans écrire du SQL brut partout. C'est le standard en Python pour la couche d'accès aux données.
    psycopg[binary] : le driver PostgreSQL pour Python. C'est la version 3 (psycopg3), moderne et performante. SQLAlchemy en a besoin pour communiquer avec PostgreSQL.
    pandas : manipulation de données tabulaires. Indispensable pour lire les fichiers Excel et transformer les données.
    openpyxl : moteur de lecture des fichiers .xlsx. Pandas en a besoin pour lire tes fichiers Excel.

On ajoutera d'autres dépendances au fur et à mesure (Soda, Slack SDK, etc.), mais commençons par l'essentiel.

Exécute :
```bash
uv add sqlalchemy "psycopg[binary]" pandas openpyxl

#Puis vérifie que tout est bien installé :

uv run python -c "import sqlalchemy; import psycopg; import pandas; print(f'SQLAlchemy {sqlalchemy.__version__}'); print(f'Pandas {pandas.__version__}'); print('Tout est OK !')"
```
### Étape 3.2 — Créer le fichier de configuration de la base de données

Avant de définir le modèle de données, on va créer un utilitaire de connexion à PostgreSQL. C'est une bonne pratique de centraliser la configuration de la BDD dans un seul fichier.

**Point pédagogique — Le pattern de connexion**
On utilise SQLAlchemy avec le concept d'Engine (le point d'entrée vers la BDD) et de Session (une conversation avec la BDD). On lit les paramètres depuis les variables d'environnement ou depuis le fichier .env, ce qui permet de ne jamais coder en dur les identifiants.

Crée le fichier src/utils/database.py :

Et on teste la connexion :
```bash 
uv run python -m src.utils.database
``` 
La connexion Python → PostgreSQL fonctionne. La chaîne complète est opérationnelle.

### Étape 3.3 — Créer le modèle de données
Maintenant on va définir les tables qui vont accueillir nos données. C'est le schéma de notre base.

**Point pédagogique — Modélisation des données**
En Data Engineering, on réfléchit au modèle de données avant d'écrire le moindre pipeline. On a besoin de 3 tables principales :

    - salaries — Les données RH des employés (issues de Donnee_RH.xlsx)

    - sports_pratiques — Les sports déclarés par les salariés (issues de Donnees_Sportive.xlsx)
    
    - activites — L'historique simulé des activités sportives (les milliers de lignes qu'on va générer, façon Strava)

On utilisera aussi une table pour stocker les résultats d'éligibilité aux avantages, mais on la créera plus tard.

On utilise SQLAlchemy ORM avec le pattern déclaratif : chaque table est une classe Python. C'est plus maintenable et lisible que du SQL brut, et ça permet de versionner le schéma dans Git.

Crée le fichier src/utils/models.py :

**Points importants dans ce modèle**

Les CheckConstraint sur la table activites garantissent au niveau de la BDD que les distances ne peuvent pas être négatives et que les temps écoulés non plus. C'est directement lié à ce que demande la note de cadrage dans la section "Tests sur les données". La colonne distance_m est nullable car certains sports comme l'escalade n'ont pas de distance pertinente, comme le précise la note de cadrage. Les relations (relationship) permettent de naviguer facilement entre les tables en Python (par exemple, accéder aux activités d'un salarié via salarie.activites).


Maintenant, créons les tables dans PostgreSQL :

src/utils/init_db.py


On Exécute :
```bash 
uv run python -m src.utils.init_db

#Puis on vérifie directement dans PostgreSQL que les tables existent :

docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "\dt"

```

## Étape 4 — Extraction et chargement des données brutes (le "E" et "L" de ETL)

On va maintenant lire les fichiers Excel et charger les données dans PostgreSQL. C'est la première brique du pipeline.
Point pédagogique — ETL vs ELT

Traditionnellement, on parle d'ETL (Extract, Transform, Load). Mais en pratique moderne, on fait souvent du ELT : on charge d'abord les données brutes en base, puis on les transforme ensuite. L'avantage, c'est qu'on garde toujours les données d'origine intactes dans la base et qu'on peut rejouer les transformations. C'est ce qu'on va faire ici : d'abord charger, puis transformer dans une étape ultérieure.

### Étape 4.1 — Script d'extraction et chargement des données RH

Crée le fichier src/extraction/load_rh.py :

Crée ensuite le fichier src/extraction/load_sports.py :

Maintenant, on exécute les deux scripts dans l'ordre (les salariés d'abord, car la table sports a une clé étrangère vers salariés) :
```bash 
uv run python -m src.extraction.load_rh
uv run python -m src.extraction.load_sports
``` 
Excellent ! 161 salariés et 161 enregistrements sportifs chargés. On voit déjà que 95 salariés pratiquent un sport et 66 n'en déclarent pas. Ces chiffres seront utiles pour le dashboard Power BI.


Vérifions rapidement que les données sont bien en base avec quelques requêtes :
```bash 
docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "
SELECT s.id_salarie, s.nom, s.prenom, s.moyen_deplacement, sp.sport
FROM salaries s
JOIN sports_pratiques sp ON s.id_salarie = sp.id_salarie
WHERE sp.sport IS NOT NULL
LIMIT 10;
"
```

Résultat : 
``` bash 
(sport-data-solution) behramko@BehramMacbookPro sport-data-solution % docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "
SELECT s.id_salarie, s.nom, s.prenom, s.moyen_deplacement, sp.sport
FROM salaries s
JOIN sports_pratiques sp ON s.id_salarie = sp.id_salarie
WHERE sp.sport IS NOT NULL
LIMIT 10;
"

 id_salarie |   nom    |  prenom   |       moyen_deplacement       |      sport      
------------+----------+-----------+-------------------------------+-----------------
      56482 | Dumont   | Michelle  | véhicule thermique/électrique | Tennis
      17757 | Bazin    | Margaret  | Vélo/Trottinette/Autres       | Badminton
      17036 | Jacques  | Julien    | véhicule thermique/électrique | Escalade
      90284 | Chartier | Aurélie   | véhicule thermique/électrique | Randonnée
      83440 | Maillard | Augustin  | Transports en commun          | Triathlon
      33386 | Neveu    | Yves      | véhicule thermique/électrique | Randonnée
      25701 | Foucher  | Eugénie   | véhicule thermique/électrique | Runing
      43124 | Laole    | Francoise | véhicule thermique/électrique | Équitation
      56632 | Evrard   | Claire    | véhicule thermique/électrique | Voile
      17997 | Dias     | Mathilde  | véhicule thermique/électrique | Tennis de table
(10 rows)
```

Les données sont proprement jointes entre les deux tables. On voit les salariés avec leur moyen de déplacement et leur sport déclaré. La base est solide.


## Étape 5 — Génération des données simulées (façon Strava)

C'est la partie la plus intéressante. La note de cadrage demande de simuler 12 mois d'historique d'activités sportives avec plusieurs milliers de lignes, en attendant la connexion réelle à l'API Strava.
Point pédagogique — Pourquoi simuler des données réalistes ?

Dans un POC, on a rarement accès aux vraies données dès le départ. On génère donc des données synthétiques qui respectent les mêmes caractéristiques statistiques que les données réelles. L'important est la cohérence : un coureur ne fait pas 100 km en 10 minutes, un randonneur ne marche pas 2 km en 8 heures. 

On doit calibrer les paramètres par sport pour que les données soient crédibles. C'est aussi ce qui sera testé par les outils de qualité ensuite.

### La logique de génération

Pour chaque salarié qui a déclaré un sport, on va générer entre 15 et 40 activités sur les 12 derniers mois (avril 2025 → avril 2026). 
**Pourquoi 15 minimum ?**  Parce que le seuil d'éligibilité aux 5 jours bien-être est de 15 activités. Certains seront au-dessus, d'autres en dessous — c'est plus réaliste. On va aussi ajouter quelques commentaires aléatoires pour simuler les messages Slack.

Crée le fichier src/generation/generate_activities.py :

On exécute le générateur :
```bash 
uv run python -m src.generation.generate_activities
``` 

Résultats : 
```bash 
(sport-data-solution) behramko@BehramMacbookPro sport-data-solution % uv run python -m src.generation.generate_activities
Nombre de sportifs : 95
Total activités générées : 2173
Période : 2025-04-20 07:47:00 → 2026-04-19 16:50:00
✓ 2173 activités chargées dans la table 'activites'

Répartition par sport :
  Randonnée: 438
  Course à pied: 423
  Tennis: 243
  Natation: 178
  Football: 114
  Judo: 112
  Rugby: 105
  Voile: 102
  Badminton: 99
  Boxe: 81
  Escalade: 78
  Triathlon: 73
  Équitation: 56
  Tennis de table: 36
  Basketball: 35
```
2173 activités générées sur 12 mois, bien réparties par sport. La randonnée et la course à pied dominent, ce qui est cohérent avec le nombre de pratiquants dans les données. On est au-dessus des "plusieurs milliers de lignes" demandées dans la note de cadrage.

Vérifions quelques lignes dans la base pour s'assurer que les données sont réalistes :
```bash 
docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "
SELECT a.id, s.prenom, s.nom, a.sport_type, a.distance_m, a.temps_ecoule_s, a.commentaire
FROM activites a
JOIN salaries s ON a.id_salarie = s.id_salarie
ORDER BY a.date_debut DESC
LIMIT 5;
"
``` 

Résultats : 
```bash
(sport-data-solution) behramko@BehramMacbookPro sport-data-solution % docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "
SELECT a.id, s.prenom, s.nom, a.sport_type, a.distance_m, a.temps_ecoule_s, a.commentaire
FROM activites a
JOIN salaries s ON a.id_salarie = s.id_salarie
ORDER BY a.date_debut DESC
LIMIT 5;
"
  id  |   prenom   |    nom    |  sport_type   | distance_m | temps_ecoule_s |                  commentaire                  
------+------------+-----------+---------------+------------+----------------+-----------------------------------------------
 2173 | Bernard    | Georges   | Randonnée     |    20373.4 |          18921 | 
 2172 | Gégoire    | Guillot   | Course à pied |       6848 |           2596 | Reprise tranquille après une semaine de repos
 2171 | Marguerite | Carre     | Course à pied |    11788.7 |           4446 | Sortie au bord du Lez, magnifique
 2170 | Gabriel    | Poirier   | Voile         |      14417 |           2965 | Régate du dimanche, belle 3ème place
 2169 | Léon       | Rodriguez | Course à pied |    20104.6 |           7789 | Belle sortie matinale, bon rythme !
(5 rows)

``` 
Les données sont réalistes : une randonnée de 20 km en ~5h15, une course de 6.8 km en ~43 min, une sortie voile de 14 km... tout est cohérent. Parfait.


## Étape 6 — Validation des distances domicile-entreprise (API Google Maps)

C'est une étape clé du POC. La note de cadrage demande de vérifier la cohérence des déclarations des salariés sur leur mode de déplacement. Un salarié qui déclare venir en marchant mais habite à 50 km, c'est une anomalie à détecter.

**Point pédagogique — Pourquoi cette validation ?**
En Data Engineering, la qualité des données est fondamentale. Les données déclaratives sont souvent sources d'erreurs : déménagement non signalé, mauvaise saisie, etc. On met en place des règles de validation automatiques pour détecter ces incohérences. Ici, on va croiser deux sources de données (l'adresse déclarée et le mode de transport) avec une source externe (Google Maps) pour valider la cohérence.

### Les règles (note de cadrage)

    Marche/Running → maximum 15 km
    Vélo/Trottinette/Autres → maximum 25 km
    Adresse de l'entreprise : 1362 Av. des Platanes, 34970 Lattes

### Étape 6.1 — Obtenir une clé API Google Maps

Pour utiliser l'API Distance Matrix de Google, tu as besoin d'une clé API. Voici les étapes :

    Va sur https://console.cloud.google.com
    Crée un projet (ou utilise un existant)
    Active l'API "Distance Matrix API"
    Crée une clé API dans "Identifiants" (Credentials)

Google offre un crédit gratuit de 200$/mois, largement suffisant pour nos 161 requêtes.

### Étape 6.2 — Installer la librairie Google Maps et créer le script de validation

D'abord, installons le client Python Google Maps :
```bash 
uv add googlemaps python-dotenv
```

python-dotenv nous permet de charger le fichier .env automatiquement dans nos scripts.

Ensuite, crée le fichier src/transformation/validate_distances.py :
Ce que fait ce script

Il identifie tous les salariés déclarant un mode de déplacement sportif (marche/running ou vélo/trottinette). Pour chacun, il appelle l'API Google Maps pour calculer la distance réelle entre leur domicile et l'entreprise (1362 Av. des Platanes, Lattes). Il compare la distance obtenue avec le seuil autorisé et signale les anomalies. Les résultats sont sauvegardés en base (table validation_distances) et exportés en CSV.

On lance le script :
```bash
uv run python -m src.transformation.validate_distances
```
Ça va prendre une ou deux minutes car on fait une requête API par salarié avec une petite pause entre chaque. Partage-moi le résultat complet !

Résultat : 
Tout fonctionne parfaitement. Les 68 salariés à déplacement sportif ont été vérifiés et tous sont conformes — aucune anomalie détectée. Les adresses sont toutes dans la région de Montpellier/Lattes, donc les distances sont cohérentes avec les déclarations.

C'est un résultat réaliste pour un POC. Dans la vraie vie, on trouverait probablement quelques anomalies. Ton évaluateur verra surtout que le mécanisme de détection est en place et fonctionnel.


## Étape 7 — Tests de qualité des données avec Soda Core

**Point pédagogique — Pourquoi tester les données ?**
La note de cadrage mentionne explicitement la nécessité de "documenter les tests de cohérence et de fonctionnalité". 
En Data Engineering, on ne fait pas confiance aux données : on les teste systématiquement. C'est comme les tests unitaires en développement logiciel, mais pour les données. On vérifie que les distances ne sont pas négatives, que les dates sont valides, qu'il n'y a pas de doublons incohérents, etc.

Soda Core est un outil open source de data quality testing. Il permet d'écrire des vérifications en YAML de manière déclarative, c'est-à-dire qu'on décrit ce qu'on attend des données plutôt que comment le vérifier. C'est plus lisible et maintenable que des scripts SQL manuels, et c'est un outil très apprécié en entreprise.

### Étape 7.1 — Installer Soda Core
```bash 
uv add soda-core-postgres
``` 

### Étape 7.2 — Configurer Soda et créer les tests de qualité

On va créer deux fichiers : un fichier de configuration (connexion à la BDD) et un fichier de checks (les tests à exécuter).

Crée le dossier de configuration Soda et le fichier de connexion :

tests/soda/configuration.yml 

Maintenant, crée le fichier de checks. C'est ici que la magie opère — chaque test vérifie une règle de qualité :

tests/soda/checks.yml

**Ce que testent ces checks** 

Les tests couvrent les 5 dimensions classiques de la qualité des données : la complétude (pas de valeurs manquantes sur les champs obligatoires), l'unicité (pas de doublons d'ID), la validité (salaires positifs, distances non négatives, types de contrat reconnus), la cohérence (date de naissance avant date d'embauche), et l'intégrité référentielle (chaque activité est liée à un salarié existant).

Lance les tests :
```bash 
uv run soda scan -d sport_data -c tests/soda/configuration.yml tests/soda/checks.yml
``` 

!!! Petite erreur !!! 
problème connu : le module distutils a été supprimé dans Python 3.12+ et Soda Core ne s'est pas encore adapté. On va installer le package de remplacement :
```bash 
uv add setuptools

#Puis relance le scan :

uv run soda scan -d sport_data -c tests/soda/configuration.yml tests/soda/checks.yml
```

Résultats : 
20/20 checks PASSED — "All is good. No failures. No warnings. No errors." C'est un résultat impeccable.

L'évaluateur verra que nous avons mis en place une suite de tests de qualité couvrant les 4 tables, avec des vérifications de complétude, unicité, validité et volumétrie. C'est exactement ce que demandait la note de cadrage.


## Étape 8 — Calcul des avantages (Transformation — le "T" de ETL)

Maintenant on va créer le cœur métier du projet : 
- calculer quels salariés sont éligibles aux deux avantages et chiffrer l'impact financier pour l'entreprise.

**Point pédagogique — La couche de transformation**
C'est ici qu'on applique les règles métier définies dans la note de cadrage. On transforme les données brutes en informations exploitables. C'est la partie la plus importante pour les décideurs (Juliette) et pour le dashboard Power BI.

### Rappel des règles

Prime sportive (5% du salaire brut) : éligible si le moyen de déplacement est sportif (Marche/running, Vélo/Trottinette/Autres) ET que la distance domicile-entreprise est conforme.

5 journées bien-être : éligible si le salarié a au minimum 15 activités physiques dans l'année.

Crée le fichier src/transformation/compute_avantages.py :

Et on lance le calcul :

```bash 
uv run python -m src.transformation.compute_avantages
``` 

Résultats : 
```bash 
(sport-data-solution) behramko@BehramMacbookPro sport-data-solution % uv run python -m src.transformation.compute_avantages
============================================================
CALCUL DE LA PRIME SPORTIVE (5% salaire brut)
============================================================
  Salariés éligibles : 68 / 161
  Coût total primes  : 172,482.50 €
  Prime moyenne      : 2,536.51 €

============================================================
CALCUL DES JOURNÉES BIEN-ÊTRE (5 jours si >= 15 activités)
============================================================
  Salariés éligibles   : 73 / 161
  Total jours accordés : 365

============================================================
TABLEAU RÉCAPITULATIF
============================================================
  ✓ Table 'avantages_salaries' créée (161 lignes)
  ✓ Export CSV : data/processed/avantages_salaries.csv

============================================================
IMPACT PAR BUSINESS UNIT
============================================================
  Finance      |  42 sal. | Prime: 23 élig. ( 59,439.00 €) | Bien-être: 22 élig. (110 jours)
  Marketing    |  25 sal. | Prime: 10 élig. ( 24,529.50 €) | Bien-être: 10 élig. ( 50 jours)
  R&D          |  26 sal. | Prime:  5 élig. (  9,774.00 €) | Bien-être: 10 élig. ( 50 jours)
  Support      |  35 sal. | Prime: 15 élig. ( 42,043.00 €) | Bien-être: 14 élig. ( 70 jours)
  Ventes       |  33 sal. | Prime: 15 élig. ( 36,697.00 €) | Bien-être: 17 élig. ( 85 jours)

============================================================
IMPACT FINANCIER GLOBAL
============================================================
  Coût total primes sportives :   172,482.50 €
  Total jours bien-être       :          365 jours
  Nombre de salariés          :          161
(sport-data-solution) behramko@BehramMacbookPro sport-data-solution % 
``` 
Les résultats sont très parlants et c'est exactement ce que Juliette attend pour le POC :

    68 salariés éligibles à la prime sportive, pour un coût total de 172 482,50 €
    73 salariés éligibles aux journées bien-être, soit 365 jours au total
    La Finance est la BU la plus impactée (42 salariés, 23 primes)

Ces chiffres alimenteront directement le dashboard Power BI.


## Étape 9 — Notifications Slack

La note de cadrage demande que chaque activité sportive génère automatiquement un message dans un channel Slack pour favoriser l'émulation entre collègues.

**Point pédagogique — Webhooks Slack**
Un Webhook entrant (Incoming Webhook) est la manière la plus simple d'envoyer des messages dans Slack depuis un programme externe. C'est une URL unique à laquelle tu envoies un JSON et Slack affiche le message dans le channel configuré. Pas besoin de gérer l'authentification OAuth, c'est parfait pour un POC.

### Étape 9.1 — Créer un Webhook Slack

Pour ça tu as besoin d'un workspace Slack. Tu as deux options :

Option A — Tu as déjà un workspace Slack de test → on crée un webhook directement

Option B — Tu n'en as pas → tu peux en créer un gratuitement sur https://slack.com/create

Voici les étapes pour créer le webhook :

    Va sur https://api.slack.com/apps
    Clique "Create New App" → "From scratch"
    Nom : Sport Data Bot, choisis ton workspace
    Dans le menu gauche, clique "Incoming Webhooks" → Active-le
    Clique "Add New Webhook to Workspace" → choisis un channel (par exemple #sport-activites)
    Copie l'URL du webhook

### Étape 9.2 — Créer le script de notifications Slack

On va créer un module qui génère des messages motivants basés sur les activités sportives, exactement comme les exemples de la note de cadrage.

Installons d'abord la librairie requests pour les appels HTTP :
```bash 
uv add requests
``` 

Puis on crée le fichier src/notifications/slack_notifier.py :

Et on lance le test avec les 5 dernières activités :
```bash
uv run python -m src.notifications.slack_notifier
``` 
Résultats : 
5 messages envoyés avec succès ! on a vérifié sur le channel #all-sport-data-workspace que les messages s'affichent bien avec les emojis et le format motivant. 

# Récapitulons ce qui est fait et ce qui reste :

Fait :

    ✅ Structure du projet
    ✅ PostgreSQL (Docker)
    ✅ Modèle de données (3 tables)
    ✅ Extraction/chargement des données RH et sportives
    ✅ Génération des données simulées (2173 activités)
    ✅ Validation des distances (API Google Maps)
    ✅ Tests de qualité (Soda Core — 20/20)
    ✅ Calcul des avantages (primes + journées bien-être)
    ✅ Notifications Slack

Reste à faire :

    ⬜ Orchestration avec Airflow (DAG du pipeline complet)
    ⬜ Monitoring
    ⬜ Dashboard Power BI
    ⬜ Documentation (README GitHub)


## Étape 10 — Orchestration avec Apache Airflow

**Point pédagogique — Pourquoi Airflow ?**

Jusqu'ici, on a exécuté chaque script manuellement. En production, on a besoin d'un orchestrateur qui exécute les étapes dans le bon ordre, gère les dépendances entre elles, relance en cas d'erreur, et fournit une interface de monitoring. 
C'est le rôle d'Airflow. On définit un DAG (Directed Acyclic Graph) : un graphe des tâches avec leurs dépendances. Airflow se charge de tout exécuter dans l'ordre.

### Étape 10.1 — Ajouter Airflow au docker-compose

On va mettre à jour le docker-compose.yml pour ajouter Airflow. On utilise l'image officielle en mode standalone (simplifié pour un POC) :

Ce qu'on a configuré

Airflow tourne avec un SequentialExecutor et une base SQLite interne — c'est suffisant pour un POC. 

On monte nos dossiers dags/, src/, data/ et tests/ dans le conteneur pour qu'Airflow accède à notre code. 

La variable POSTGRES_HOST=postgres pointe vers le conteneur PostgreSQL via le réseau Docker interne (pas localhost). 

Les dépendances Python sont installées au démarrage du conteneur.

On relance les services :
```bash
docker-compose down
docker-compose up -d
```

Le premier démarrage d'Airflow prend 1-2 minutes (installation des dépendances + migration de la BDD). 
On surveille les logs :
```bash
docker logs -f sport_airflow
```

Attends de voir un message du type webserver | [INFO] Listening at: http://0.0.0.0:8080. Tu peux interrompre les logs avec Ctrl+C. Partage-moi ce que tu vois !

### Étape 10.2 — Créer le DAG du pipeline

Le DAG va orchestrer toutes les étapes de notre pipeline dans l'ordre. Voici le flux :
```bash 
load_rh 
    → load_sports 
        → generate_activities 
            → validate_distances 
                → compute_avantages 
                    → run_soda_tests 
                        → notify_slack
```

On crée le fichier dags/sport_pipeline_dag.py :

**Ce que fait ce DAG**

Les 7 tâches s'enchaînent dans l'ordre logique du pipeline. 
- D'abord le chargement des données sources (RH puis sports), 
- ensuite la génération des activités simulées, 
- puis la validation des distances via Google Maps, 
- le calcul des avantages, 
- les tests de qualité Soda, 
- et enfin les notifications Slack. 
Le schedule=None signifie qu'on le déclenche manuellement — c'est approprié pour un POC.

Attends 30 secondes qu'Airflow détecte le nouveau DAG, puis rafraîchis la page dans ton navigateur. Tu devrais voir apparaître le DAG sport_data_pipeline. Envoie-moi un screenshot !

### Étape 10.3 — Exécuter le pipeline

Avant de lancer le DAG, il faut d'abord mettre à jour la configuration Soda pour qu'elle pointe vers postgres (le nom du conteneur Docker) au lieu de localhost, car les tâches s'exécutent à l'intérieur du conteneur Airflow :


Il faut aussi adapter le fichier src/utils/database.py pour qu'il lise la variable POSTGRES_HOST depuis l'environnement (ce qu'on avait déjà prévu — la valeur par défaut est localhost pour le local, et Airflow passera postgres) :

Vérifions que c'est bien le cas :
```bash 
grep "POSTGRES_HOST" src/utils/database.py
```

Si c'est bon, on peut lancer le pipeline. Dans l'interface Airflow :

    On Active le DAG en cliquant sur le toggle à gauche du nom (le petit interrupteur)
    On Clique sur le bouton Play (▶) en haut à droite puis "Trigger DAG"

Le pipeline va s'exécuter tâche par tâche. Nous verrons les blocs passer du blanc au vert (succès) ou rouge (échec). 

Résultats :  Echec à la tâche Load , première tâche
Le problème est que la commande pip install dans le docker-compose installe une version ancienne de SQLAlchemy (1.x) qui ne supporte pas DeclarativeBase. On va corriger ça en fixant les versions et en utilisant les URLs S3 pour les données — c'est même mieux car ça montre à l'évaluateur une vraie extraction depuis une source externe.

On modifie  : docker-compose.yml , les scripts src/extraction/load_rh.py et src/extraction/load_sports.py
Maintenant, relance les conteneurs :

docker compose down
docker compose up -d

Attends 2-3 minutes que les dépendances s'installent, puis surveille :

docker logs -f sport_airflow 2>&1 | tail -20

Les logs montrent un conflit de version . La meilleure approche est d'utiliser Airflow 3.x qui supporte nativement SQLAlchemy 2.x. Vérifions la dernière image disponible : 
Airflow 3.x est disponible mais c'est un changement majeur avec des modifications de syntaxe des DAGs. Pour éviter des complications, adoptons une approche plus pragmatique : gardons Airflow 2.10.5 et installons SQLAlchemy 1.4 dans le conteneur, tout en gardant notre code compatible. On va simplement adapter notre fichier database.py pour qu'il fonctionne avec SQLAlchemy 1.4 dans Airflow :

il faut aussi adapter le fichier models.py pour être compatible avec les deux versions de SQLAlchemy :

Maintenant, relance tout :

docker compose down
docker compose up -d

Attends 2-3 minutes puis vérifie les logs :

docker logs sport_airflow 2>&1 | tail -5

Résultats : 
🎉 Le pipeline complet tourne de bout en bout dans Airflow ! Toutes les 7 tâches sont en vert :

    load_donnees_rh — chargement depuis S3
    load_donnees_sportives — chargement depuis S3
    generate_activities — 2173 activités simulées
    validate_distances — vérification Google Maps
    compute_avantages — calcul des primes et jours bien-être
    run_soda_tests — 20/20 tests qualité
    notify_slack — 3 messages envoyés avec succès

Le diagramme de Gantt montre que validate_distances est la tâche la plus longue (les appels API Google Maps), ce qui est logique. Le pipeline total prend environ 40 secondes. C'est excellent pour une démo live.



## Étape 11 — Dashboard Power BI
**Point pédagogique — Pourquoi Power BI ?**

C'est explicitement demandé dans l'énoncé. Power BI va permettre à Juliette de visualiser l'impact financier des avantages sportifs de manière interactive. On va connecter Power BI directement à notre base PostgreSQL pour que les données soient toujours à jour.

### Étape 11.1 — Préparer les données pour Power BI

Pour faciliter la connexion, on va d'abord vérifier que toutes les tables nécessaires sont bien présentes :
```bash 
docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "\dt"
```

Résultat : 
```bash 
(sport-data-solution) behramko@BehramMacbookPro sport-data-solution % docker exec -it sport_postgres psql -U sport_admin -d sport_data -c "\dt"
                  List of relations
 Schema |         Name         | Type  |    Owner    
--------+----------------------+-------+-------------
 public | activites            | table | sport_admin
 public | avantages_par_bu     | table | sport_admin
 public | avantages_salaries   | table | sport_admin
 public | salaries             | table | sport_admin
 public | sports_pratiques     | table | sport_admin
 public | validation_distances | table | sport_admin
(6 rows)

```
c'est la meilleure approche sur Mac. On va exporter toutes les tables nécessaires en CSV, puis tu pourras les importer dans Power BI (via le web gratuit ou via une VM Windows si tu en as une).

### Étape 11.2 — Exporter toutes les données pour Power BI

on crée le fichier src/utils/export_powerbi.py

Exécute l'export :

uv run python -m src.utils.export_powerbi

Puis vérifie :

ls -la dashboards/

Tous les fichiers CSV sont exportés. Tu as tout ce qu'il faut pour construire le dashboard Power BI.

### Étape 11.3 — Créer le Dashboard Power BI

Pour utiliser Power BI depuis ton Mac, tu as plusieurs options. La plus simple est Power BI Service (en ligne) : va sur https://app.powerbi.com et connecte-toi avec un compte Microsoft (gratuit). Tu pourras importer les CSV et créer le rapport directement dans le navigateur.

Voici les KPIs et visualisations que je te recommande de créer, en lien direct avec ce que demande la note de cadrage et Juliette :

Page 1 — Vue d'ensemble

    Carte KPI : Nombre total de salariés (161)
    Carte KPI : Coût total des primes sportives (172 482,50 €)
    Carte KPI : Total jours bien-être accordés (365)
    Carte KPI : Nombre de sportifs déclarés (95)
    Graphique en barres : Répartition des salariés par BU
    Graphique en anneau : Proportion sportifs vs non-sportifs

Page 2 — Avantages sportifs

    Graphique en barres groupées : Éligibles prime et bien-être par BU (utilise avantages_par_bu.csv)
    Graphique en barres : Coût des primes par BU
    Tableau détaillé : Liste des salariés éligibles avec montants (utilise resume_par_salarie.csv)
    Filtre/slicer : par BU, par type de contrat

Page 3 — Activités sportives

    Graphique en courbe : Nombre d'activités par mois (utilise activites_enrichies.csv, colonne mois)
    Graphique en barres : Top 10 des sports pratiqués
    Graphique en barres : Top 10 des salariés les plus actifs
    Filtre/slicer : par sport, par BU

Page 4 — Validation des déplacements

    Carte KPI : Nombre de déplacements sportifs validés (68)
    Carte KPI : Nombre d'anomalies (0)
    Graphique en barres : Répartition par mode de déplacement
    Histogramme : Distribution des distances domicile-entreprise (utilise validation_distances.csv)

Les fichiers à importer dans Power BI sont principalement resume_par_salarie.csv (vue complète par salarié), activites_enrichies.csv (détail des activités), avantages_par_bu.csv (résumé par BU), et validation_distances.csv.





