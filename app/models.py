"""
SQLAlchemy 2.0 ORM Models
Using mapped_column, Mapped types, and modern Python 3.14 syntax
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import String, Float, DateTime, Date, Boolean, Text, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column, relationship, WriteOnlyMapped

from app import db


class MicroFerme(db.Model):
    """
    Modern SQLAlchemy 2.0 model using Mapped[] types
    Compatible with Python 3.14 type hint syntax
    """
    __tablename__ = 'micro_fermes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    nom: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    proprietaire: Mapped[str] = mapped_column(String(100), nullable=False)
    telephone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    
    # Location data (Yaoundé coordinates)
    quartier: Mapped[str] = mapped_column(String(50), nullable=False)
    arrondissement: Mapped[str] = mapped_column(String(50), nullable=False)
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    # Characteristics
    superficie_m2: Mapped[float] = mapped_column(Float, nullable=False)
    type_culture_principal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    date_creation: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    
    # Relationships - SQLAlchemy 2.0 style
    # WriteOnlyMapped for efficient large collection handling
    recoltes: WriteOnlyMapped[List["Recolte"]] = relationship(
        back_populates="ferme",
        cascade="all, delete-orphan",
        lazy="noload"  # Explicit loading strategy
    )
    
    donnees_meteo: WriteOnlyMapped[List["DonneeMeteo"]] = relationship(
        back_populates="ferme",
        lazy="noload"
    )
    
    def __repr__(self) -> str:
        return f'<MicroFerme({self.nom!r}, {self.quartier!r})>'
    
    @property
    def rendement_moyen(self) -> float:
        """
        Calculate average yield using modern Python 3.14+ syntax
        Using walrus operator and sum() with generator
        """
        if not (recoltes_list := db.session.scalars(
            db.select(Recolte).where(Recolte.ferme_id == self.id)
        ).all()):
            return 0.0
        
        total_kg = sum(r.quantite_kg for r in recoltes_list)
        return round(total_kg / self.superficie_m2, 2) if self.superficie_m2 else 0.0


class Recolte(db.Model):
    """Harvest data with SQLAlchemy 2.0 mapped columns"""
    __tablename__ = 'recoltes'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ferme_id: Mapped[int] = mapped_column(ForeignKey('micro_fermes.id'), nullable=False)
    
    # Production data
    culture_type: Mapped[str] = mapped_column(String(50), nullable=False)
    quantite_kg: Mapped[float] = mapped_column(Float, nullable=False)
    qualite: Mapped[str] = mapped_column(String(1), default='B')  # A, B, C
    date_recolte: Mapped[Date] = mapped_column(Date, nullable=False)
    
    # Economic data (FCFA)
    prix_vente_kg: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    canal_vente: Mapped[Optional[str]] = mapped_column(
        String(20), 
        nullable=True,
        default='direct'
    )
    
    # Metadata
    date_saisie: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    saisi_par: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Relationship
    ferme: Mapped["MicroFerme"] = relationship(back_populates="recoltes")
    
    def __repr__(self) -> str:
        return f'<Recolte({self.culture_type!r}, {self.quantite_kg}kg)>'


class DonneeMeteo(db.Model):
    """Local weather conditions"""
    __tablename__ = 'donnees_meteo'
    
    id: Mapped[int] = mapped_column(primary_key=True)
    ferme_id: Mapped[int] = mapped_column(ForeignKey('micro_fermes.id'), nullable=False)
    
    date_enregistrement: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    temperature_c: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    humidite_percent: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    precipitation_mm: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    ensoleillement_h: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    source: Mapped[str] = mapped_column(String(50), default='manuel')
    
    ferme: Mapped["MicroFerme"] = relationship(back_populates="donnees_meteo")