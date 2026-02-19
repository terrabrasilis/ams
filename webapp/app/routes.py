import json
import os

from marshmallow import ValidationError

from ams.save_indicators import prepare_indicators_to_save
from ams.spatial_unit_profile import SpatialUnitProfile
from flask import render_template, request, send_file, g, jsonify

from . import bp as app
from .config import Config
from .controllers import AppConfigController

from .validator import BiomeConfigSchema, PanelSchema, IndicatorsSchema, ProfileSchema, format_validation_error, update_validators

import uuid
import time


@app.route('/', methods=['GET'])
def index():
    update_validators()
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


def _get_config(
    biome: str,
    subset: str,
    municipalities_group: str,
    geocodes: str,
    municipality_panel_mode: bool,
    start_date: str="",
    end_date: str="",
    temp_unit: str="",
    classname: str="",
):
    dburl = Config.DB_URL

    ctrl = AppConfigController(dburl)

    if not ctrl.is_connected():
        return {}
    
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
        'municipalities_group': ctrl.read_municipalities_group(gtype="user-defined"),
        'states_group': ctrl.read_municipalities_group(gtype="state", customized=False),
        'selected_subset': subset,
        'selected_biomes': selected_biomes,
        'selected_municipalities_group': municipalities_group,
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
        return "Bad endpoint.", 404
    
    # print(f"/biome/config __\n{request.args}")
    schema = BiomeConfigSchema()
    
    try:
        schema.load(request.args)
    except ValidationError as e:
        print(e)
        return format_validation_error(e.messages), 400
    
    try:
        params = request.args
        conf = _get_config(
            biome=params["targetbiome"],
            subset=params["subset"],
            municipalities_group=params["municipalitiesGroup"],
            geocodes=params["geocodes"],
            municipality_panel_mode=params["municipalityPanelMode"].lower() == "true",
            start_date=params["startDate"],
            end_date=params["endDate"],
            temp_unit=params["tempUnit"],
            classname=params["classname"],
        )

        if not conf:
            return "Erro no carregamento do config.", 500

        return json.dumps(conf)

    except Exception as e:
        print(e)
        return "Erro no carregamento do config.", 500


@app.route('/panel', methods=['GET'])
def set_municipality_panel_mode():
    # print(f"/panel __ \n {request.args}")
    schema = PanelSchema()

    try:
        schema.load(request.args)
    except ValidationError as e:
        print(e)
        return _render_template(params={"error-msg": format_validation_error(e.messages)})

    try:
        ctrl = AppConfigController(db_url=Config.DB_URL)

        params = request.args

        if "id" in params:
            geocode = ctrl.read_municipality_geocode(su_id=params["id"])
        else:
            geocode = params["geocode"]
   
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
    
    except Exception as e:
        print(e)
        return _render_template(
            params={"error-msg": "Ocorreu um erro no servidor ao carregar a sala de situação municipal."}
        )


@app.route('/callback/<endpoint>', methods=['GET'])
def get_profile(endpoint):
    if endpoint != 'spatial_unit_profile':
        return "Bad endpoint.", 404
    
    params = request.args.get('sData')
    params = json.loads(params) if params else {}

    schema = ProfileSchema()

    try:
        schema.load(params)
    except ValidationError as e:
        print(e)
        return format_validation_error(e.messages), 400
    
    try:
        if params['tempUnit'] == '0d':
            return json.dumps(
                {'FormTitle': 'Sem gráficos para exibir com a configuração atual.'}
            )

        spatial_unit_profile = SpatialUnitProfile(Config, params)

        # onlyOneLandUse = (land_use).find(',')
        count = params['landUse'].split(',')
        onlyOneLandUse = len(count) if count[0] != '' else -1
        
        graph_json = {
            'FormTitle': spatial_unit_profile.form_title(),
            'AreaPerLandUseProdes': ''            
        }

        if spatial_unit_profile._classname == 'AF':
            graph_json.update({'AreaPerLandUseProdes': spatial_unit_profile.fig_area_per_land_use_prodes()})

        # to avoid unnecessary function call
        if (not spatial_unit_profile._classname in ['RK', 'RI', 'FS']):
            if (onlyOneLandUse <= 1):
                graph_json.update(
                    {'AreaPerYearTableClass': spatial_unit_profile.fig_area_by_period()}
                )
            else:
                graph_json.update(
                    {
                        'AreaPerLandUse': spatial_unit_profile.fig_area_per_land_use(),
                        'AreaPerYearTableClass': spatial_unit_profile.fig_area_by_period(),
                        'AreaPerLandUsePpcdam': spatial_unit_profile.fig_area_per_land_use_ppcdam()
                    }
                )
        elif (onlyOneLandUse >= 2 and (spatial_unit_profile._classname in ['RK', 'RI', 'FS'])):
            graph_json.update(
                {
                    'AreaPerLandUse': spatial_unit_profile.fig_area_per_land_use(),
                    'AreaPerLandUsePpcdam': spatial_unit_profile.fig_area_per_land_use_ppcdam()
                }
            )
        else:
            graph_json.update(
                {'FormTitle': 'Sem gráficos para exibir com a configuração atual.'}
            )
        return graph_json
    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500
 

@app.route('/indicators', methods=['GET'])
def get_indicators():
    # print(f"/indicators__ \n {request.args}")
    schema = IndicatorsSchema()

    params = request.args.get('sData')
    params = json.loads(params) if params else {}

    try:
        schema.load(params)
    except ValidationError as e:        
        print(e)
        return format_validation_error(e.messages), 400

    try:
        zip_data = prepare_indicators_to_save(
            dburl = Config.DB_URL,
            is_authenticated=bool(params['isAuthenticated']),
            spatial_unit=params['spatialUnit'],
            classname=params['className'],
            start_date=params['startDate'],
            temporal_unit=params['tempUnit'],
            name=params["suName"],
            custom='custom' in params,
            filename_prefix=params['filenamePrefix'],
            biomes=params["targetbiome"],
            municipalities_group=params['municipalitiesGroup'],
            geocodes=params['geocodes'],
        )

    except Exception as e:
        print(e)
        return "Something is wrong on the server. Please, send this error to our support service: terrabrasilis@inpe.br", 500

    return send_file(zip_data, as_attachment=True, download_name="indicators.zip")


@app.before_request
def request_start():
    """Keep some request information for debugging."""
    if not Config.DEBUG_MODE:
        return
    
    g.request_id = str(uuid.uuid4())[:8] 
    g.start_time = time.time()

    request_debug_info = {
        'url': request.url,
        'method': request.method,
        'path': request.path,
        'query_params': request.args.to_dict(),
        'form_data': request.form.to_dict() if request.form else {},
        'remote_addr': request.remote_addr,
        'user_agent': request.headers.get('User-Agent', 'Unknown')
    }

    print(
        f"[{g.request_id}] START REQUEST: {request.method} {request.path} "
        f"from {request.remote_addr} "
        f"(info: {request_debug_info})"
    )


@app.after_request
def request_finish(response):
    """Calculate the duration of the request."""
    if not Config.DEBUG_MODE:
        return response
    
    duration = int(time.time() - g.start_time) * 1000
    print(f"[{g.request_id}] END REQUEST ({duration} ms).")
    return response
