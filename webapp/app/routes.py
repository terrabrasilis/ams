from flask import render_template, url_for, request
from .controllers import GetConfigController
from . import bp as app
from . import db


@app.route('/', methods=['GET'])
def get_config():
	ctrl = GetConfigController(db)
	return render_template('index.html', 
						workspace=ctrl.workspace, 
						spatial_units_info=ctrl.spatial_units_info)