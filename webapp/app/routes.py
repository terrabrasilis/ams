from flask import render_template, request
import json
import os;

from ams.chart import MakeCharts
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
    
    try:
        args = request.args
        appBiome = args["targetbiome"]
    except KeyError as ke:
        #exception KeyError
        #Raised when a mapping (dictionary) key is not found in the set of existing keys.
        # HTTP 412: Precondition Failed
        return "Input parameters are missing: {0}".format(str(ke)), 412

    try:
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
        makeCharts = MakeCharts(Config, params)
        onlyOneLandUse=(land_use).find(',')
        # to avoid unnecessary function call
        if(onlyOneLandUse<0):
            return json.dumps(
                {'FormTitle': makeCharts.get_title4profile(),
                'mainBarChart': makeCharts.fig_area_by_period()}
            )
        else:
            return json.dumps(
                {'FormTitle': makeCharts.get_title4profile(),
                'AreaPerLandUse': makeCharts.fig_area_per_land_use(),
                'mainBarChart': makeCharts.fig_area_by_period()}
            )
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500


@app.route('/api/spatial/unit/<endpoint>', methods=['GET'])
def index(endpoint):
    if endpoint == 'ratio_weight':
        return get_ratio_weight()
    else:
        return "Bad endpoint", 404

def get_ratio_weight():

    args = request.args
    try:
        params = json.loads(args.get('sData'))
        # validate if there are required input parameters
        classname = params['className']
        spatial_unit = params['spatialUnit']
        start_date = params['startDate']
        temporal_unit = params['tempUnit']
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
        makeCharts = MakeCharts(Config, params)
        return json.dumps(
            {'FormTitle': makeCharts.get_title4ratio(),
            'mainBarChart': makeCharts.fig_area_by_ratio_weight()}
        )
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500
