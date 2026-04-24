"""
Pydantic v1 Schemas (compatible Render/Python 3.12, pas de Rust)
"""
from datetime import date, datetime
from typing import Optional, Literal

from pydantic import BaseModel, Field, validator, EmailStr


class MicroFermeCreate(BaseModel):
    nom: str = Field(..., min_length=3, max_length=100)
    proprietaire: str = Field(..., min_length=2, max_length=100)
    telephone: Optional[str] = Field(None, regex=r'^\+?[\d\s-]{8,}$')
    email: Optional[EmailStr] = None
    quartier: str = Field(..., min_length=2, max_length=50)
    arrondissement: str = Field(..., regex=r'^(I|II|III|IV|V|VI|VII)$')
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    superficie_m2: float = Field(..., gt=0, le=10000)
    type_culture_principal: Optional[str] = Field(None, max_length=50)

    @validator('telephone')
    def validate_telephone_cm(cls, v):
        if v is None:
            return v
        import re
        cleaned = v.replace(' ', '').replace('-', '')
        if not re.match(r'^(\+237|237)?[6-9][0-9]{8}$', cleaned):
            raise ValueError('Invalid Cameroon phone format')
        return v

    class Config:
        anystr_strip_whitespace = True
        validate_assignment = True


class MicroFermeResponse(BaseModel):
    id: int
    nom: str
    proprietaire: str
    ville: str
    quartier: str
    arrondissement: str
    superficie_m2: float
    rendement_moyen: float
    date_creation: datetime
    active: bool

    class Config:
        orm_mode = True


class RecolteCreate(BaseModel):
    ferme_id: int = Field(..., gt=0)
    culture_type: str = Field(..., min_length=2, max_length=50)
    quantite_kg: float = Field(..., gt=0, le=10000)
    qualite: Literal['A', 'B', 'C'] = 'B'
    date_recolte: date
    prix_vente_kg: Optional[float] = Field(None, ge=0)
    canal_vente: Literal['direct', 'marche', 'cooperative', 'autre'] = 'direct'
    notes: Optional[str] = Field(None, max_length=500)

    @validator('date_recolte')
    def validate_date_past(cls, v):
        from datetime import date as d
        if v > d.today():
            raise ValueError('Harvest date cannot be in the future')
        return v

    @validator('culture_type')
    def normalize_culture(cls, v):
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
    id: int
    ferme_id: int
    culture_type: str
    quantite_kg: float
    qualite: str
    date_recolte: date
    prix_vente_kg: Optional[float]
    canal_vente: str
    valeur_totale: Optional[float] = None

    @validator('valeur_totale', always=True)
    def calculate_value(cls, v, values):
        prix = values.get('prix_vente_kg')
        qte = values.get('quantite_kg')
        if prix and qte:
            return round(prix * qte, 2)
        return None

    class Config:
        orm_mode = True


class DonneeMeteoCreate(BaseModel):
    ferme_id: int = Field(..., gt=0)
    temperature_c: Optional[float] = Field(None, ge=10, le=45)
    humidite_percent: Optional[float] = Field(None, ge=0, le=100)
    precipitation_mm: Optional[float] = Field(None, ge=0, le=500)
    ensoleillement_h: Optional[float] = Field(None, ge=0, le=24)
