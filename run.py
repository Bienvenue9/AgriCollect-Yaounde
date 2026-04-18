#!/usr/bin/env python3
"""
Entry point for Python 3.14 + Flask 3.1.3
Modern CLI using Click (integrated with Flask 3.x)
"""
import os
from datetime import date, timedelta
import random

from app import create_app, db
from app.models import MicroFerme, Recolte

# Create app instance
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)


@app.shell_context_processor
def make_shell_context():
    """Shell context for debugging"""
    return {
        'db': db,
        'MicroFerme': MicroFerme,
        'Recolte': Recolte,
        'select': __import__('sqlalchemy').select  # Include select() for SQLAlchemy 2.0
    }


@app.cli.command('init-db')
def init_db():
    """Initialize database tables"""
    with app.app_context():
        db.create_all()
        print('✅ Database initialized successfully')


@app.cli.command('seed')
def seed_data():
    """Seed database with test data"""
    with app.app_context():
        quartiers = ['Essos', 'Mokolo', 'Bastos', 'Obili', 'Nkomkana']
        cultures = ['Gombo', 'Tomate', 'Piment', 'Epinard', 'Aubergine']
        arrondissements = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII']
        
        for i in range(5):
            ferme = MicroFerme(
                nom=f'Ferme Test {i+1}',
                proprietaire=f'Agriculteur {i+1}',
                telephone=f'+237677{random.randint(100000, 999999)}',
                quartier=random.choice(quartiers),
                arrondissement=random.choice(arrondissements),
                superficie_m2=random.uniform(50, 500),
                type_culture_principal=random.choice(cultures),
                latitude=3.8 + random.uniform(-0.1, 0.1),
                longitude=11.5 + random.uniform(-0.1, 0.1)
            )
            db.session.add(ferme)
            db.session.flush()  # Get ID without committing
            
            # Add harvests
            for j in range(3):
                recolte = Recolte(
                    ferme_id=ferme.id,
                    culture_type=ferme.type_culture_principal,
                    quantite_kg=random.uniform(10, 100),
                    qualite=random.choice(['A', 'B', 'C']),
                    date_recolte=date.today() - timedelta(days=random.randint(1, 60)),
                    prix_vente_kg=random.uniform(200, 800),
                    canal_vente=random.choice(['direct', 'marche', 'cooperative'])
                )
                db.session.add(recolte)
        
        db.session.commit()
        print('✅ Test data inserted successfully')


if __name__ == '__main__':
    # Development server with modern Flask 3.x
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=env == 'development',
        use_reloader=True,
        threaded=True
    )

    # For production (Render.com)
if __name__ == '__main__':
    app.run(debug=True)
else:
    # For production servers like Render
    app = create_app('production')