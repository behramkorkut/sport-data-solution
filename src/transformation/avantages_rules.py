"""
Règles métier des avantages sportifs — fonctions pures et testables.

Centralise la logique de calcul utilisée par ``compute_avantages.py`` :

- Prime sportive : 5 % du salaire brut si déplacement sportif validé.
- Journées bien-être : 5 jours si >= 15 activités physiques sur 12 mois.

Ces fonctions ne font aucune entrée/sortie (pas de base de données) :
elles sont déterministes et couvertes par des tests unitaires
(``tests/unit/test_avantages_rules.py``).
"""

import os

# Paramètres métier (surclassables par variables d'environnement)
TAUX_PRIME = float(os.getenv("TAUX_PRIME", "0.05"))
SEUIL_ACTIVITES = int(os.getenv("SEUIL_ACTIVITES", "15"))
JOURS_BIENETRE = int(os.getenv("JOURS_BIENETRE", "5"))

# Modes de déplacement considérés comme « sportifs »
MODES_SPORTIFS = ["Marche/running", "Vélo/Trottinette/Autres"]


def est_eligible_prime(moyen_deplacement, is_valid=None):
    """Détermine l'éligibilité à la prime sportive.

    Args:
        moyen_deplacement: mode de déplacement déclaré par le salarié.
        is_valid: résultat de la validation de distance (Google Maps).
            ``None`` si la validation n'est pas disponible : dans ce cas,
            seule l'appartenance aux modes sportifs est exigée.

    Returns:
        ``True`` si le salarié est éligible à la prime, sinon ``False``.
    """
    eligible_mode = moyen_deplacement in MODES_SPORTIFS
    if is_valid is None:
        return eligible_mode
    return eligible_mode and bool(is_valid)


def calcul_montant_prime(salaire_brut, eligible, taux=TAUX_PRIME):
    """Calcule le montant de la prime sportive.

    Returns:
        ``taux`` % du salaire brut (arrondi à 2 décimales) si éligible,
        sinon ``0.0``.
    """
    if not eligible:
        return 0.0
    return round(salaire_brut * taux, 2)


def est_eligible_bienetre(nb_activites, seuil=SEUIL_ACTIVITES):
    """Éligibilité aux journées bien-être : au moins ``seuil`` activités."""
    return nb_activites >= seuil


def calcul_jours_bienetre(eligible, jours=JOURS_BIENETRE):
    """Nombre de journées bien-être accordées (``jours`` si éligible, sinon 0)."""
    return jours if eligible else 0
