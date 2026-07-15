# -*- coding: utf-8 -*-
from __future__ import annotations
from plotly.graph_objs import layout
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from psycopg2.extensions import connection, cursor
from psycopg2 import connect
import pandas as pd
import plotly
import plotly.express as px
from datetime import datetime
import json
import re
from dateutil.relativedelta import relativedelta
import numpy as np
from babel.dates import format_datetime

from datetime import datetime
from typing import Final
import inspect


def _execute_sql(db_url: str, sql: str):
    curr: cursor | None = None
    conn: connection | None = None

    try:
        conn = connect(db_url)
        curr = conn.cursor()
        curr.execute(sql)
        rows = curr.fetchall()
        return rows[0][0] if rows else None
    except Exception as e:
        raise e
    finally:
        if conn is not None and not conn.closed: # type: ignore
            conn.close() # type: ignore

def _execute_sql_as_dataframe(db_url: str, sql: str):
    return pd.read_sql(sql, db_url)


PROFILE_REGISTRY = {}

def register_profile(key):
    def decorator(cls):
        PROFILE_REGISTRY[key] = cls
        return cls
    return decorator

def create_profile(key, **kwargs):
    try:
        signature = inspect.signature(PROFILE_REGISTRY[key])
        expected = list(dict(signature.parameters).keys())
        _kwargs = {key:value for key, value in kwargs.items() if key in expected}
        return PROFILE_REGISTRY[key](**_kwargs)
    except KeyError:
        raise ValueError(f"Perfil desconhecido: {key}")

class Profile:
    _db_url: str
    _name: str
    _classname: str
    _column: str
    _column_name: str
    _custom: bool
    _spatial_unit: str
    _biome: str
    _temporal_unit: str
    _municipalities_group: str
    _geocodes: str
    _round_factor: int
    _land_use: str
    _custom: bool
    _start_date: str
    _end_date: str
    _unit: str
    _query_limit: Final[int] = 20
    UNIT_KM2: str = "km²"
    UNIT_HA = str = "ha"

    _temporal_unit_desc = {
        "7d": "Agregado 7 dias",
        "15d": "Agregado 15 dias",
        "1m": "Agregado 30 dias",
        "3m": "Agregado 90 dias",
        "1y": "Agregado 365 dias"
    }

    _temporal_unit_sql = {
        7: (
            "select TO_CHAR(date, 'YYYY/WW') as period, classname, "
            "sum(a.{default_column}) as resultsum "
            'from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} '
            "group by TO_CHAR(date, 'YYYY/WW'), classname "
            "order by 1 desc limit {2}"
        ),
        15: (
            "select concat(TO_CHAR(date, 'YYYY'), '/', "
            "to_char(TO_CHAR(date, 'WW')::int/2+1, 'FM00')) as period, "
            "classname, sum(a.{default_column}) as resultsum "
            'from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} '
            "group by concat(TO_CHAR(date, 'YYYY'), '/', "
            "to_char(TO_CHAR(date, 'WW')::int/2+1, 'FM00')), classname "
            "order by 1 desc limit {2}"
        ),
        31: (
            "select TO_CHAR(date, 'YYYY/MM') as period, classname, "
            "sum(a.{default_column}) as resultsum "
            'from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} '
            "group by TO_CHAR(date, 'YYYY/MM'), classname "
            "order by 1 desc limit {2}"
        ),
        124: (
            "select TO_CHAR(date, 'YYYY/Q') as period, classname, "
            "sum(a.{default_column}) as resultsum "
            'from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} '
            "group by TO_CHAR(date, 'YYYY/Q'), classname "
            "order by 1 desc limit {2}"
        ),
        366: (
            "select TO_CHAR(date, 'YYYY') as period, classname, "
            "sum(a.{default_column}) as resultsum "
            'from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} '
            "group by TO_CHAR(date, 'YYYY'), classname "
            "order by 1 desc limit {2}"
        ),
    }
    
    def __init__(
        self,
        db_url: str,
        classname: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        column: str,
        column_name: str,
        round_factor: int,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        self._db_url = db_url
        self._classname = classname
        self._name = name
        self._spatial_unit = spatial_unit
        self._biome = biome
        
        self._land_use = land_use

        self._column = column
        self._column_name = column_name
        self._temporal_unit = temporal_unit or ""
        self._municipalities_group = municipalities_group or ""
        self._geocodes = geocodes or ""
        self._custom = custom or False
        self._start_date = start_date
        self._end_date = end_date

        self._round_factor = round_factor

        self._unit = unit

        days = int(self._temporal_unit[:-1]) if self._custom and self._temporal_unit else 0

        if days not in self._temporal_unit_sql:
            self._temporal_unit_sql[days] = self._temporal_unit_sql[7]
            self._temporal_unit_desc[f"{days}d"] = f"Agregado customizado ({days} dias)"

        self._temporal_unit_period = {
            f"{days}d": (days, 'day', self._query_limit*days),
            '7d': (7, 'day', self._query_limit*7),
            '15d': (15, 'day', self._query_limit*15),
            '1m': (30, 'day', self._query_limit*30),
            '3m': (90, 'day', self._query_limit*90),
            '1y': (365, 'day', self._query_limit*365),
        }

        _start_date = datetime.strptime(self._start_date, '%Y-%m-%d')
        temporal_unit_prev_date = {
            f"{days}d": (_start_date + relativedelta(days=-days)),
            '7d': (_start_date + relativedelta(days=-7)).strftime('%Y-%m-%d'),
            '15d': (_start_date + relativedelta(days=-15)).strftime('%Y-%m-%d'),
            '1m': (_start_date + relativedelta(days=-30)).strftime('%Y-%m-%d'),
            '3m': (_start_date + relativedelta(days=-90)).strftime('%Y-%m-%d'),
            '1y': (_start_date + relativedelta(days=-365)).strftime('%Y-%m-%d'),
        }

        self._start_period_date = temporal_unit_prev_date[self._temporal_unit]

        self._name = self._name.replace('|',' ')
        if self._name == self._biome:
            self._name = '*'

        if self._spatial_unit == self._biome:
            self._spatial_unit = 'states'

        sql = """
            SELECT string_agg('"'||dataname||'":{"description":"'||description||'", "key":"'||as_attribute_name||'"}', ', ')
            FROM public.spatial_units
        """
        su_info = _execute_sql(sql=sql, db_url=self._db_url)
        su_info = su_info if su_info is not None else "error:'failure on get infos from database'"
        self._table_info = json.loads(f"{{{su_info}}}")

    def _read_land_uses(self, land_use_type):
        sql = f"SELECT name FROM public.land_use_{land_use_type} ORDER BY priority"
        return _execute_sql_as_dataframe(db_url=self._db_url, sql=sql)

    def _get_period_settings(self):
        return self._temporal_unit_period.get(self._temporal_unit, (0,0,0))
    
    def _get_indicator_name(self):
        raise NotImplementedError(f"you have to implement this method ({inspect.stack()[0][3]}).")
    
    def _get_customized_description(self):
        geocodes = [_ for _ in self._geocodes.split(",") if _]

        if len(geocodes) > 0:
            if len(geocodes) == 1:
                sql = f"""
                    SELECT name FROM public.municipalities WHERE geocode='{geocodes[0]}';
                """
                return f"para todo o município ({_execute_sql(db_url=self._db_url, sql=sql)})"
            return f"para os municípios selecionados"

        assert self._municipalities_group != "ALL"

        sql = f"""
            SELECT type FROM public.municipalities_group WHERE name='{self._municipalities_group}';
        """

        group_type = _execute_sql(db_url=self._db_url, sql=sql)

        if group_type == "state":
            return f"para todo o estado ({self._municipalities_group})"
        
        return f"para os municípios do grupo selecionado ({self._municipalities_group})"
    
    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        _ = spatial_unit
        _ = spatial_description
        raise NotImplementedError(f"you have to implement this method ({inspect.stack()[0][3]}).")
    
    def get_chart_main_title(self):
        if self._name == '*':
            if self._municipalities_group == 'ALL':
                spatial_unit = 'para todos os biomas' if self._biome == 'ALL' else 'para todo o bioma'
                spatial_description = "" if self._biome == 'ALL' else f" ({self._biome})"
            else:
                spatial_unit = self._get_customized_description()
                spatial_description = f" ({self._biome})" if self._municipalities_group == 'ALL' else ""
        else:
            spatial_unit = f"com recorte na unidade espacial <b>{self._name}</b>"
            spatial_description = f" ({self._table_info[self._spatial_unit]['description']})"

        return self._get_chart_description(spatial_unit, spatial_description)
    
    def _get_chart_by_period_title(self):
        indicator = self._get_indicator_name()
        unit = self._temporal_unit_desc[self._temporal_unit]

        return f"""
            Evolução temporal de <b>{indicator}</b> para os períodos do
            <br><b>{unit}</b> (limitado aos últimos {self._query_limit} períodos).
        """
    
    def _add_chart_by_period_labe_columnl(self, dfr: pd.DataFrame):
        dfr["label"] = dfr[self._column_name]
        
        if self._unit == "ha":
            dfr[self._column_name] = dfr[self._column_name] * 100
            dfr["label"] = dfr["label"]*100

        # apply rounding factor to normalize values
        dfr[self._column_name] = dfr[self._column_name].round(self._round_factor)
        
        # adjust values for label use only
        dfr["label"] = dfr["label"].mask(dfr["label"] < 1, dfr["label"].round(2))
        dfr["label"] = dfr["label"].mask(
            (dfr["label"] > 1) & (dfr["label"]<100),
            dfr["label"].round(1)
        )
        dfr["label"] = dfr["label"].mask(dfr["label"]>=100, dfr["label"].round(0))
        dfr["label"] = dfr["label"].astype(str).apply(lambda x: re.sub( r'\.0$', '', x))

        return dfr
    
    def _get_chart_by_period_x_col(self) -> str:
        return 'Data de referência'

    def _get_chart_by_period_x_title(self) -> str:
        return 'Data de início de cada período'

    def _generate_series_sql(self):
        # 7, day, 140
        interval_val, period_unit, period_series = self._get_period_settings()
       
        series = f"""
            SELECT
                ((ld::date - interval '{interval_val} {period_unit}') + interval '1 day')::date as fd,
                ld::date as ld,
                0 as year
            FROM generate_series(
                ('{self._start_date}'::date - interval '{period_series} {period_unit}')::date,
                date '{self._start_date}',
                interval '{interval_val} {period_unit}'
            ) AS t(ld)
            ORDER BY 1 DESC
            LIMIT {self._query_limit}
        """

        return series
    
    def _get_reference_date_indices(self, dfr: pd.DataFrame):
        indices= [] * len(dfr['Data de referência'])

        ref_date = dfr.tail(1).values[0][1]
        prev = ref_date.strftime('%Y-%m')

        for i in range(len(dfr['Data de referência'])-1, -1, -1):
            if prev == (dfr['Data de referência'][i]).strftime('%Y-%m'):
                indices.append(i)
                ref_date = dfr['Data de referência'][i]
                prev = (ref_date - relativedelta(years = +1)).strftime('%Y-%m')

        return indices
    
    def _format_date_str(self, date: str) -> str:
        return f'{date[8:10]}/{date[5:7]}/{date[0:4]}'

    def _format_date(self, date: datetime) -> str:
        return self._format_date_str(date.isoformat())
    
    def _get_temporal_unit_column_sql(self):
        return f"sum(a.{self._column})"
    
    def _get_temporal_unit_sql(self, land_use_type: str):
        calendar = self._generate_series_sql()

        land_use_type_suffix = "" if land_use_type == "ams" else f"_{land_use_type}"

        name_escaped = self._name.replace("'", "''")

        where_group = (
            "" if self._name == "*" else
            f"""b.\"{self._table_info[self._spatial_unit]['key']}\" = '{name_escaped}' AND"""
        )

        where_biome = f"('{self._biome}' = 'ALL' OR a.biome = ANY ('{{{self._biome}}}'))"
        
        where_municipalities_group = f""" AND (
            '{self._municipalities_group}' = 'ALL' OR a.geocode =
            ANY(
                SELECT geocode
                FROM public.municipalities_group_members mgm
                WHERE mgm.group_id = (
                    SELECT mg.id
                    FROM public.municipalities_group mg
                    WHERE mg.name='{self._municipalities_group}'
                )
            )
            OR a.geocode = ANY('{{{self._geocodes}}}')
        ) """

        col = self._get_temporal_unit_column_sql()

        group_by_periods=f"""
            WITH calendar AS (
                {calendar}
            ),
            bar_chart AS (
                SELECT
                    (calendar.fd || '/' || calendar.ld) as period,
                    ROUND({col}::numeric,{self._round_factor}) as resultsum
                FROM
                    calendar,
                    "{self._spatial_unit}_land_use{land_use_type_suffix}" a
                    INNER JOIN "{self._spatial_unit}" b
                        ON a.suid = b.suid
                WHERE
                    {where_group}
                    {where_biome}
                    {where_municipalities_group}
                    AND classname = '{self._classname}'
                    AND date >= calendar.fd
                    AND date <= calendar.ld
                    AND a.land_use_id = ANY (array[{self._land_use}])
                GROUP BY
                    period
                ORDER BY
                    period DESC
                LIMIT {self._query_limit}
            )
            SELECT
                TO_CHAR(cd.fd::date, 'dd/mm/yyyy')|| '-' ||TO_CHAR(cd.ld::date, 'dd/mm/yyyy') as period,
                cd.fd as firstday, COALESCE(bc.resultsum,0) as resultsum,
                cd.year as year
            FROM
                calendar cd LEFT JOIN bar_chart bc
                    ON (cd.fd || '/' || cd.ld)=bc.period
            ORDER BY
                2 ASC
        """

        return group_by_periods
    
    def _build_indicator_period_dataframe(self, land_use_type: str):
        sql = self._get_temporal_unit_sql(land_use_type=land_use_type)
        dfr = _execute_sql_as_dataframe(db_url=self._db_url, sql=sql)
        dfr.columns = ['Período', 'Data de referência', self._column_name, 'Ano']
        return dfr
    
    def _get_classname_filter_sql(self) -> str:
        return ""

    def _build_indicator_by_landuse_dataframe(self, land_use_type: str, columns: list=[]):
        land_use_type_suffix = "" if land_use_type == "ams" else f"_{land_use_type}"
        name_escaped = self._name.replace("'", "''")

        where_specific = self._get_classname_filter_sql()
        where_spatial_unit = (
            "" if self._name=='*' else
            f"""b.\"{self._table_info[self._spatial_unit]['key']}\" = '{name_escaped}' AND"""
        )
        where_biome = f"('{self._biome}' = 'ALL' OR a.biome = ANY ('{{{self._biome}}}')) AND"
        where_municipalities_group = f"""(
            '{self._municipalities_group}' = 'ALL' OR a.geocode =
            ANY(
                SELECT geocode
                FROM public.municipalities_group_members mgm
                WHERE mgm.group_id = (
                    SELECT mg.id
                    FROM public.municipalities_group mg
                    WHERE mg.name='{self._municipalities_group}'
                )
            )
            OR a.geocode = ANY('{{{self._geocodes}}}')
        ) AND """

        where_filter = f"{where_biome} {where_municipalities_group} {where_specific} {where_spatial_unit}"
        where_landuse1 = (
            f"AND a.land_use_id = ANY (ARRAY[{self._land_use}])" if land_use_type == "ams" else ""
        )
        where_landuse2 = (
            f"WHERE a.id = ANY (ARRAY[{self._land_use}])" if land_use_type == "ams" else ""
        )

        sql = f"""
            SELECT
                a.name,
                a.priority,
                COALESCE(resultsum, 0) AS resultsum,
                SUM(COALESCE(resultsum, 0)) OVER () AS resultsum_total
            FROM land_use{land_use_type_suffix} a 
            LEFT JOIN (
                SELECT
                    a.land_use_id,
                    SUM(a.{self._column}) AS resultsum
                FROM
                    \"{self._spatial_unit}_land_use{land_use_type_suffix}\" a 
                INNER JOIN
                    \"{self._spatial_unit}\" b on a.suid = b.suid 
                WHERE
                    {where_filter}
                    a.date > '{self._start_period_date}'
                    AND a.date <= '{self._start_date}' 
                    AND a.classname = '{self._classname}' 
                    {where_landuse1}
                GROUP BY
                    a.land_use_id
            ) b
            ON
                a.id = b.land_use_id 
            {where_landuse2}
            ORDER BY
                a.priority ASC 
        """

        dfr = _execute_sql_as_dataframe(db_url=self._db_url, sql=sql)

        if not columns:
            columns = ['Categoria Fundiária', 'Prioridade', self._column_name, 'Total (km²)']

        dfr.columns = columns

        return dfr
    
    def _build_landuse_dataframe(self, land_use_type: str):
        land_use_type_suffix = "" if land_use_type == "ams" else f"_{land_use_type}"
        su_col_id = self._table_info[self._spatial_unit]['key']

        name_escaped = self._name.replace("'", "''")

        where_spatial_unit="" if(self._name=='*') else f"""su.\"{su_col_id}\" = '{name_escaped}' AND"""

        where_biome = f"('{self._biome}' = 'ALL' OR lua.biome = ANY ('{{{self._biome}}}')) AND"

        where_municipalities_group = f"""(
            '{self._municipalities_group}' = 'ALL' OR lua.geocode =
            ANY(
                SELECT geocode
                FROM public.municipalities_group_members mgm
                WHERE mgm.group_id = (
                    SELECT mg.id
                    FROM public.municipalities_group mg
                    WHERE mg.name='{self._municipalities_group}'
                )
            )
            OR lua.geocode = ANY('{{{self._geocodes}}}')
        ) AND """

        where_filter=f"{where_biome} {where_municipalities_group} {where_spatial_unit}"

        sql = f"""
            SELECT
                lu.name,
	            COALESCE(SUM(lua.area), 0) AS land_use_area,
	            SUM(SUM(lua.area)) OVER () AS land_use_total_area
            FROM
	            public.{self._spatial_unit}_land_use_area{land_use_type_suffix} lua
            INNER JOIN
	            public.land_use{land_use_type_suffix} lu ON lu.id=lua.land_use_id
            INNER JOIN
	            public.{self._spatial_unit} su ON su.{su_col_id}=lua.su_id
            WHERE
                {where_filter}
                lua.land_use_id = ANY (ARRAY[{self._land_use}]) 
            GROUP BY
	            lua.land_use_id, lu.name
            ORDER BY
                lua.land_use_id ASC;
        """

        dfr = _execute_sql_as_dataframe(db_url=self._db_url, sql=sql)
        dfr.columns = ['Categoria Fundiária', 'Área da Categoria (km²)', 'Área da Unidade Espacial (km²)']
        return dfr    
    
    def build_fig_by_period(self, json_format: bool=True):
        land_use_type = "ams"

        dfr = self._build_indicator_period_dataframe(land_use_type=land_use_type)

        # set bar colors
        color_discrete_sequence = ['#b7acad'] * len(dfr)
        # highlight the bars
        color_change_items = self._get_reference_date_indices(dfr=dfr)
        for i in color_change_items:
            color_discrete_sequence[i] = '#71a68c'

        chart_title = self._get_chart_by_period_title()

        cto = dfr['Data de referência'].to_list()
        dfr['Data de referência'] = dfr['Data de referência'].apply(self._format_date)
        dfr['Ano'] = dfr['Ano'].astype(str)

        dfr = self._add_chart_by_period_labe_columnl(dfr=dfr)

        x_col = self._get_chart_by_period_x_col()
        x_title = self._get_chart_by_period_x_title()

        fig = px.bar(
            dfr,
            x=x_col,
            y=self._column_name,
            title=chart_title,
            category_orders = {x_col: cto},
            color=x_col,
            color_discrete_sequence=color_discrete_sequence,
        )

        offset_annotation = dfr[self._column_name].max() * 0.03

        fig.update_layout(
            paper_bgcolor='#f3f9f8',
            plot_bgcolor='#f3f9f8',
            height=350,
            width=700,
            xaxis=layout.XAxis(
                linecolor='#000',
                tickcolor='#C0C0C0',
                ticks='outside',
                type='category',
                tickangle=45,
                title_text=x_title),
            showlegend=False,
            hovermode="x unified",
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=60,
                pad=0
            ),
            annotations=[
                {'x': x, 'y': total + offset_annotation, 'text': f'{totall}', 'showarrow': False}
                for x, total, totall in zip(dfr.index, dfr[self._column_name], dfr["label"])
            ]
        )

        ymin = dfr[self._column_name].min()
        ymax = dfr[self._column_name].max()

        fig.update_yaxes(
            range=[ymin * 0.95, ymax * 1.05],
            linecolor='#000',
            tickcolor='#C0C0C0',
            ticks='outside'
        )

        if not json_format:
            return fig
        
        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def _to_ha(self, dfr: pd.DataFrame):
        columns = {col: col.replace(self.UNIT_KM2, self.UNIT_HA) for col in dfr.columns if self.UNIT_KM2 in col}
        dfr.rename(columns=columns, inplace=True)
        self._column_name = self._column_name.replace(self.UNIT_KM2, self.UNIT_HA)
        for _, col in columns.items():
            dfr[col] = dfr[col] * 100
        return dfr
    
    def _get_chart_by_landuse_indicator(self):
        raise NotImplementedError(f"you have to implement this method ({inspect.stack()[0][3]}).")

    def _get_chart_by_landuse_total(self, total: float):
        _ = total
        raise NotImplementedError(f"you have to implement this method ({inspect.stack()[0][3]}).")

    def _get_chart_by_landuse_unit(self):
        return ""
    
    def _get_chart_by_landuse_spatial_unit(self):
        spatial_unit = "a Unidade Espacial"
        if self._name == '*':
            spatial_unit = 'o Bioma' if self._municipalities_group == 'ALL' else 'os Municípios de Interesse'
        return spatial_unit
    
    def _get_chart_by_landuse_title1(self):
        graph_spatial_unit = self._get_chart_by_landuse_spatial_unit()
        return f'<i>Informação fundiária de referência</i><br><b>Percentual da Área da Categoria<br>n{graph_spatial_unit}</b>'
    
    def _get_chart_by_landuse_title2(self):
        graph_indicator = self._get_chart_by_landuse_indicator()
        return f'<i>Informação dinâmica</i><br><b>Percentual de <br>{graph_indicator.title()}<br>em Relação ao Total</b>'
    
    def _get_chart_by_landuse_area_unit(self):
        return self.UNIT_KM2 if self._unit != self.UNIT_HA else self.UNIT_HA
    
    def _get_chart_by_landuse_custom_data(self, dfr: pd.DataFrame):
        _ = dfr
        return None
    
    def _get_chart_by_landuse_template2(self, value, percent, label):
        graph_indicator = self._get_chart_by_landuse_indicator()
        graph_unit = self._get_chart_by_landuse_unit()
        return f"Do total de {graph_indicator}, {value}{graph_unit}, o que corresponde a {percent},<br>estão em {label}."
    
    def _get_chart_by_landuse_title(self, total: float):
        _ = total
        raise NotImplementedError(f"you have to implement this method ({inspect.stack()[0][3]}).")
   
    def build_fig_by_landuse(self, json_format: bool=True):
        label = "Categoria Fundiária"
        land_use_type = "ams"

        # loading and mergin data
        df1 = self._build_indicator_by_landuse_dataframe(land_use_type=land_use_type)
        df2 = self._build_landuse_dataframe(land_use_type=land_use_type)

        dfr = pd.merge(df1, df2, on=label, how='outer') 
        dfr.update(dfr.select_dtypes(include=['float']).fillna(0.0))
        dfr = dfr.round({col: 0 if col=="Unidades" else 2 for col in dfr.select_dtypes(include=['float']).columns})
        dfr = dfr.sort_values(by=['Prioridade'], ascending=True)

        # converting to ha
        if self._unit == self.UNIT_HA and self._column == "area":
            dfr = self._to_ha(dfr=dfr)

        total = dfr[self._column_name].sum()

        if total == 0.:
            return None
        
        graph_label = "<b>%{label}</b>"
        graph_value = "%{value}"
        graph_percent = "%{percent:.2%}"

        graph_colors = [
            "#658faa",
            "#535585",
            "#53886e",
            "#998e8f",
            "#90c0c9",
            "#d7babe",
            "#c5c8ce",
            "#f8edd3",
            "#d7d0b3",
        ]

        graph_area_unit = self._get_chart_by_landuse_area_unit()

        graph_spatial_unit = self._get_chart_by_landuse_spatial_unit()

        title1 = self._get_chart_by_landuse_title1()
        title2 = self._get_chart_by_landuse_title2()

        fig = make_subplots(
            rows=2, cols=1,
            specs=[[{'type':'domain'}], [{'type':'domain'},]], 
            subplot_titles=[title2, title1],
        )

        # graph 1
        template1 = f"{graph_percent} da área total d{graph_spatial_unit.lower()}, {graph_value} {graph_area_unit},<br>é {graph_label}."
        fig.add_trace(
            go.Pie(
                labels=dfr[label],
                values=dfr[f'Área da Categoria ({graph_area_unit})'],
                hole=0.4,
                name=title1,
                hovertemplate=template1,                
            ),
            row=2, col=1
        )

        # graph 2
        custom_data = self._get_chart_by_landuse_custom_data(dfr=dfr)

        template2 = self._get_chart_by_landuse_template2(value=graph_value, percent=graph_percent, label=graph_label)

        fig.add_trace(
            go.Pie(
                labels=dfr[label],
                values=dfr[self._column_name],
                hole=0.4,
                name=title2,
                customdata=custom_data,
                hovertemplate=template2,
            ),
            row=1, col=1
        )

        title = self._get_chart_by_landuse_title(total=total)

        fig.update_traces(
            sort=False,
            textposition='inside',
            textfont_size=12,
            marker=dict(colors=graph_colors, line=dict(color='#c0c0c0', width=1))
        )
        fig.update_layout(
            title_text=title,
            title_x=0.5,
            title_y=0.95,
            paper_bgcolor='#f3f9f8',
            height=700,
            width=700,
            uniformtext_minsize=10,
            uniformtext_mode='hide',
            legend=dict(
                font=dict(size=12),
                y=0.5,
                yanchor="middle",
            ),
            margin=dict(
                l=0,
                r=0,
                b=10,
                t=180,
                pad=1
            )
        )        

        if not json_format:
            return fig

        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def _build_landuse_ppcdam_dataframe(self):
        default_col_name = self._column_name
        land_use_type = "ppcdam"
        car = "CAR"
        ccar = "com CAR"
        scar = "sem CAR"
        cf = "Categoria Fundiária"
        gr = "group"
        tt = "total"
        tg = "total by group"
        igp = "in-group percentage"
        pg = "percentage by group"
        sc = "scaled"
        pe = "percentage"

        # formating the dataframe
        all_categories = self._read_land_uses(land_use_type=land_use_type)["name"].tolist()

        dfr = self._build_indicator_by_landuse_dataframe(land_use_type=land_use_type)

        if self._unit == self.UNIT_HA and self._column == "area":
            dfr = self._to_ha(dfr=dfr)

        # including all categories
        dfr = dfr.set_index(cf)
        dfr = dfr.reindex(all_categories, fill_value=0).reset_index()

        # total and percentage
        dfr[tt] = dfr[default_col_name].sum()
        dfr[pe] = dfr[default_col_name] / dfr[tt] * 100.

        # com CAR and sem CAR groups
        dfr[gr] = dfr[cf].apply(lambda col: ccar if car in col else scar)    
        sum_ccar = dfr.loc[dfr[gr] == ccar, default_col_name].sum()
        sum_scar = dfr.loc[dfr[gr] == scar, default_col_name].sum()
        dfr.loc[dfr[gr] == ccar, tg] = sum_ccar
        dfr.loc[dfr[gr] == scar, tg] = sum_scar

        # total per group
        dfr[igp] = dfr[default_col_name] / dfr[tg] * 100.
        dfr[pg] = dfr[tg] / dfr[tt] * 100

        dfr[sc] = dfr[pe]

        dfr.fillna(0., inplace=True)

        return dfr
    
    def _get_chart_by_landuse_ppcdam_total(self):
        return f"do total de {self._get_chart_by_landuse_indicator()}"
    
    def _get_chart_by_landuse_ppcdam_extra(self, graph_custom_data0: str):
        return f" - {graph_custom_data0}<extra></extra>"

    def build_fig_by_landuse_ppcdam(self, json_format: bool=True):
        label_abbr = {
            'Terra indígena': 'TI',
            'Unidade de conservação': 'UC',
            'Território quilombola': 'TQ',
            'Assentamento rural': 'Assentamento',
            'Área de proteção ambiental': 'APA',
            'Floresta pública não destinada': 'FPND',
            'CAR sobreposto em terra indígena': 'sobreposto em TI',
            'CAR sobreposto em unidade de conservação': 'sobreposto em UC',
            'CAR sobreposto em território quilombola': 'sobreposto em TQ',
            'CAR sobreposto em assentamento rural': 'sobreposto em AR',
            'CAR sobreposto em área de proteção ambiental': 'sobreposto em APA',
            'CAR sobreposto em floresta pública não destinada': 'sobreposto em FPND',
            'Propriedade privada (Dados do CAR)': 'CAR sem sobreposição',
            'Área sem registro fundiário': 'sem registro fundiário'
        }
        _text_abbr = lambda lbls: [label_abbr.get(_, _) for _ in lbls]
    
        # column names and constants
        default_col_name = self._column_name
        uso = "Total"
        ccar = "com CAR"
        scar = "sem CAR"
        cf = "Categoria Fundiária"
        gr = "group"
        tt = "total"
        pg = "percentage by group"
        sc = "scaled"
        pe = "percentage"

        if self._unit == self.UNIT_HA:
            default_col_name = default_col_name.replace(self.UNIT_KM2, self.UNIT_HA)
    
        graph_unit = self._get_chart_by_landuse_unit()
    
        dfr = self._build_landuse_ppcdam_dataframe()

        if dfr["total"][0] == 0.:
            return None

        labels = [uso] + dfr[gr].unique().tolist() + dfr[cf].tolist()
        labels = _text_abbr(labels)
    
        parents = [""]  + [uso] * len(dfr[gr].unique()) + dfr[gr].tolist()
        parents = _text_abbr(parents)
    
        values = (
            [100]
            + dfr.groupby([gr])[sc].sum().reindex(dfr[gr].unique().tolist()).tolist()
            + dfr[sc].tolist()
        )

        custom_values = (
            [dfr[tt].tolist()[0]]
            + dfr.groupby([gr])[default_col_name].sum().reindex(dfr[gr].unique().tolist()).tolist()
            + dfr[default_col_name].tolist()
        )
        custom_values = [round(_, self._round_factor) for _ in custom_values]
        custom_values = [f"{_} {graph_unit}" for _ in custom_values]
        custom_percentages = (
            [100]
            + dfr.drop_duplicates(subset=[gr])[pg].tolist()
            + dfr[pe].tolist()
        )
        custom_labels = (
            [uso, scar, ccar] + dfr[cf].tolist()
        )
        custom_data = np.array([custom_values, custom_labels, custom_percentages]).T
    
        dfr.loc[dfr[gr] == ccar, "color"] = "#b7acad"
        dfr.loc[dfr[gr] == scar, "color"] = "#71a68c"
        colors = ["#fff", "#53886e", "#998e8f"] + dfr["color"].tolist()
    
        # assert len(values) == len(labels) == len(parents) == len(custom_values) == len(custom_labels) == len(colors)
    
        title = "<b>Análise da distribuição do indicador<br>no período em relação ao CAR</b><br>"
        title += "<i>CAR refere-se às propriedades privadas autodeclaradas no Cadastro Ambiental Rural</i>"
    
        graph_custom_data0 = "%{customdata[0]}"
        graph_custom_data1 = "%{customdata[1]}"
        graph_custom_data2 = "%{customdata[2]:.2f}%"

        graph_total = self._get_chart_by_landuse_ppcdam_total()

        template = f"{graph_custom_data1}: {graph_custom_data2} {graph_total}"
        template += self._get_chart_by_landuse_ppcdam_extra(graph_custom_data0=graph_custom_data0)

        fig = go.Figure(go.Sunburst(
            labels=labels,
            parents=parents,
            values=values,
            customdata=custom_data,
            branchvalues="total",
            texttemplate="%{label}",
            hovertemplate=template,
            marker=dict(colors=colors, line=dict(color='#fff', width=1.5)),
            insidetextorientation="horizontal", 
        ))
        fig.update_layout(
            title_text=title,
            title_x=0.5,
            title_y=0.95,
            paper_bgcolor='#f3f9f8',
            width=700,
            height=550,
            uniformtext=dict(minsize=10, ),
        )
        fig.update_traces(
            textfont=dict(size=16, color="white"),
        )

        if not json_format:
            return fig

        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

    def build_fig_by_landuse_prodes(self, json_format: bool=True) -> str | go.Figure:
        _ = json_format
        return ""
    
    def build_figs(self):
        return {"FormTitle": self.get_chart_main_title()}


class ProdesProfile(Profile):
    _prodes_start: int
    _prodes_end: int
    _prodes_period: str
    _classnames: Final[list[str]] = ["AI", "AD", "IV", "AV"]
    _names: Final[dict] = {
        "AI": "Incremento Anual de Desmatamento",
        "AD": "Desmatamento Acumulado",
        "IV": "Incremento anual/Vegetação nativa remanescente",
        "AV": "Desmatamento acumulado/Vegetação nativa original",
    }

    def __init__(
        self,
        db_url: str,
        classname: str,
        column: str,
        column_name: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname=classname,
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            column=column,
            column_name=column_name,
            round_factor=2,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

        if self._classname not in self._classnames:
            raise ValueError("invalid deter classname %s" % classname)

        start = datetime.strptime(self._start_date, '%Y-%m-%d')
        end = datetime.strptime(self._end_date, '%Y-%m-%d')
        
        self._start_period_date = end
        self._temporal_unit = f"{(start - end).days}d"
        self._prodes_start = start.year
        self._prodes_end = end.year + 1
        self._prodes_period = (
            f"{self._prodes_end} a {self._prodes_start}"
            if (self._prodes_start - self._prodes_end > 0) else f"{self._prodes_end}"
        )

    def _get_chart_by_period_x_col(self) -> str:
        return "Ano"

    def _get_chart_by_period_x_title(self) -> str:
        return "Ano Prodes"

    def _get_indicator_name(self):
        return self._names[self._classname]

    def _generate_series_sql(self):
        series = f"""
            SELECT  
                make_date(y, 1, 1) AS fd,
                make_date(y, 12, 31) AS ld,
                y as year
            FROM (
                SELECT DISTINCT EXTRACT(YEAR FROM date)::int AS y
                FROM states_land_use
		        WHERE classname = '{self._classname}'
            ) years
            ORDER BY y
        """

        return series
    
    def _get_reference_date_indices(self, dfr: pd.DataFrame):
        indices= [] * len(dfr['Data de referência'])

        for i, row in enumerate(dfr.itertuples(), start=0):
            if self._prodes_end <= row.Ano <= self._prodes_start:
                indices.append(i)

        return indices
    
    def _get_chart_by_landuse_title(self, total: float):
        graph_total = self._get_chart_by_landuse_total(total=total)
        indicator = self._get_indicator_name()

        title = f"<b>{indicator}</b> por categoria fundiária"
        title += f" do PRODES <b>{self._prodes_period}</b>"
        title += f". <br><b>{graph_total}</b>"

        return title
    
    def _get_chart_by_landuse_total(self, total: float):
        return f"Área total: {total:.2f} {self._unit}."


class AreaProfile(Profile):
    def __init__(
        self,
        db_url: str,
        classname: str,
        unit: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
    ):
        super().__init__(
            db_url=db_url,
            classname=classname,
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            column="area",
            column_name=f"Área ({unit})",
            round_factor=2,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

    def _get_chart_total(self, total: float):
        return f"Área total: {total:.2f} {self._unit}."

class UnitsProfile(Profile):
    def __init__(
        self,
        db_url: str,
        classname: str,
        column: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname=classname,
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            column=column,
            column_name="unidades",
            round_factor=0,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )
        
class ScoreProfile(Profile):
    def __init__(
        self,
        db_url: str,
        classname: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname=classname,
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            column="score",
            column_name="Score",
            round_factor=2,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

@register_profile("DS")
@register_profile("DG")
@register_profile("CS")
@register_profile("MN")
class DeterProfile(AreaProfile):
    _classnames: Final[list[str]] = ["DS", "DG", "CS", "MN"]
    _names: Final[dict] = {
        "DS": "Desmatamento",
        "DG": "Degradação",
        "CS": "Corte Seletivo",
        "MN": "Mineração",
    }

    def __init__(
        self,
        db_url: str,
        classname: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname=classname,
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )
        if self._classname not in self._classnames:
            raise ValueError("invalid deter classname %s" % classname)

    def _get_indicator_name(self):
        return self._names[self._classname]
    
    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        indicator = self._get_indicator_name()
        temporal_unit = self._temporal_unit_desc[self._temporal_unit]
        last_date = self._format_date_str(self._start_date)
        return f"""
            Análise dos dados de <b>{indicator}</b> do DETER até <b>{last_date}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas
            e unidade temporal <b>{temporal_unit}</b>.
        """
   
    def _get_chart_by_landuse_indicator(self):
        return "alertas"
    
    def _get_chart_by_landuse_custom_data(self, dfr: pd.DataFrame):
        return dfr[f'Área ({self._unit})'] / dfr[f'Área da Categoria ({self._unit})']
    
    def _get_chart_by_landuse_total(self, total: float):
        return f"Área total: {total:.2f} {self._unit}."
    
    def _get_chart_by_landuse_title(self, total: float):
        graph_total = self._get_chart_by_landuse_total(total=total)
        unid_temp = self._temporal_unit_desc[self._temporal_unit]
        indicator = self._get_indicator_name()

        title = f"<b>{indicator}</b> por categoria fundiária"
        title += f" no último período do <b>{unid_temp}"
        title += f". <br><b>{graph_total}</b>"

        return title
    
    def build_figs(self):
        res = super().build_figs()
        res["AreaPerYearTableClass"] = self.build_fig_by_period()
        res["AreaPerLandUse"] = self.build_fig_by_landuse()        
        res["AreaPerLandUsePpcdam"] = self.build_fig_by_landuse_ppcdam()
        return res


@register_profile("AF")
class ActiveFiresProfile(UnitsProfile):
    def __init__(
        self,
        db_url: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="AF",
            column="counts",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit="focos",
        )

    def _get_indicator_name(self):
        return "Focos"

    def _get_chart_by_landuse_indicator(self):
        return "focos"
    
    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        indicator = self._get_indicator_name()
        temporal_unit = self._temporal_unit_desc[self._temporal_unit]
        last_date = self._format_date_str(self._start_date)

        return f"""
            Análise dos dados de <b>{indicator}</b> de Queimadas até <b>{last_date}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas
            e unidade temporal <b>{temporal_unit}</b>.
        """
    
    def _get_chart_by_landuse_total(self, total: float):
        return f"Contagem de {self._get_chart_by_landuse_indicator()}: {total:.0f}."

    def _get_chart_by_landuse_title(self, total: float):
        graph_total = self._get_chart_by_landuse_total(total=total)
        unid_temp = self._temporal_unit_desc[self._temporal_unit]
        indicator = self._get_indicator_name()

        title = f"<b>{indicator}</b> por categoria fundiária"
        title += f" no último período do <b>{unid_temp}"
        title += f". <br><b>{graph_total}</b>"

        return title
    
    def build_fig_by_landuse_prodes(self, json_format: bool=True) -> str | go.Figure:
        label = "Classe PRODES"
        default_col_name = self._column_name
        land_use_type = "prodes"
        
        columns = [label, 'Prioridade', default_col_name, 'Total (km²)']

        dfr = self._build_indicator_by_landuse_dataframe(land_use_type=land_use_type, columns=columns)
        dfr.loc[dfr["Classe PRODES"] == "Vegetacao Nativa", "Classe PRODES"] = "Vegetação Nativa"
        dfr = dfr.round(0)
        dfr = dfr.sort_values(by=['Prioridade'], ascending=True)

        indicator = self._get_indicator_name()
        unid_temp = self._temporal_unit_desc[self._temporal_unit]
        total = dfr[default_col_name].sum()

        if total == 0.:
            return ""
        
        # generating the graphics
        graph_label = "<b>%{label}</b>"
        graph_value = "%{value}"
        graph_unit =  ""

        graph_percent = "%{percent:.2%}"
        graph_indicator = "focos"
        graph_total = f"Contagem de {graph_indicator}: {total}."
        graph_colors = ["#d4e157", "#ffee58", "#ffc107", "#ff9800"]

        title1 = f'<br><b>Percentual de {graph_indicator.title()}<br>em Relação ao Total de {graph_indicator.title()}</b>'

        template = f"Do total de {graph_indicator}, {graph_value}{graph_unit}, o que corresponde a {graph_percent},<br>estão em {graph_label}."

        fig = go.Figure(
            go.Pie(
                labels=dfr[label],
                values=dfr[default_col_name],
                hole=0.4,
                hovertemplate=template,
            )
        )

        fig.add_annotation(
            x=0.5,
            y=1.2,
            xref="paper",
            yref="paper",
            showarrow=False,
            text=title1,
            font=dict(size=14),
            align="center"
        )

        title = f"<b>{indicator}</b> por classe PRODES"
        title += f"<br>no último período do <b>{unid_temp}"
        title += f". <b>{graph_total}</b>"

        fig.update_traces(
            sort=False,
            textposition='inside',
            textfont_size=12,
            marker=dict(colors=graph_colors, line=dict(color='#c0c0c0', width=1))
        )

        fig.update_layout(
            title_text=title,
            title_x=0.5,
            title_y=0.95,
            paper_bgcolor='#f3f9f8',
            height=400,
            width=700,
            uniformtext_minsize=10,
            uniformtext_mode='hide',
            legend=dict(
                font=dict(size=12),
                y=0.5,
                yanchor="middle",
            ),
            margin=dict(
                l=0,
                r=0,
                b=10,
                t=140,
                pad=1
            )
        )

        if not json_format:
            return fig

        return json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    def build_figs(self):
        res = super().build_figs()
        res["AreaPerYearTableClass"] = self.build_fig_by_period()
        res["AreaPerLandUse"] = self.build_fig_by_landuse()        
        res["AreaPerLandUsePpcdam"] = self.build_fig_by_landuse_ppcdam()
        res["AreaPerLandUseProdes"] = self.build_fig_by_landuse_prodes()
        return res


@register_profile("FS")
class FireSpreadingRisk(UnitsProfile):
    def __init__(
        self,
        db_url: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="FS",
            column="units",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        indicator = self._get_indicator_name()

        return f"""
            Análise dos dados de <b>{indicator}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas.
        """
    
    def _get_chart_by_landuse_total(self, total: float):
        return f"Contagem de {self._get_chart_by_landuse_indicator()}: {total:.0f}."
    
    def _get_chart_by_landuse_title(self, total: float):
        graph_total = self._get_chart_by_landuse_total(total=total)
        indicator = self._get_indicator_name()

        title = f"<b>{indicator}</b> por categoria fundiária. <br><b>{graph_total}</b>"

        return title

    def _get_indicator_name(self):
        return "Risco de Espalhamento do Fogo"
    
    def build_fig_by_period(self, json_format: bool=True):
        _ = json_format
        raise NotImplementedError("there is no period graph for this indicator.")
    
    def _get_chart_by_landuse_indicator(self):
        return "pontos de risco"
    
    def build_figs(self):
        res = super().build_figs()
        res["AreaPerLandUse"] = self.build_fig_by_landuse()        
        res["AreaPerLandUsePpcdam"] = self.build_fig_by_landuse_ppcdam()
        return res


@register_profile("FT")
class FireToday(UnitsProfile):
    def __init__(
        self,
        db_url: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="FT",
            column="units",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit="focos"
        )

    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        indicator = self._get_indicator_name()

        return f"""
            Análise dos dados de <b>{indicator}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas.
        """
    
    def _get_chart_by_landuse_total(self, total: float):
        return f"Contagem de {self._get_chart_by_landuse_indicator()}: {total:.0f}."
    
    def _get_chart_by_landuse_title(self, total: float):
        graph_total = self._get_chart_by_landuse_total(total=total)
        indicator = self._get_indicator_name()

        title = f"<b>{indicator}</b> por categoria fundiária. <br><b>{graph_total}</b>"

        return title

    def _get_indicator_name(self):
        return "Focos de Hoje"
    
    def build_fig_by_period(self, json_format: bool=True):
        _ = json_format
        raise NotImplementedError("there is no period graph for this indicator.")
    
    def _get_chart_by_landuse_indicator(self):
        return "focos"
    
    def build_figs(self):
        res = super().build_figs()
        res["AreaPerLandUse"] = self.build_fig_by_landuse()        
        res["AreaPerLandUsePpcdam"] = self.build_fig_by_landuse_ppcdam()
        return res


@register_profile("RI")
class DeforestionRiskProfile(ScoreProfile):
    def __init__(
        self,
        db_url: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="RI",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

    def _get_indicator_name(self):
        return "Risco de Desmatamento"

    def build_fig_by_period(self, json_format: bool=True):
        _ = json_format
        raise NotImplementedError("there is no period graph for this indicator.")
    
    def _get_classname_filter_sql(self) -> str:
        return " a.score >= 0 AND "
    
    def _get_chart_by_landuse_indicator(self):
        return "score de risco"
    
    def _get_risk_date(self):
        sql = """
            SELECT risk_date
            FROM risk.risk_image_date
            WHERE source='inpe'
            ORDER BY id DESC
            LIMIT 1;
        """
        return _execute_sql(sql=sql, db_url=self._db_url)
    
    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        risk_date: datetime = self._get_risk_date()
        fortnight = f"{('primeira' if risk_date.day < 15 else 'segunda')} quinzena de {format_datetime(risk_date, 'MMMM', locale='pt_BR')} de {risk_date.year}"

        return f"""
            Análise dos dados de Risco de Desmatamento da <b>{fortnight}</b>, {spatial_unit}{spatial_description},
            para as categorias fundiárias selecionadas, intensidade de 0 (sem risco) a 1 (maior risco).
        """

    def _get_chart_by_landuse_title(self, total: float):
        graph_total = self._get_chart_by_landuse_total(total=total)
        indicator = self._get_indicator_name()

        title = f"<b>{indicator}</b> por categoria fundiária. <br><b>{graph_total}</b>"

        return title

    def _get_chart_by_landuse_total(self, total: float):
        return f"Intensidade total de risco: {total:.2f}." if self._name != "*" else ""
    
    def _get_chart_by_landuse_title2(self):
        return "<i>Informação dinâmica</i><br><b>Percentual da Intensidade Total de Risco<br>por Categoria Fundiária</b>"
    
    def _get_chart_by_landuse_template2(self, value: str, percent: str, label: str):
        _ = value
        return f"Da intensidade total de risco, {percent} estão em {label}."
    
    def _get_chart_by_landuse_ppcdam_total(self):
        return "da intensidade total de risco"
    
    def _get_chart_by_landuse_ppcdam_extra(self, graph_custom_data0: str):
        _ = graph_custom_data0
        return ""

    def build_figs(self):
        res = super().build_figs()
        res["AreaPerLandUse"] = self.build_fig_by_landuse()        
        res["AreaPerLandUsePpcdam"] = self.build_fig_by_landuse_ppcdam()
        return res

@register_profile("AI")
class AnnualIncrease(ProdesProfile):
    def __init__(
        self,
        db_url: str,
        unit: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="AI",
            column="area",
            column_name=f"Área ({unit})",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        return f"""
            Análise dos dados de <b>incremento anual de desmatamento</b> do PRODES <b>{self._prodes_period}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas.
        """
    
    def _get_chart_by_period_title(self):
        indicator = self._get_indicator_name()
        return f"""Evolução temporal do <b>{indicator}</b> do PRODES."""
    
    def _get_chart_by_landuse_indicator(self):
        return "incremento anual de desmatamento"
    
    def build_figs(self):
        res = super().build_figs()
        res["AreaPerYearTableClass"] = self.build_fig_by_period()
        res["AreaPerLandUse"] = self.build_fig_by_landuse()        
        res["AreaPerLandUsePpcdam"] = self.build_fig_by_landuse_ppcdam()
        return res


@register_profile("AD")
class AccumulatedDeforestation(ProdesProfile):
    def __init__(
        self,
        db_url: str,
        unit: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="AD",
            column="area",
            column_name=f"Área ({unit})",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        return f"""
            Análise dos dados de <b>desmatamento acumulado</b> do PRODES <b>{self._prodes_period}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas.
        """
    
    def _get_chart_by_period_title(self):
        indicator = self._get_indicator_name()
        return f"""Evolução temporal do <b>{indicator}</b> do PRODES."""
    
    def _get_chart_by_landuse_indicator(self):
        return "desmatamento acumulado"

    def build_figs(self):
        res = super().build_figs()
        res["AreaPerYearTableClass"] = self.build_fig_by_period()
        res["AreaPerLandUse"] = self.build_fig_by_landuse()        
        res["AreaPerLandUsePpcdam"] = self.build_fig_by_landuse_ppcdam()
        return res

@register_profile("IV")
class AnnualIncreaseRatio(ProdesProfile):
    def __init__(
        self,
        db_url: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="IV",
            column="ratio",
            column_name="percentual",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

    def _get_temporal_unit_column_sql(self):
        return f"""
            COALESCE(
                SUM(a.counts)::double precision
                /
                NULLIF(
                    SUM(a.counts)::double precision +
                    SUM(a.counts2)::double precision,
                    0
                ) * 100.,
                0
            )
            """
    
    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        return f"""
            Análise da razão entre o <b>Incremento anual de desmatamento</b> e a
            <b>Vegetação nativa remanescente</b> do PRODES <b>{self._prodes_period}</b>, 
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas.
        """
    
    def _get_chart_by_period_title(self):
        return f"""Evolução temporal da razão entre o <b>Incremento anual de desmatamento</b>
            <br>e a <b>Vegetação nativa remanescente</b> do PRODES.
        """
    
    def build_figs(self):
        res = super().build_figs()
        res["AreaPerYearTableClass"] = self.build_fig_by_period()
        return res


@register_profile("AV")
class AcumulatedDeforestationRatio(ProdesProfile):
    def __init__(
        self,
        db_url: str,
        name: str,
        spatial_unit: str,
        biome: str,
        land_use: str,
        temporal_unit: str,
        custom: bool,
        municipalities_group: str,
        geocodes: str,
        start_date: str,
        end_date: str,
        unit: str,
    ):
        super().__init__(
            db_url=db_url,
            classname="AV",
            column="ratio",
            column_name="percentual",
            name=name,
            spatial_unit=spatial_unit,
            biome=biome,
            land_use=land_use,
            temporal_unit=temporal_unit,
            custom=custom,
            municipalities_group=municipalities_group,
            geocodes=geocodes,
            start_date=start_date,
            end_date=end_date,
            unit=unit,
        )

    def _get_temporal_unit_column_sql(self):
        return f"""
            COALESCE(
                SUM(a.counts)::double precision
                /
                NULLIF(
                    SUM(a.counts2)::double precision,
                    0
                ) * 100.,
                0
            )
            """
    
    def _get_chart_description(self, spatial_unit: str, spatial_description: str):
        return f"""
            Análise da razão entre o <b>Desmatamento acumulado</b> e a
            <b>Vegetação nativa original</b> do PRODES <b>{self._prodes_period}</b>, 
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas.
        """
    
    def _get_chart_by_period_title(self):
        return f"""Evolução temporal da razão entre o <b>Desmatamento acumulado</b>
            <br>e a <b>Vegetação nativa original</b> do PRODES.
        """
    
    def build_figs(self):
        res = super().build_figs()
        res["AreaPerYearTableClass"] = self.build_fig_by_period()
        return res
