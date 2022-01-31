from flask import render_template, request
import json

from ams.area_profile import AreaProfile
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


@app.route('/callback/<endpoint>', methods=['GET'])
def get_profile(endpoint):
    try:
        if endpoint == 'area_profile':
            args = request.args
            params = json.loads(args.get('sData'))
            area_profile = AreaProfile(Config, params)
            return json.dumps(
                {'FormTitle': area_profile.form_title(),
                'AreaPerLandUse': area_profile.fig_area_per_land_use(),
                #'AreaPerClass': area_profile.fig_area_per_class(params),
                'AreaPerYearTableClass':
                    area_profile.fig_area_by_period()}
            )
        else:
            return "Bad endpoint", 400
    except Exception as e:
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500
