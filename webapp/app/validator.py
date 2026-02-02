from datetime import datetime
from marshmallow import Schema, fields, validate, ValidationError, validates_schema
from functools import partial

import json
import re

from .config import Config
from .controllers import AppConfigController


VALID_PARMS_FROM_DB = {}


def _load_valid_params_from_db():
    global VALID_PARMS_FROM_DB
    
    try:
        controller = AppConfigController(db_url=Config.DB_URL)

        VALID_PARMS_FROM_DB["targetbiome"] = ["ALL", "all"] + json.loads(controller.read_biomes())
        VALID_PARMS_FROM_DB["municipalitiesGroup"] = (
            ["ALL"] +
            json.loads(controller.read_municipalities_group(gtype="user-defined")) +
            json.loads(controller.read_municipalities_group(gtype="state"))
        )
        VALID_PARMS_FROM_DB["classname"] = [""] + json.loads(controller.read_classnames())
        VALID_PARMS_FROM_DB["spatialUnit"] = (
            ["ALL"] +
            json.loads(controller.read_biomes()) +
            json.loads(controller.read_spatial_units())
        )
        VALID_PARMS_FROM_DB["suName"] = (
            ["ALL"] +
            json.loads(controller.read_biomes()) +
            controller.read_spatial_unit_names()
        )

    except Exception as e:
        print(f"There was an error loading the validation parameters from the database ({e}).")


_load_valid_params_from_db()


def update_validators():
    _load_valid_params_from_db()


def _validate_date(allow_empty: bool, value: str):
    if allow_empty and not len(value.strip()):
        return
    try:
        _ = datetime.strptime(value,  "%Y-%m-%d")
    except Exception as e:
        print(e)
        raise ValidationError(f"Date ({value})")


def _validate_geocodes(value: str):
    if len(value.strip()) == 0:
        return

    if sum([not _.isdigit() for _ in value.split(",")]) > 0:
        ValidationError(f"geocodes ({value})")

    controller = AppConfigController(db_url=Config.DB_URL)

    for geocode in value.split(","):
        if not controller.geocode_is_valid(geocode=geocode):
            raise ValidationError(f"geocode ({geocode})")


def _validate_suname(value: str):
    if re.match(r'^C\d{2,3}L\d{2,3}$', value):
        return
    
    value = value.replace("|", " ")
    
    if value in VALID_PARMS_FROM_DB['suName']:
        return

    raise ValidationError(f"suName ({value})")


def _validate_landuse(value: str):
    if len(value.strip()) == 0:
        return
    
    for land_use in value.split(","):
        if not land_use.isdigit():
            raise ValidationError(f"landUse ({value})")


def format_validation_error(err):
    formatted_error_msg = ""
    for field, errors in err.items():
        formatted_error_msg += f"Erro no campo: '{field}': {', '.join(errors)}\n"
    return formatted_error_msg


def _validate_prefix(value: str):
    if re.match(r'^\S+$', value):
        return
    
    raise ValidationError(f"prefixFilename ({value})")


class BiomeConfigSchema(Schema):
    global VALID_PARMS_FROM_DB

    targetbiome = fields.Str(
        required=True,
        validate=validate.OneOf(VALID_PARMS_FROM_DB['targetbiome'])
    )
    subset = fields.Str(
        required=True,
        validate=validate.OneOf(["Bioma", "Municípios de Interesse", "Estado"])
    )
    municipalitiesGroup = fields.Str(
        required=True,
        validate=validate.OneOf(VALID_PARMS_FROM_DB["municipalitiesGroup"])
    )
    geocodes = fields.Str(
        required=False,
        validate=_validate_geocodes,
    )
    municipalityPanelMode = fields.Bool()
    startDate = fields.Str(required=True, validate=partial(_validate_date, True))
    endDate = fields.Str(required=True, validate=partial(_validate_date, True))
    tempUnit = fields.Str(required=True)
    classname = fields.Str(required=True, validate=validate.OneOf(VALID_PARMS_FROM_DB["classname"]))
    isAuthenticated = fields.Bool(required=False)

    @validates_schema
    def _validate_others(self, data, **kwargs):
        _ = kwargs  # no warn
        value = data["tempUnit"]
        if not (
            value[:-1].isdigit() and value[-1] == "d" if "custom" in data else
            value in ["7d", "15d", "1m", "3m", "1y", "custom"]
        ):
            raise ValidationError(f"tempUnit ({value})", "tempUnit")


class PanelSchema(Schema):
    global VALID_PARMS_FROM_DB

    id = fields.Int(required=False)
    geocode = fields.Int(required=False)
    startDate = fields.Str(required=False, validate=partial(_validate_date, True))
    endDate = fields.Str(required=False, validate=partial(_validate_date, True))
    tempUnit = fields.Str(required=False)
    classname = fields.Str(required=False, validate=validate.OneOf(VALID_PARMS_FROM_DB["classname"]))

    @validates_schema
    def _validate_others(self, data, **kwargs):
        _ = kwargs  # no warn

        controller = AppConfigController(db_url=Config.DB_URL)

        if not "id" in data and not "geocode" in data:
            raise ValidationError(
                "O parâmetro informado na URL é inválido. Por favor, utilize 'id' ou 'geocode'.", "geocode"
            )

        if "id" in data:
            geocode = controller.read_municipality_geocode(su_id=data["id"])
        else:
            geocode = data["geocode"]

        if not controller.geocode_is_valid(geocode=geocode):
            raise ValidationError(
                 f"Geocódigo '{geocode}' não foi encontrado. Por favor, verifique se o valor está correto e tente novamente.",
                 "geocode"
            )
        
        if not "tempUnit" in data:
            return
        
        value = data["tempUnit"]
        if not (
            value[:-1].isdigit() and value[-1] == "d" if "custom" in data else
            value in ["7d", "15d", "1m", "3m", "1y"]
        ):
            raise ValidationError(f"tempUnit ({value})", "tempUnit")


class IndicatorsSchema(Schema):
    global VALID_PARMS_FROM_DB

    targetbiome = fields.Str(
        required=True,
        validate=validate.OneOf(VALID_PARMS_FROM_DB['targetbiome'])
    )
    className = fields.Str(required=True, validate=validate.OneOf(VALID_PARMS_FROM_DB["classname"]))
    spatialUnit = fields.Str(required=True, validate=validate.OneOf(VALID_PARMS_FROM_DB["spatialUnit"]))
    startDate = fields.Str(required=True, validate=partial(_validate_date, False))
    tempUnit = fields.Str(required=True)
    custom = fields.Bool(required=False)
    suName = fields.Str(required=True, validate=_validate_suname)
    landUse = fields.Str(required=True, validate=_validate_landuse)
    municipalitiesGroup = fields.Str(
        required=True,
        validate=validate.OneOf(VALID_PARMS_FROM_DB["municipalitiesGroup"])
    )
    geocodes = fields.Str(
        required=True,
        validate=_validate_geocodes,
    )
    isAuthenticated = fields.Bool(required=False)
    filenamePrefix=fields.Str(required=True, validate=_validate_prefix)

    @validates_schema
    def _validate_others(self, data, **kwargs):
        _ = kwargs  # no warn
        # temptUnit
        value = data["tempUnit"]
        if not (
            value[:-1].isdigit() and value[-1] == "d" if "custom" in data else
            value in ["7d", "15d", "1m", "3m", "1y"]
        ):
            raise ValidationError(f"tempUnit ({value})", "tempUnit")


class ProfileSchema(Schema):
    global VALID_PARMS_FROM_DB

    className = fields.Str(required=True, validate=validate.OneOf(VALID_PARMS_FROM_DB["classname"]))
    spatialUnit = fields.Str(required=True, validate=validate.OneOf(VALID_PARMS_FROM_DB["spatialUnit"]))
    startDate = fields.Str(required=True, validate=partial(_validate_date, False))
    tempUnit = fields.Str(required=True)    
    suName = fields.Str(required=True, validate=_validate_suname)
    landUse = fields.Str(required=True, validate=_validate_landuse)
    targetbiome = fields.Str(
        required=True,
        validate=validate.OneOf(VALID_PARMS_FROM_DB['targetbiome'])
    )
    municipalitiesGroup = fields.Str(
        required=True,
        validate=validate.OneOf(VALID_PARMS_FROM_DB["municipalitiesGroup"])
    )
    geocodes = fields.Str(
        required=True,
        validate=_validate_geocodes,
    )
    unit = fields.Str(required=True, validate=validate.OneOf(["km²", "ha", "focos", "risco", "score"]))
    riskThreshold = fields.Float(required=False)
    custom = fields.Bool(required=False)

    @validates_schema
    def _validate_others(self, data, **kwargs):
        _ = kwargs  # no warn
        # temptUnit
        value = data["tempUnit"]
        if not (
            value[:-1].isdigit() and value[-1] == "d" if "custom" in data else
            value in ["7d", "15d", "1m", "3m", "1y"]
        ):
            raise ValidationError(f"tempUnit ({value})", "tempUnit")
