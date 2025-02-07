"""Module to save deter alerts."""
from datetime import datetime
from dateutil.relativedelta import relativedelta
import geopandas as gpd
from pathlib import Path
from psycopg2 import connect

import io
import json
import tempfile
import zipfile


def _execute_sql(dburl: str, sql: str):
    # this code is duplicated in the spatial_unit_profile module
    # try to use ams.utils.database_utils
    curr = None
    conn = None
    try:
        conn = connect(dburl)
        curr = conn.cursor()
        curr.execute(sql)
        rows = curr.fetchall()
        return rows[0][0] if rows else None
    except Exception as e:
        raise e
    finally:
        if(not conn.closed): conn.close()


def _get_prev_date_temporal_unit(start_date: str, temporal_unit: str, custom: bool)->str:
    # this code is duplicated in the spatial_unit_profile module, issue #181 is to fix this duplication
    start_date_date = datetime.strptime(start_date, '%Y-%m-%d')

    if custom:
        return (start_date_date + relativedelta(days=-int(temporal_unit[:-1]))).strftime('%Y-%m-%d')
        
    if temporal_unit == '7d': return (start_date_date + relativedelta(days = -7)).strftime('%Y-%m-%d')
    elif temporal_unit == '15d': return (start_date_date + relativedelta(days = -15)).strftime('%Y-%m-%d')
    elif temporal_unit == '1m': return (start_date_date + relativedelta(days = -30)).strftime('%Y-%m-%d')
    elif temporal_unit == '3m': return (start_date_date + relativedelta(days = -90)).strftime('%Y-%m-%d')
    elif temporal_unit == '1y': return (start_date_date + relativedelta(days = -365)).strftime('%Y-%m-%d')

    assert False


def prepare_alerts_to_save(
    dburl: str,
    is_authenticated: bool,
    spatial_unit: str,
    classname: str,
    start_date: str,
    temporal_unit: str,
    name: str,
    custom: bool,
    filename_prefix: str,
    biomes: str,
    municipalities_group: str,
    geocodes: str
):
    """
    Retrieve spatial unit alerts, convert them into a shapefile format, 
    and enable user access for downloading.
    """
    sql="""
    SELECT string_agg('"'||dataname||'":{"description":"'||description||'", "key":"'||as_attribute_name||'"}', ', ')
    FROM public.spatial_units
    """
    suinfo = _execute_sql(dburl=dburl, sql=sql)
    suinfo = suinfo if suinfo is not None else "error:'failure on get infos from database'"
    tableinfo = json.loads("{"+suinfo+"}")
    spatial_unit_table_id = tableinfo[spatial_unit]['key']
    start_period_date = _get_prev_date_temporal_unit(
        start_date=start_date, temporal_unit=temporal_unit, custom=custom
    )

    codes = {
        "DS": ["DESMATAMENTO_CR", "DESMATAMENTO_VEG"],
        "DG": ["CICATRIZ_DE_QUEIMADA", "DEGRADACAO"],
        "CS": ["CS_DESORDENADO", "CS_GEOMETRICO"],
        "MN": ["MINERACAO"],
    }

    # tempdir to save the shapefiles
    temp_dir = Path(tempfile.mkdtemp(prefix="ams-"))

    # alerts geometry
    classname_cond = " OR ".join([f"deter.classname='{_}'" for _ in codes[classname]])
    columns = ",".join(
        [
            f"deter.{_}" for _ in [
                "geom", "gid", "origin_gid", "classname", "date", "areamunkm", "areatotalkm", "areauckm",
                "mun", "uc", "uf"
            ]
        ]
    )

    table = "deter_auth" if is_authenticated else "deter"

    where_biome = f"('{biomes}' = 'ALL' OR deter.biome = ANY ('{{{biomes}}}'))"

    where_municipalities = f""" (
        '{municipalities_group}' = 'ALL' OR deter.geocode =
        ANY(
            SELECT geocode
            FROM public.municipalities_group_members mgm
            WHERE mgm.group_id = (
                SELECT mg.id
                FROM public.municipalities_group mg
                WHERE mg.name='{municipalities_group}'
            )
        )
        OR deter.geocode = ANY('{{{geocodes}}}')
    ) """


    alerts_sql = f'''
    SELECT {columns}
    FROM deter.{table} deter, public."{spatial_unit}" su
    WHERE deter.date > '{start_period_date}' AND deter.date <= '{start_date}'
    AND {where_biome}
    AND {where_municipalities}
    AND su.{spatial_unit_table_id} = '{name}'
    AND ({classname_cond})
    AND NOT ST_IsEmpty(ST_Intersection(deter.geom, su.geometry));
    '''

    alerts_geom = gpd.read_postgis(alerts_sql, dburl)
    alerts_geom["date"] = alerts_geom["date"].astype(str)
    alerts_geom.to_file(temp_dir / f"{filename_prefix}.shp")
    
    # spatial unit geometry
    spatial_unit_sql = f'''
    SELECT geometry as geom, {spatial_unit_table_id}
    FROM public."{spatial_unit}" su
    WHERE su.{spatial_unit_table_id} = '{name}';
    '''

    spatial_unit_geom = gpd.read_postgis(spatial_unit_sql, dburl)
    spatial_unit_geom.to_file(temp_dir / f"{name}.shp")

    # zipping files
    zip_data = io.BytesIO()

    with zipfile.ZipFile(zip_data, mode='w') as zip_file:
        for filename in list(temp_dir.glob("*")):
            zip_file.write(filename, arcname=filename.name)
            filename.unlink()
    temp_dir.rmdir()
    
    zip_data.seek(0)

    return zip_data
