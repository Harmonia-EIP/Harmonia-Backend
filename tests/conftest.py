import sys
from pathlib import Path

# C:\...\Harmonia-Backend
PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Ajoute la racine du projet au sys.path pour que imports comme "services.*" marchent
sys.path.insert(0, str(PROJECT_ROOT))
