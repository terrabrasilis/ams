import json
import os

from datetime import datetime

from ams.save_alerts import prepare_alerts_to_save
from ams.spatial_unit_profile import SpatialUnitProfile
from flask import render_template, request, send_file

from . import bp as app
from .config import Config
from .controllers import AppConfigController


@app.route('/', methods=['GET'])
def index():
    return _render_template()

def _render_template(params: dict={}):
    try:
        isDevelopmentEnv = os.getenv("FLASK_ENV", "production")
        params.update(Config.get_params_to_frontend())
        return (
            render_template('index_dev.html', params=params) if (isDevelopmentEnv == "development") else
            render_template('index.html', params=params)
        )
    except Exception as e:
        # HTTP 500: Internal error
        return "Template configurations are missing: {0}".format(str(e)), 412


def _validate_params(json_str, required_params):
    params = json.loads(json_str)

    for name in required_params:
        if not name in params:
            # exception KeyError
            # Raised when a mapping (dictionary) key is not found in the set of existing keys.
            # HTTP 412: Precondition Failed
            return False, (f"Input parameters are missing: {name}.", 412)
    return True, params


def _get_config(
    biome: str,
    subset: str,
    municipalities_group: str,
    geocodes: str,
    is_authenticated: bool,
    municipality_panel_mode: bool,
    start_date: str="",
    end_date: str="",
    temp_unit: str="",
    classname: str="",
):
    dburl = Config.DB_URL
    ctrl = AppConfigController(dburl)

    biomes = ctrl.read_biomes()  # all biomes
    selected_geocodes = geocodes.split(",")

    if subset == "Bioma":
        selected_biomes = json.dumps([biome])
        municipalities_group = "ALL"
        sui_subset = ctrl.read_spatial_units_for_subset(subset=subset, biome=biome)
        cg = ctrl.read_class_groups(biomes=[biome])
    else:
        selected_biomes = json.dumps(["ALL"])
        biome = "ALL"
        sui_subset = ctrl.read_spatial_units_for_subset(
            subset="Munic\xedpios",
            exclude=(
                ["cs_150km", "municipalities",]
                if municipality_panel_mode or (municipalities_group == "customizado" and len(selected_geocodes) < 2)
                else ""
            )
        )
        mbiomes = ctrl.read_municipalities_biome(geocodes=
            selected_geocodes if municipalities_group == "customizado" else ctrl.read_municipalities_geocode(municipality_group=municipalities_group)
        )
        cg = ctrl.read_class_groups(biomes=mbiomes)

    publish_date = (
        ctrl.read_publish_date(biomes=json.loads(selected_biomes)) if not is_authenticated else
        datetime.now().strftime("%Y-%m-%d")
    )

    ldu = ctrl.read_land_uses(land_use_type="ams")

    # incluing thresholds in the layer names
    cg = json.loads(cg.replace("'", '"'))
    for _ in cg:
        if _['name'] == 'RK':
            _['title'] += f" (>= {Config.RISK_THRESHOLD:.2f})"
            break
    cg = json.dumps(cg)

    bbox = ctrl.read_bbox(
        subset=subset, biome=biome, municipalities_group=municipalities_group, geocodes=geocodes
    )

    return {
        'geoserver_url': Config.GEOSERVER_URL,
        'appBiome': biome,
        'deter_class_groups': cg,
        'land_uses': ldu,
        'spatial_units_info_for_subset': sui_subset,
        'biomes': biomes,
        'bbox': bbox,
        'municipalities_group': ctrl.read_municipalities_group(),
        'selected_subset': subset,
        'selected_biomes': selected_biomes,
        'selected_municipalities_group': municipalities_group,
        'publish_date': publish_date,
        'selected_geocodes': json.dumps(selected_geocodes),
        'all_municipalities': ctrl.read_municipalities(biomes=json.loads(biomes)),
        'municipality_panel_mode': json.dumps(municipality_panel_mode),
        'selected_municipality': (
            ctrl.read_municipality_name(geocode=selected_geocodes[0])
            if geocodes.strip() and len(selected_geocodes)==1 else ""
        ),
        'start_date': start_date,
        'end_date': end_date,
        'temp_unit': temp_unit,
        'classname': classname,
    }


@app.route('/biome/<endpoint>', methods=['GET'])
def get_config(endpoint):
    if endpoint != 'config':
        return "Bad endpoint", 404

    status, params_or_error = _validate_params(
        json_str = json.dumps(dict(request.args)),
        required_params=[
            "targetbiome",
            "subset",
            "municipalitiesGroup",
            "isAuthenticated",
            "geocodes",
            "municipalityPanelMode"
        ]
    )

    if not status:
        return params_or_error

    try:
        params = params_or_error

        conf = _get_config(
            biome=params["targetbiome"],
            subset=params["subset"],
            municipalities_group=params["municipalitiesGroup"],
            geocodes=params["geocodes"],
            is_authenticated=params['isAuthenticated'].lower() == "true",
            municipality_panel_mode=params["municipalityPanelMode"].lower() == "true",
            start_date=params["startDate"],
            end_date=params["endDate"],
            temp_unit=params["tempUnit"],
            classname=params["classname"],
        )

        return json.dumps(conf)

    except Exception as e:
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500


@app.route('/panel', methods=['GET'])
def set_municipality_panel_mode():
    params = request.args

    if not len(set(params) & {"id", "geocode"}):
        return _render_template(
            params={"error-msg": "Invalid URL parameter. Expected values are 'id' or 'geocode'."}
        )

    dburl = Config.DB_URL
    ctrl = AppConfigController(dburl)

    if "id" in params:
        geocode = ctrl.read_municipality_geocode(su_id=params["id"])
    else:
        geocode = params["geocode"]

    if not ctrl.geocode_is_valid(geocode=geocode):
        return _render_template(
            params={"error-msg": f"Geocódigo {geocode} não encontrado. Verifique se o valor informado está correto."}
        )
    
    params = {
        "municipality-panel": "true",
        "geocode": geocode,
        "start_date": params.get("startDate", ""),
        "end_date": params.get("endDate", ""),
        "temp_unit": params.get("tempUnit", ""),
        "classname": params.get("classname", ""),
    }

    return _render_template(
        params=params
    )

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
        municipalities_group = params["municipalitiesGroup"]
        geocodes = params["geocodes"]

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
                     'AreaPerYearTableClass': spatial_unit_profile.fig_area_by_period(),
                     'AreaPerLandUsePpcdam': spatial_unit_profile.fig_area_per_land_use_ppcdam()}
                )
        elif (onlyOneLandUse >= 2 and spatial_unit_profile._classname == 'RK'):
            return json.dumps(
                {'FormTitle': spatial_unit_profile.form_title(),
                 'AreaPerLandUse': spatial_unit_profile.fig_area_per_land_use(),
                 'AreaPerLandUsePpcdam': spatial_unit_profile.fig_area_per_land_use_ppcdam()}
            )
        else:
            return json.dumps(
                {'FormTitle': 'Sem gráficos para exibir com a configuração atual.'}
            )
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500
 

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
            'municipalitiesGroup',
            'geocodes',
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
            dburl = Config.DB_URL,
            is_authenticated=params['isAuthenticated'],
            spatial_unit=params['spatialUnit'],
            classname=params['className'],
            start_date=params['startDate'],
            temporal_unit=params['tempUnit'],
            name=name,
            custom='custom' in params,
            filename_prefix=params['filenamePrefix'],
            biomes=biome,
            municipalities_group=params['municipalitiesGroup'],
            geocodes=params['geocodes'],
        )
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500

    return send_file(zip_data, as_attachment=True, download_name="alerts.zip")
