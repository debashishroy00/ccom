"""
CCOM CLI Package
Modular command line interface following SOLID principles
"""

from .main import main
from .parser import create_argument_parser

__all__ = ['main', 'create_argument_parser']