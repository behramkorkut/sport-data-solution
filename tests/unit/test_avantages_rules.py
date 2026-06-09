"""
Tests unitaires des règles métier des avantages sportifs.

Couvre la logique pure de ``src/transformation/avantages_rules.py`` :
éligibilité et montant de la prime, éligibilité et nombre de journées
bien-être, y compris les cas limites (seuil exact, arrondis, modes non
sportifs, distance non validée).

Lancement : ``uv run pytest`` (ou ``uv run pytest -v``).
"""

from src.transformation.avantages_rules import (
    MODES_SPORTIFS,
    calcul_jours_bienetre,
    calcul_montant_prime,
    est_eligible_bienetre,
    est_eligible_prime,
)

# ---------------------------------------------------------------------------
# Éligibilité à la prime sportive
# ---------------------------------------------------------------------------


def test_mode_sportif_sans_validation_est_eligible():
    assert est_eligible_prime("Marche/running") is True
    assert est_eligible_prime("Vélo/Trottinette/Autres") is True


def test_mode_non_sportif_n_est_pas_eligible():
    assert est_eligible_prime("Voiture") is False
    assert est_eligible_prime("Transports en commun") is False


def test_mode_sportif_avec_distance_validee_est_eligible():
    assert est_eligible_prime("Marche/running", is_valid=True) is True


def test_mode_sportif_mais_distance_non_validee_n_est_pas_eligible():
    assert est_eligible_prime("Marche/running", is_valid=False) is False


def test_mode_non_sportif_meme_si_distance_validee_n_est_pas_eligible():
    assert est_eligible_prime("Voiture", is_valid=True) is False


def test_tous_les_modes_sportifs_sont_eligibles():
    for mode in MODES_SPORTIFS:
        assert est_eligible_prime(mode) is True


# ---------------------------------------------------------------------------
# Montant de la prime
# ---------------------------------------------------------------------------


def test_prime_egale_a_5_pourcent_du_salaire():
    assert calcul_montant_prime(30000, eligible=True, taux=0.05) == 1500.0


def test_prime_nulle_si_non_eligible():
    assert calcul_montant_prime(30000, eligible=False) == 0.0


def test_prime_arrondie_a_deux_decimales():
    # 33333 * 0.05 = 1666.65
    assert calcul_montant_prime(33333, eligible=True, taux=0.05) == 1666.65


def test_prime_avec_taux_personnalise():
    assert calcul_montant_prime(30000, eligible=True, taux=0.10) == 3000.0


def test_prime_salaire_zero():
    assert calcul_montant_prime(0, eligible=True) == 0.0


# ---------------------------------------------------------------------------
# Éligibilité aux journées bien-être
# ---------------------------------------------------------------------------


def test_bienetre_au_dessus_du_seuil():
    assert est_eligible_bienetre(20, seuil=15) is True


def test_bienetre_exactement_au_seuil_est_eligible():
    # 15 activités = éligible (comparaison >=)
    assert est_eligible_bienetre(15, seuil=15) is True


def test_bienetre_juste_en_dessous_du_seuil_n_est_pas_eligible():
    assert est_eligible_bienetre(14, seuil=15) is False


def test_bienetre_aucune_activite():
    assert est_eligible_bienetre(0, seuil=15) is False


def test_bienetre_seuil_personnalise():
    assert est_eligible_bienetre(10, seuil=10) is True
    assert est_eligible_bienetre(9, seuil=10) is False


# ---------------------------------------------------------------------------
# Nombre de journées bien-être
# ---------------------------------------------------------------------------


def test_jours_bienetre_eligible_donne_5_jours():
    assert calcul_jours_bienetre(True) == 5


def test_jours_bienetre_non_eligible_donne_0_jour():
    assert calcul_jours_bienetre(False) == 0


# ---------------------------------------------------------------------------
# Scénarios bout en bout (enchaînement des règles)
# ---------------------------------------------------------------------------


def test_scenario_cycliste_tres_actif():
    eligible = est_eligible_prime("Vélo/Trottinette/Autres", is_valid=True)
    prime = calcul_montant_prime(40000, eligible, taux=0.05)
    jours = calcul_jours_bienetre(est_eligible_bienetre(18, seuil=15))
    assert eligible is True
    assert prime == 2000.0
    assert jours == 5


def test_scenario_automobiliste_peu_actif():
    eligible = est_eligible_prime("Voiture", is_valid=True)
    prime = calcul_montant_prime(40000, eligible, taux=0.05)
    jours = calcul_jours_bienetre(est_eligible_bienetre(3, seuil=15))
    assert eligible is False
    assert prime == 0.0
    assert jours == 0
