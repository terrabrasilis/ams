from flask import render_template, request
import json
import os;

from ams.spatial_unit_profile import SpatialUnitProfile
from .controllers import AppConfigController
from .config import Config
from . import bp as app

@app.route('/', methods=['GET'])
def get_config():
    try:
        isDevelopmentEnv=os.getenv("FLASK_ENV", "production")
        return render_template('index_dev.html') if(isDevelopmentEnv=="development") else render_template('index.html')
    except Exception as e:
        # HTTP 500: Internal error 
        return "Template configurations are missing: {0}".format(str(e)), 412

@app.route('/biome/<endpoint>', methods=['GET'])
def get_biome_config(endpoint):
    if endpoint != 'config':
        return "Bad endpoint", 404
    args = request.args
    try:
        appBiome = args["targetbiome"]
        dburl = Config.DB_CERRADO_URL if (appBiome=='Cerrado') else Config.DB_AMAZON_URL
        ctrl = AppConfigController(dburl)
        sui=ctrl.read_spatial_units()
        cg=ctrl.read_class_groups()
        ldu=ctrl.read_land_uses()
        return json.dumps(
            {
                'geoserver_url': Config.GEOSERVER_URL,
                'appBiome': appBiome,
                'spatial_units_info':sui,
                'deter_class_groups':cg,
                'land_uses':ldu
            }
        )
    except Exception as e:
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500

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
        land_use=params['landUse']
        # app unit measure
        unit=params['unit']
        appBiome=params['targetbiome']
    except KeyError as ke:
        #exception KeyError
        #Raised when a mapping (dictionary) key is not found in the set of existing keys.
        # HTTP 412: Precondition Failed
        return "Input parameters are missing: {0}".format(str(ke)), 412
    
    try:
        spatial_unit_profile = SpatialUnitProfile(Config, params)
        onlyOneLandUse=(params['landUse']).find(',')
        # to avoid unnecessary function call
        if(onlyOneLandUse<0):
            return json.dumps(
                {'FormTitle': spatial_unit_profile.form_title(),
                'AreaPerYearTableClass': spatial_unit_profile.fig_area_by_period()}
            )
        else:
            return json.dumps(
                {'FormTitle': spatial_unit_profile.form_title(),
                'AreaPerLandUse': spatial_unit_profile.fig_area_per_land_use(),
                'AreaPerYearTableClass': spatial_unit_profile.fig_area_by_period()}
            )
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500
