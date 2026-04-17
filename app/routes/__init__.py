"""
Blueprint exports for Flask 3.x
Modern import pattern
"""
from .farms import farms_bp
from .harvests import harvests_bp
from .dashboard import dashboard_bp

__all__ = ['farms_bp', 'harvests_bp', 'dashboard_bp']