from flask import render_template, request
import json

from ams.spatial_unit_profile import SpatialUnitProfile
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
    if endpoint != 'spatial_unit_profile':
        return "Bad endpoint", 404

    args = request.args
    try:
        params = json.loads(args.get('sData'))
        # validate if there are required input parameters
        classname = params['className']
        spatial_unit = params['spatialUnit']
        start_date = params['startDate']
        temporal_unit = params['tempUnit']
        name=params['suName']
        # app unit measure
        unit=params['unit']
    except KeyError as ke:
        #exception KeyError
        #Raised when a mapping (dictionary) key is not found in the set of existing keys.
        # HTTP 412: Precondition Failed
        return "Input parameters are missing: {0}".format(str(ke)), 412
    
    try:
        spatial_unit_profile = SpatialUnitProfile(Config, params)
        return json.dumps(
            {'FormTitle': spatial_unit_profile.form_title(),
            'AreaPerLandUse': spatial_unit_profile.fig_area_per_land_use(),
            'AreaPerYearTableClass': spatial_unit_profile.fig_area_by_period()}
        )
    except Exception as e:
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500
