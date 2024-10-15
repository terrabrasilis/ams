import json
import os

from ams.save_alerts import prepare_alerts_to_save
from ams.spatial_unit_profile import SpatialUnitProfile
from flask import render_template, request, send_file

from . import bp as app
from .config import Config
from .controllers import AppConfigController


@app.route('/', methods=['GET'])
def get_config():
    try:
        isDevelopmentEnv = os.getenv("FLASK_ENV", "production")
        params = Config.get_params_to_frontend()
        return (
            render_template('index_dev.html', params=params) if (isDevelopmentEnv == "development") else
            render_template('index.html', params=params)
        )
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
        subset = args["subset"]
        municipality = args["municipality"]
    except KeyError as ke:
        # exception KeyError
        # Raised when a mapping (dictionary) key is not found in the set of existing keys.
        # HTTP 412: Precondition Failed
        return "Input parameters are missing: {0}".format(str(ke)), 412

    try:
        dburl = Config.DB_URL
        ctrl = AppConfigController(dburl)

        biomes = ctrl.read_biomes()  # all biomes
        municipalities = ctrl.read_municipalities()  # all municipalities (group or municipality names)

        if subset == "Bioma":
            selected_biomes = json.dumps([appBiome])
            municipality = "ALL"
            sui_subset = ctrl.read_spatial_units_for_subset(subset=subset, biome=appBiome)
        else:
            selected_biomes = ctrl.read_municipality_biomes(municipality)
            appBiome = ','.join(json.loads(selected_biomes))
            sui_subset = ctrl.read_spatial_units_for_subset(subset=subset)

        ldu = ctrl.read_land_uses()

        cg = ctrl.read_class_groups(biomes=json.loads(selected_biomes))
        # incluing thresholds in the layer names
        cg = json.loads(cg.replace("'", '"'))

        for _ in cg:
            if _['name'] == 'RK':
                _['title'] += f" (>= {Config.RISK_THRESHOLD:.2f})"
                break
        cg = json.dumps(cg)

        res = {
            'geoserver_url': Config.GEOSERVER_URL,
            'appBiome': appBiome,
            'deter_class_groups': cg,
            'land_uses': ldu,
            'spatial_units_info_for_subset': sui_subset,
            'biomes': biomes,
            'municipalities': municipalities,
            'selected_subset': subset,
            'selected_biomes': selected_biomes,
            'selected_municipality': municipality,
        }

        return json.dumps(res)
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
        name = params['suName']
        land_use = params['landUse']
        # app unit measure
        unit = params['unit']
        appBiome = params['targetbiome']
        riskThreshold = params['riskThreshold']
        municipality = params["municipality"]

    except KeyError as ke:
        # exception KeyError
        # Raised when a mapping (dictionary) key is not found in the set of existing keys.
        # HTTP 412: Precondition Failed
        return "Input parameters are missing: {0}".format(str(ke)), 412

    try:
        spatial_unit_profile = SpatialUnitProfile(Config, params)

        # onlyOneLandUse = (land_use).find(',')
        count = land_use.split(',')
        onlyOneLandUse = len(count) if count[0] != '' else -1

        # to avoid unnecessary function call
        if (spatial_unit_profile._classname != 'RK'):
            if (onlyOneLandUse <= 1):
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
        elif (onlyOneLandUse >= 2 and spatial_unit_profile._classname == 'RK'):
            return json.dumps(
                {'FormTitle': spatial_unit_profile.form_title(),
                 'AreaPerLandUse': spatial_unit_profile.fig_area_per_land_use()}
            )
        else:
            return json.dumps(
                {'FormTitle': 'Sem gráficos para exibir com a configuração atual.'}
            )
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500


def _validate_params(json_str, required_params):
    params = json.loads(json_str)

    for name in required_params:
        if not name in params:
            # exception KeyError
            # Raised when a mapping (dictionary) key is not found in the set of existing keys.
            # HTTP 412: Precondition Failed
            return False, (f"Input parameters are missing: {name}.", 412)
    return True, params


@app.route('/alerts', methods=['GET'])
def get_alerts():
    args = request.args

    status, params_or_error = _validate_params(
        json_str=args.get('sData'),
        required_params=[
            'targetbiome',
            'isAuthenticated',
            'className',
            'spatialUnit',
            'startDate',
            'tempUnit',
            'suName',
            'filenamePrefix',
        ]
    )

    if not status:
        return params_or_error

    try:
        params = params_or_error

        biome = params['targetbiome']
        name = params['suName'].replace('|', ' ')
        if name == biome:
            name = '*'

        zip_data = prepare_alerts_to_save(
            dburl=Config.DB_CERRADO_URL if (
                biome == 'Cerrado') else Config.DB_AMAZON_URL,
            is_authenticated=params['isAuthenticated'],
            spatial_unit=params['spatialUnit'],
            classname=params['className'],
            start_date=params['startDate'],
            temporal_unit=params['tempUnit'],
            name=name,
            custom='custom' in params,
            filename_prefix=params['filenamePrefix']
        )
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500

    return send_file(zip_data, as_attachment=True, download_name="alerts.zip")
