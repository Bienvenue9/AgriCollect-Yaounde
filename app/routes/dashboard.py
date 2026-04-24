"""
Web interface routes - Flask 3.x render_template
"""
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from pydantic import ValidationError
from sqlalchemy import select

from app import db
from app.models import MicroFerme, Recolte
from app.schemas import MicroFermeCreate

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.get('/')
def index():
    """Homepage with KPIs"""
    stats = {
        'total_fermes': db.session.scalar(
            select(db.func.count()).select_from(MicroFerme).where(MicroFerme.active.is_(True))
        ),
        'total_recoltes': db.session.scalar(
            select(db.func.count()).select_from(Recolte)
        ),
        'production_totale': db.session.scalar(
            select(db.func.sum(Recolte.quantite_kg))
        ) or 0,
        'dernieres_recoltes': db.session.scalars(
            select(Recolte).order_by(Recolte.date_recolte.desc()).limit(5)
        ).all()
    }
    return render_template('index.html', **stats)

@dashboard_bp.get('/carte')
def carte_fermes():
    """Map showing farms with GPS coordinates"""
    from sqlalchemy import select
    
    # Query only farms with coordinates
    stmt = select(MicroFerme).where(
        MicroFerme.latitude.isnot(None),
        MicroFerme.longitude.isnot(None),
        MicroFerme.active.is_(True)
    )
    fermes = db.session.scalars(stmt).all()
    
    return render_template('carte.html', fermes=fermes)


@dashboard_bp.route('/fermes/nouvelle', methods=['GET', 'POST'])
def nouvelle_ferme_form():
    """Web form for new farm"""
    if request.method == 'POST':
        try:
            # Convert form to dict, handling empty strings as None
            form_data = {
                'nom': request.form.get('nom'),
                'proprietaire': request.form.get('proprietaire'),
                'telephone': request.form.get('telephone') or None,
                'email': request.form.get('email') or None,
                'quartier': request.form.get('quartier'),
                'arrondissement': request.form.get('arrondissement'),
                'latitude': float(request.form['latitude']) if request.form.get('latitude') else None,
                'longitude': float(request.form['longitude']) if request.form.get('longitude') else None,
                'superficie_m2': float(request.form['superficie_m2']),
                'type_culture_principal': request.form.get('type_culture_principal') or None
            }
            
            validated = MicroFermeCreate.parse_obj(form_data)
            ferme = MicroFerme(**validated.dict())
            
            db.session.add(ferme)
            db.session.commit()
            
            flash(f'Farm "{ferme.nom}" created successfully!', 'success')
            return redirect(url_for('dashboard.index'))
            
        except ValidationError as e:
            for error in e.errors():
                field = error['loc'][0] if error['loc'] else 'field'
                flash(f"{field}: {error['msg']}", 'danger')
        except Exception as e:
            flash(f'Error: {str(e)}', 'danger')
            db.session.rollback()
    
    return render_template('forms/ferme_form.html')