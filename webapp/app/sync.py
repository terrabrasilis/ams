from ams.dataaccess import AlchemyDataAccess
from .controllers import InitializerController
from .config import Config

db = AlchemyDataAccess()

def startSync(config=Config):
  db.connect(config.DATABASE_URL)
  InitializerController(db, config.DETER_DAILY_UPDATE_TIME_INTERVAL)