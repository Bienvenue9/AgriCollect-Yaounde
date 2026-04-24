"""
Flask 3.x API routes with SQLAlchemy 2.0 queries
Using modern exception handling and type hints
"""
from flask import Blueprint, request, jsonify, abort, current_app
from sqlalchemy import select, func
from pydantic import ValidationError

from app import db
from app.models import MicroFerme
from app.schemas import MicroFermeCreate, MicroFermeResponse

farms_bp = Blueprint('farms', __name__, url_prefix='/api/farms')


@farms_bp.get('/')
def list_fermes() -> dict:
    """
    List farms with filters - Flask 3.x syntax (.get() instead of .route())
    SQLAlchemy 2.0 style queries using select()
    """
    # Query parameters
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)
    quartier = request.args.get('quartier')
    arrondissement = request.args.get('arrondissement')
    active_only = request.args.get('active', 'true').lower() == 'true'
    
    # Build query using SQLAlchemy 2.0 select()
    stmt = select(MicroFerme)
    
    if quartier:
        stmt = stmt.where(MicroFerme.quartier.ilike(f'%{quartier}%'))
    if arrondissement:
        stmt = stmt.where(MicroFerme.arrondissement == arrondissement)
    if active_only:
        stmt = stmt.where(MicroFerme.active.is_(True))
    
    # Order and paginate
    stmt = stmt.order_by(MicroFerme.date_creation.desc())
    
    # Execute with pagination
    result = db.paginate(stmt, page=page, per_page=per_page, error_out=False)
    
    # Serialize using Pydantic v2
    items = [MicroFermeResponse.parse_obj(f).model_dump() for f in result.items]
    
    return jsonify({
        'data': items,
        'pagination': {
            'total': result.total,
            'pages': result.pages,
            'current_page': page,
            'per_page': per_page
        }
    })


@farms_bp.get('/<int:farm_id>')
def get_ferme(farm_id: int) -> dict:
    """Get single farm by ID using SQLAlchemy 2.0 session.get()"""
    ferme = db.session.get(MicroFerme, farm_id)
    
    if ferme is None:
        abort(404, description="Farm not found")
    
    return jsonify(MicroFermeResponse.parse_obj(ferme).model_dump())


@farms_bp.post('/')
def create_ferme() -> tuple:
    """Create new farm with Pydantic v2 validation"""
    try:
        # Validate input
        data = MicroFermeCreate.parse_obj(request.get_json())
        
        # Check uniqueness using SQLAlchemy 2.0 exists()
        exists_stmt = select(MicroFerme).where(
            MicroFerme.nom == data.nom,
            MicroFerme.quartier == data.quartier
        )
        if db.session.scalar(exists_stmt):
            return jsonify({'error': 'Farm already exists in this neighborhood'}), 409
        
        # Create instance
        ferme = MicroFerme(**data.model_dump())
        db.session.add(ferme)
        db.session.commit()
        
        return jsonify({
            'message': 'Farm created successfully',
            'data': MicroFermeResponse.parse_obj(ferme).model_dump()
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'error': 'Validation failed',
            'details': e.errors(include_url=False)
        }), 400
    except Exception as e:
        db.session.rollback()
        # Flask 3.x logging
        current_app.logger.error(f"Error creating farm: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@farms_bp.put('/<int:farm_id>')
def update_ferme(farm_id: int) -> dict:
    """Update existing farm"""
    ferme = db.session.get(MicroFerme, farm_id)
    if not ferme:
        abort(404)
    
    try:
        data = MicroFermeCreate.parse_obj(request.get_json())
        
        # Update fields
        for key, value in data.model_dump().items():
            setattr(ferme, key, value)
        
        db.session.commit()
        return jsonify({
            'message': 'Farm updated',
            'data': MicroFermeResponse.parse_obj(ferme).model_dump()
        })
        
    except ValidationError as e:
        return jsonify({'error': 'Validation failed', 'details': e.errors()}), 400


@farms_bp.delete('/<int:farm_id>')
def delete_ferme(farm_id: int) -> dict:
    """Soft delete (deactivate) farm"""
    ferme = db.session.get(MicroFerme, farm_id)
    if not ferme:
        abort(404)
    
    ferme.active = False
    db.session.commit()
    return jsonify({'message': f'Farm {ferme.nom} deactivated'})


@farms_bp.get('/stats/arrondissements')
def stats_by_arrondissement() -> list:
    """Aggregate stats using SQLAlchemy 2.0 func"""
    stmt = select(
        MicroFerme.arrondissement,
        func.count(MicroFerme.id).label('nb_fermes'),
        func.sum(MicroFerme.superficie_m2).label('superficie_totale')
    ).where(
        MicroFerme.active.is_(True)
    ).group_by(MicroFerme.arrondissement)
    
    results = db.session.execute(stmt).all()
    
    return jsonify([{
        'arrondissement': row.arrondissement,
        'nombre_fermes': row.nb_fermes,
        'superficie_totale_m2': round(float(row.superficie_totale or 0), 2)
    } for row in results])