from flask import render_template
from .controllers import GetConfigController
from .config import Config
from . import bp as app
from . import db


@app.route('/', methods=['GET'])
def get_config():
	ctrl = GetConfigController(db)
	return render_template('index.html', 
						geoserver_url=Config.GEOSERVER_URL,
						workspace=Config.GEOSERVER_WORKSPACE, 
						spatial_units_info=ctrl.spatial_units_info,
						deter_class_groups=ctrl.deter_class_groups)
