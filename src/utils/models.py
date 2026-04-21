"""
Modèles SQLAlchemy — Définition des tables de la base de données.
Compatible SQLAlchemy 1.4+ et 2.0+.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    Date,
    DateTime,
    Text,
    ForeignKey,
    CheckConstraint,
)
from sqlalchemy.orm import relationship

from src.utils.database import Base


class Salarie(Base):
    """Table des salariés — données RH."""

    __tablename__ = "salaries"

    id_salarie = Column(Integer, primary_key=True)
    nom = Column(String(100), nullable=False)
    prenom = Column(String(100), nullable=False)
    date_naissance = Column(Date, nullable=False)
    bu = Column(String(50), nullable=False)
    date_embauche = Column(Date, nullable=False)
    salaire_brut = Column(Float, nullable=False)
    type_contrat = Column(String(10), nullable=False)
    nb_jours_cp = Column(Integer, nullable=False)
    adresse_domicile = Column(String(255), nullable=False)
    moyen_deplacement = Column(String(100), nullable=False)

    sport_pratique = relationship(
        "SportPratique", back_populates="salarie", uselist=False
    )
    activites = relationship("Activite", back_populates="salarie")

    def __repr__(self):
        return f"<Salarie {self.id_salarie} - {self.prenom} {self.nom}>"


class SportPratique(Base):
    """Table des sports pratiqués — déclaratif salarié."""

    __tablename__ = "sports_pratiques"

    id_salarie = Column(Integer, ForeignKey("salaries.id_salarie"), primary_key=True)
    sport = Column(String(100), nullable=True)

    salarie = relationship("Salarie", back_populates="sport_pratique")

    def __repr__(self):
        return f"<SportPratique {self.id_salarie} - {self.sport}>"


class Activite(Base):
    """Table des activités sportives — données simulées type Strava."""

    __tablename__ = "activites"

    id = Column(Integer, primary_key=True, autoincrement=True)
    id_salarie = Column(Integer, ForeignKey("salaries.id_salarie"), nullable=False)
    date_debut = Column(DateTime, nullable=False)
    sport_type = Column(String(100), nullable=False)
    distance_m = Column(Float, nullable=True)
    temps_ecoule_s = Column(Integer, nullable=True)
    commentaire = Column(Text, nullable=True)

    __table_args__ = (
        CheckConstraint(
            "distance_m >= 0 OR distance_m IS NULL", name="check_distance_positive"
        ),
        CheckConstraint(
            "temps_ecoule_s >= 0 OR temps_ecoule_s IS NULL", name="check_temps_positif"
        ),
    )

    salarie = relationship("Salarie", back_populates="activites")

    def __repr__(self):
        return f"<Activite {self.id} - {self.id_salarie} - {self.sport_type}>"
