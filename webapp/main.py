import os
import sys
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)
from app import create_app  # noqa: E402


app = create_app()
