"""
Pydantic v2 Schemas for Python 3.14
Using modern validation patterns and Annotated types
"""
from datetime import date, datetime
from typing import Annotated, Literal

from pydantic import BaseModel, Field, field_validator, EmailStr, ConfigDict
import re


class MicroFermeCreate(BaseModel):
    """
    Pydantic v2 model with Annotated fields and field_validator
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra='forbid'  # Reject extra fields
    )
    
    nom: Annotated[str, Field(min_length=3, max_length=100)]
    proprietaire: Annotated[str, Field(min_length=2, max_length=100)]
    telephone: Annotated[str | None, Field(pattern=r'^\+?[\d\s-]{8,}$')] = None
    email: EmailStr | None = None
    
    # Yaoundé location
    quartier: Annotated[str, Field(min_length=2, max_length=50)]
    arrondissement: Annotated[str, Field(pattern=r'^(I|II|III|IV|V|VI|VII)$')]
    
    # GPS bounds for all the world
    #latitude: Annotated[float | None, Field(default = None, ge=90, le=90)] = None
    #longitude: Annotated[float | None, Field(default = None, ge=180, le=180)] = None
    latitude: float | None = None
    longitude: float | None = None
    
    superficie_m2: Annotated[float, Field(gt=0, le=10000)]
    type_culture_principal: str | None = Field(default=None, max_length=50)
    
    @field_validator('telephone')
    @classmethod
    def validate_telephone_cm(cls, v: str | None) -> str | None:
        """Validate Cameroon phone format"""
        if v is None:
            return v
        
        cleaned = v.replace(' ', '').replace('-', '')
        if not re.match(r'^(\+237|237)?[6-9][0-9]{8}$', cleaned):
            raise ValueError('Invalid Cameroon phone format. Expected: +237 6XX XXX XXX')
        return v
    
    @field_validator('quartier')
    @classmethod
    def normalize_quartier(cls, v: str) -> str:
        """Normalize neighborhood names"""
        return v.title()


class MicroFermeResponse(BaseModel):
    """Response model using Pydantic v2 from_attributes"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    nom: str
    proprietaire: str
    quartier: str
    arrondissement: str
    superficie_m2: float
    rendement_moyen: float
    date_creation: datetime
    active: bool


class RecolteCreate(BaseModel):
    """Harvest creation validation"""
    model_config = ConfigDict(str_strip_whitespace=True)
    
    ferme_id: Annotated[int, Field(gt=0)]
    culture_type: Annotated[str, Field(min_length=2, max_length=50)]
    quantite_kg: Annotated[float, Field(gt=0, le=10000)]
    qualite: Literal['A', 'B', 'C'] = 'B'
    date_recolte: date
    prix_vente_kg: Annotated[float | None, Field(ge=0)] = None
    canal_vente: Literal['direct', 'marche', 'cooperative', 'autre'] = 'direct'
    notes: Annotated[str | None, Field(max_length=500)] = None
    
    @field_validator('date_recolte')
    @classmethod
    def validate_date_past(cls, v: date) -> date:
        if v > date.today():
            raise ValueError('Harvest date cannot be in the future')
        return v
    
    @field_validator('culture_type')
    @classmethod
    def normalize_culture(cls, v: str) -> str:
        """Normalize crop names for Cameroon context"""
        mapping = {
            'gombo': 'Gombo', 'okra': 'Gombo',
            'tomate': 'Tomate', 'tomato': 'Tomate',
            'piment': 'Piment', 'pepper': 'Piment',
            'aubergine': 'Aubergine', 'eggplant': 'Aubergine',
            'epinard': 'Epinard', 'spinach': 'Epinard',
            'mais': 'Maïs', 'corn': 'Maïs'
        }
        return mapping.get(v.lower(), v.title())


class RecolteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    ferme_id: int
    culture_type: str
    quantite_kg: float
    qualite: str
    date_recolte: date
    prix_vente_kg: float | None
    canal_vente: str
    valeur_totale: float | None = None
    
    @field_validator('valeur_totale', mode='before')
    @classmethod
    def calculate_value(cls, v, info) -> float | None:
        data = info.data
        if data.get('prix_vente_kg') and data.get('quantite_kg'):
            return round(data['prix_vente_kg'] * data['quantite_kg'], 2)
        return None


class DonneeMeteoCreate(BaseModel):
    ferme_id: Annotated[int, Field(gt=0)]
    temperature_c: Annotated[float | None, Field(ge=10, le=45)] = None
    humidite_percent: Annotated[float | None, Field(ge=0, le=100)] = None
    precipitation_mm: Annotated[float | None, Field(ge=0, le=500)] = None
    ensoleillement_h: Annotated[float | None, Field(ge=0, le=24)] = None