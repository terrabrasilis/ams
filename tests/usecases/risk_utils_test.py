# Used as entry point to debug the risk_utils.py in localhost during development.
#
# Read data from database
# local test (see environment vars into launch startup definition)
from os import path
from ams.utils.database_utils import DatabaseUtils
from ams.utils.risk_utils import RiskUtils

db_url="postgresql://postgres:postgres@192.168.15.49:5444/AMS4H"

db = DatabaseUtils(db_url=db_url)
ru = RiskUtils(db=db)

# used to avoid uneeded risk processing
risk_file, risk_date = ru.get_last_file_info()
is_new, risk_time_id = ru.first_phase_already(risk_date=risk_date)

if (path.isfile(risk_file) and is_new and risk_time_id is not None):
    print("return True. Proceeding with the risk processing...")
else:
    print("return False. Abort the risk processing...")