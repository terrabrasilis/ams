from flask import Flask, Blueprint
from flask_cors import CORS
from .config import Config

bp = Blueprint('ams', __name__)

def create_app(config=Config):
	app = Flask(__name__)
	CORS(app)
	app.config.from_object(config)
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	app.register_blueprint(bp)
	return app

from . import routes
