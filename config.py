"""
Configuration for Python 3.14 + Flask 3.1.3
Using modern dataclasses and type hints
"""
import os
from dataclasses import dataclass, field
from typing import Self


@dataclass(frozen=True)
class Config:
    """Immutable configuration using dataclass (Python 3.7+)"""
    SECRET_KEY: str = os.environ.get('SECRET_KEY', 'dev-secret-key-yaounde1')
    SQLALCHEMY_DATABASE_URI: str = os.environ.get(
        'DATABASE_URL', 
        'sqlite:///agricollect.db'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS: bool = False
    SQLALCHEMY_ENGINE_OPTIONS:  dict = field(default_factory=lambda: {
        'pool_pre_ping': True, 
        'pool_recycle': 300
    })
    
    def __post_init__(self):
        if self.SQLALCHEMY_ENGINE_OPTIONS is None:
            object.__setattr__(
                self, 
                'SQLALCHEMY_ENGINE_OPTIONS', 
                {'pool_pre_ping': True, 'pool_recycle': 300}
            )

    @classmethod
    def from_env(cls) -> Self:
        """Factory method for environment-based config"""
        return cls()


class DevelopmentConfig(Config):
    DEBUG: bool = True
    SQLALCHEMY_ECHO: bool = True


class ProductionConfig(Config):
    DEBUG: bool = False
    # Render provides DATABASE_URL automatically
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///agricollect.db'


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}