from flask import Flask, Blueprint
from flask_cors import CORS
from ams.dataaccess import AlchemyDataAccess
from .controllers import DeterDailyUpdateController
from .config import Config

db = AlchemyDataAccess()
bp = Blueprint('', __name__)

def create_app(config=Config):
	app = Flask(__name__)
	cors = CORS(app)	
	app.config.from_object(config)	
	app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
	db.connect(config.DATABASE_URL)
	app.register_blueprint(bp)
	deter_daily_up = DeterDailyUpdateController(db, config.DETER_DAILY_UPDATE_TIME)
	return app


from . import routes
