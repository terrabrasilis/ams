import os
import sys
path = os.path.join(os.path.dirname(__file__), os.pardir)
sys.path.append(path)

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
