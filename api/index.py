"""
Vercel Entry Point - Routes all requests to server.py
"""
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the FastAPI app from server.py
from server import app

# Export for Vercel
__all__ = ['app']
