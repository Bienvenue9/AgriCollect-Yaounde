"""
Harvest API routes - Flask 3.x + SQLAlchemy 2.0
"""
from flask import Blueprint, request, jsonify, abort, current_app
from sqlalchemy import select, func, extract
from pydantic import ValidationError

from app import db
from app.models import Recolte, MicroFerme
from app.schemas import RecolteCreate, RecolteResponse

harvests_bp = Blueprint('harvests', __name__)


@harvests_bp.get('/')
def list_recoltes() -> dict:
    """List harvests with advanced filters"""
    ferme_id = request.args.get('ferme_id', type=int)
    culture = request.args.get('culture')
    date_debut = request.args.get('date_debut')
    date_fin = request.args.get('date_fin')
    
    stmt = select(Recolte).join(MicroFerme)
    
    if ferme_id:
        stmt = stmt.where(Recolte.ferme_id == ferme_id)
    if culture:
        stmt = stmt.where(Recolte.culture_type.ilike(f'%{culture}%'))
    if date_debut:
        stmt = stmt.where(Recolte.date_recolte >= date_debut)
    if date_fin:
        stmt = stmt.where(Recolte.date_recolte <= date_fin)
    
    stmt = stmt.order_by(Recolte.date_recolte.desc()).limit(100)
    recoltes = db.session.scalars(stmt).all()
    
    return jsonify([
        RecolteResponse.parse_obj(r).dict() for r in recoltes
    ])


@harvests_bp.post('/')
def create_recolte() -> tuple:
    """Create new harvest"""
    try:
        data = RecolteCreate.parse_obj(request.get_json())
        
        # Verify farm exists using session.get() (SQLAlchemy 2.0)
        if not db.session.get(MicroFerme, data.ferme_id):
            return jsonify({'error': 'Farm not found'}), 404
        
        recolte = Recolte(**data.dict())
        db.session.add(recolte)
        db.session.commit()
        
        return jsonify({
            'message': 'Harvest recorded',
            'data': RecolteResponse.parse_obj(recolte).dict()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors(include_url=False)
        }), 400
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error creating harvest: {e}")
        return jsonify({'error': 'Server error'}), 500


@harvests_bp.get('/analytics/production')
def analytics_production() -> list:
    """Monthly production analytics"""
    stmt = select(
        extract('year', Recolte.date_recolte).label('annee'),
        extract('month', Recolte.date_recolte).label('mois'),
        func.sum(Recolte.quantite_kg).label('total_kg'),
        func.avg(Recolte.prix_vente_kg).label('prix_moyen')
    ).group_by(
        'annee', 'mois'
    ).order_by(
        'annee', 'mois'
    )
    
    results = db.session.execute(stmt).all()
    
    return jsonify([{
        'periode': f"{int(row.annee)}-{int(row.mois):02d}",
        'production_kg': round(float(row.total_kg or 0), 2),
        'prix_moyen_fcfa': round(float(row.prix_moyen or 0), 2) if row.prix_moyen else None
    } for row in results])


@harvests_bp.get('/analytics/cultures')
def analytics_cultures():
    """Classement des cultures par volume"""
    from sqlalchemy import func, select
    
    # Requête SQLAlchemy 2.0 corrigée
    stmt = select(
        Recolte.culture_type,
        func.sum(Recolte.quantite_kg).label('volume_total'),
        func.count(Recolte.id).label('nb_recoltes')
    ).group_by(
        Recolte.culture_type
    ).order_by(
        func.sum(Recolte.quantite_kg).desc()
    )
    
    try:
        results = db.session.execute(stmt).all()
        
        # Si pas de résultats
        if not results:
            return jsonify({
                'message': 'Aucune récolte enregistrée',
                'data': []
            }), 200
        
        return jsonify([{
            'culture': row[0],
            'volume_total_kg': round(float(row[1] or 0), 2),
            'nombre_recoltes': row[2]
        } for row in results])
        
    except Exception as e:
        return jsonify({
            'error': 'Erreur lors de l\'analyse',
            'details': str(e)
        }), 500
