from flask import render_template, url_for, request
from ams.usecases import GetConfig
from . import bp as app
from . import db


@app.route('/', methods=['GET'])
def get_config():
	uc = GetConfig()
	config = uc.execute(db)
	return render_template('index.html', 
						workspace=config.workspace, 
						spatial_units=config.spatial_units)