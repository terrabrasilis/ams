# -*- coding: utf-8 -*-
from dataclasses import replace
from unicodedata import category
from plotly.graph_objs import layout
import plotly.graph_objs as go
from plotly.subplots import make_subplots
from psycopg2 import connect
import pandas as pd
import plotly
import plotly.express as px
from datetime import datetime
import json
import re
from dateutil.relativedelta import relativedelta


class SpatialUnitProfile():
    """
    Data extraction to generate the profile graph panel for a spatial unit.

    Called by the endpoint API. See the routes.py at webapp directory.

    There are required input parameters:

        params['className'], Data class name.
        params['spatialUnit'], The Spatial Unit data table prefix. Ex.: 'csAmz_150km'
        params['startDate'], The reference start date.
        params['tempUnit'], The selected temporal unit code. Ex.: {'7d','15d','1m','3m','1y'}
        params['suName'], The selected Spatial Unit name. Ex.: 'C13L08'
        params['landUse'], The list of selected land use ids
        params['unit'], The current unit measure in the App. Ex.: {'km²','ha','focos','risco'}
        params['targetbiome'], The selected biome. Ex.: {'Cerrado', 'Amazônia'}
        params['riskThreshold'] The selected risk threshold value.
        params['custom'], when the period is customized.
    """

    def __init__(self, config, params):
        # The class name is fixed to 'RK' as is all code that checks the risk class name.
        self._risk_classname = "RK"
        # The class name is fixed to 'AF' as is all code that checks the fire class name.
        self._fire_classname = "AF"

        self._config = config

        self._dburl = self._config.DB_URL

        self._appBiome = params['targetbiome']
        self._query_limit = 20
        self._classname = params['className']
        self._risk_threshold = 0

        self._custom = 'custom' in params

        self._municipalities_group = params['municipalitiesGroup']

        self._geocodes = params['geocodes']
            
        # default column to sum statistics
        self.default_column="area"
        self.default_col_name="Área (km²)"

        if(self._classname==self._fire_classname):
            self.default_column="counts"
            self.default_col_name="Unidades"

        if(self._classname==self._risk_classname):
            self._risk_threshold = params['riskThreshold']
            self.default_column="counts"
            self.default_col_name="Unidades"

        # standard area rounding
        self.round_factor=2
        if(self._classname==self._fire_classname):
            self.round_factor=0

        self._spatial_unit = params['spatialUnit']
        if(self._spatial_unit==self._appBiome):
            self._spatial_unit = 'states'

        self._start_date = params['startDate']
        self._temporal_unit = params['tempUnit']
        self._start_period_date = self.get_prev_date_temporal_unit(temporal_unit=self._temporal_unit)
        self._name=params['suName'].replace('|',' ')
        if(self._name==self._appBiome):
            self._name = '*'

        self.land_use=params['landUse']

        # app unit measure
        unit=params['unit']
        if(unit is None):
            # default area unit
            self.data_unit="km²"
        else:
            self.data_unit=unit

        sql="""
            SELECT string_agg('"'||dataname||'":{"description":"'||description||'", "key":"'||as_attribute_name||'"}', ', ')
            FROM public.spatial_units
        """

        suinfo = self.execute_sql(sql=sql)
        suinfo = suinfo if suinfo is not None else "error:'failure on get infos from database'"
        self._tableinfo = json.loads("{"+suinfo+"}")

        self._classes = pd.DataFrame(
            {'code': pd.Series(['DS','DG', 'CS', 'MN', self._fire_classname, self._risk_classname], dtype='str'),
             'name': pd.Series(['Desmatamento','Degrada&#231;&#227;o',
                      'Corte-Seletivo','Minera&#231;&#227;o', 'Focos', 'Índice'], dtype='str'),
             'color': pd.Series(['#0d0887', '#46039f', '#7201a8', '#9c179e'], dtype='str')})
        self._temporal_units = {
            "7d": "Agregado 7 dias",
            "15d": "Agregado 15 dias",
            "1m": "Agregado 30 dias",
            "3m": "Agregado 90 dias",
            "1y": "Agregado 365 dias"}

        self._temporal_unit_sql = {
            7:'''select TO_CHAR(date, 'YYYY/WW') as period,classname,sum(a.'''+self.default_column+''') as 
            resultsum from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
            group by TO_CHAR(date, 'YYYY/WW'), classname
            order by 1 desc limit {2}''',
            15: '''select concat(TO_CHAR(date, 'YYYY'),'/',to_char(TO_CHAR(date, 'WW')::int/2+1,'FM00')) as period,
            classname,sum(a.'''+self.default_column+''') as resultsum from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
            group by concat(TO_CHAR(date, 'YYYY'),'/',to_char(TO_CHAR(date, 'WW')::int/2+1,'FM00')), classname
            order by 1 desc limit {2}''',
            31: '''select TO_CHAR(date, 'YYYY/MM') as period,classname,sum(a.'''+self.default_column+''') as 
            resultsum from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
            group by TO_CHAR(date, 'YYYY/MM'), classname
            order by 1 desc limit {2}''',
            124: '''select TO_CHAR(date, 'YYYY/Q') as period,classname, sum(a.'''+self.default_column+''') as 
            resultsum from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
            group by TO_CHAR(date, 'YYYY/Q'),classname
            order by 1 desc limit {2}''',
            366: '''select TO_CHAR(date, 'YYYY') as period,classname,sum(a.'''+self.default_column+''') as 
            resultsum from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
            group by TO_CHAR(date, 'YYYY'),classname
            order by 1 desc limit {2}'''}

        if self._custom:
            days = int(self._temporal_unit[:-1])
            self._temporal_units[self._temporal_unit] = f"Agregado customizado ({days} dias)"
            if not days in self._temporal_unit_sql:
                self._temporal_unit_sql[days] = self._temporal_unit_sql[7]

    def format_date(self, date: str)->str:
        return f'{date[8:10]}/{date[5:7]}/{date[0:4]}'

    def formatDate(self, date: datetime)->str:
        return self.format_date(date.isoformat())

    def get_previous_date(self, ref_date: datetime)->str:
        """
        Gets the previous date based on reference date using a rule for each temporal unit.
        It's result is used to highlight bars
        """
        if self._custom:
            return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')
        
        if self._temporal_unit == '7d': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')
        elif self._temporal_unit == '15d': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')
        elif self._temporal_unit == '1m': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')
        elif self._temporal_unit == '3m': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')

    def get_prev_date_temporal_unit(self, temporal_unit: str)->str:
        start_date_date = datetime.strptime(self._start_date, '%Y-%m-%d')

        if self._custom:
            return (start_date_date + relativedelta(days=-int(temporal_unit[:-1]))).strftime('%Y-%m-%d')
        
        if temporal_unit == '7d': return (start_date_date + relativedelta(days = -7)).strftime('%Y-%m-%d')
        elif temporal_unit == '15d': return (start_date_date + relativedelta(days = -15)).strftime('%Y-%m-%d')
        elif temporal_unit == '1m': return (start_date_date + relativedelta(days = -30)).strftime('%Y-%m-%d')
        elif temporal_unit == '3m': return (start_date_date + relativedelta(days = -90)).strftime('%Y-%m-%d')
        elif temporal_unit == '1y': return (start_date_date + relativedelta(days = -365)).strftime('%Y-%m-%d')

    def __get_period_settings(self):
        if self._custom:
            days = int(self._temporal_unit[:-1])
            return days,'day',self._query_limit*days            
        
        if self._temporal_unit == '7d': return 7,'day',self._query_limit*7
        elif self._temporal_unit == '15d': return 15,'day',self._query_limit*15
        elif self._temporal_unit == '1m': return 30,'day',self._query_limit*30
        elif self._temporal_unit == '3m': return 90,'day',self._query_limit*90
        elif self._temporal_unit == '1y': return 365,'day',self._query_limit*365

    def __get_temporal_unit_sql(self):
        # local round factor used into SQL to read data from database
        round_factor=4
        if(self._classname==self._fire_classname):
            round_factor=0
        
        interval_val,period_unit,period_series=self.__get_period_settings()
        calendar=f"""
            SELECT
                ((ld::date - interval '{interval_val} {period_unit}') + interval '1 day')::date as fd,
                ld::date as ld
            FROM generate_series(
                ('{self._start_date}'::date - interval '{period_series} {period_unit}')::date,
                date '{self._start_date}',
                interval '{interval_val} {period_unit}'
            ) AS t(ld)
            ORDER BY 1 DESC
            LIMIT {self._query_limit}
        """
    
        where_group = "" if(self._name=='*') else f"""b.\"{self._tableinfo[self._spatial_unit]['key']}\" = '{self._name}' AND"""

        where_biome = f"('{self._appBiome}' = 'ALL' OR a.biome = ANY ('{{{self._appBiome}}}'))"
        
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

        group_by_periods=f"""
            WITH calendar AS (
                {calendar}
            ),
            bar_chart AS (
                SELECT
                    (calendar.fd || '/' || calendar.ld) as period,
                    ROUND(sum(a.{self.default_column})::numeric,{round_factor}) as resultsum
                FROM
                    calendar,
                    "{self._spatial_unit}_land_use" a
                    INNER JOIN "{self._spatial_unit}" b
                        ON a.suid = b.suid
                WHERE
                    {where_group}
                    {where_biome}
                    {where_municipalities_group}
                    AND classname = '{self._classname}'
                    AND date >= calendar.fd
                    AND date <= calendar.ld
                    AND a.land_use_id = ANY (array[{self.land_use}])
                GROUP BY
                    period
                ORDER BY
                    period DESC
                LIMIT {self._query_limit}
            )
            SELECT
                TO_CHAR(cd.fd::date, 'dd/mm/yyyy')|| '-' ||TO_CHAR(cd.ld::date, 'dd/mm/yyyy') as period,
                cd.fd as firstday, COALESCE(bc.resultsum,0) as resultsum
            FROM
                calendar cd LEFT JOIN bar_chart bc
                    ON (cd.fd || '/' || cd.ld)=bc.period
            ORDER BY
                2 ASC
        """

        return group_by_periods

    def execute_sql(self, sql):
        curr = None
        conn = None
        try:
            conn = connect(self._dburl)
            curr = conn.cursor()
            curr.execute(sql)
            rows = curr.fetchall()
            return rows[0][0] if rows else None
        except Exception as e:
            raise e
        finally:
            if(not conn.closed): conn.close()

    def resultset_as_dataframe(self, sql):
        return pd.read_sql(sql, self._dburl)

    def __area_by_period(self):
        df = self.resultset_as_dataframe(self.__get_temporal_unit_sql())
        df.columns = ['Período', 'Data de referência', self.default_col_name]
        return df

    def classname_area_per_land_use(self):
        where_risk="" if(self._classname!=self._risk_classname) else f" a.risk >= {self._risk_threshold} AND "
        where_spatial_unit="" if(self._name=='*') else f"""b.\"{self._tableinfo[self._spatial_unit]['key']}\" = '{self._name}' AND"""

        where_biome = f"('{self._appBiome}' = 'ALL' OR a.biome = ANY ('{{{self._appBiome}}}')) AND"

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

        where_filter=f"{where_biome} {where_municipalities_group} {where_risk} {where_spatial_unit}"

        sql = f"""
            SELECT
                a.name,
                COALESCE(resultsum, 0) AS resultsum,
                SUM(COALESCE(resultsum, 0)) OVER () AS resultsum_total
            FROM land_use a 
            LEFT JOIN (
                SELECT
                    a.land_use_id,
                    SUM(a.{self.default_column}) AS resultsum
                FROM
                    \"{self._spatial_unit}_land_use\" a 
                INNER JOIN
                    \"{self._spatial_unit}\" b on a.suid = b.suid 
                WHERE
                    {where_filter}
                    a.date > '{self._start_period_date}'
                    AND a.date <= '{self._start_date}' 
                    AND a.classname = '{self._classname}' 
                    AND a.land_use_id = ANY (ARRAY[{self.land_use}]) 
                GROUP BY
                    a.land_use_id
            ) b
            ON
                a.id = b.land_use_id 
            WHERE
                a.id = ANY (array[{self.land_use}]) 
            ORDER BY
                a.priority ASC 
        """

        df = self.resultset_as_dataframe(sql)

        df.columns = ['Categoria Fundiária', self.default_col_name, 'Total (km²)']
        return df
    
    def area_per_land_use(self):
        su_col_id = self._tableinfo[self._spatial_unit]['key']

        where_spatial_unit="" if(self._name=='*') else f"""su.\"{su_col_id}\" = '{self._name}' AND"""

        where_biome = f"('{self._appBiome}' = 'ALL' OR lua.biome = ANY ('{{{self._appBiome}}}')) AND"

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
	            public.{self._spatial_unit}_land_use_area lua
            INNER JOIN
	            public.land_use lu ON lu.id=lua.land_use_id
            INNER JOIN
	            public.{self._spatial_unit} su ON su.suid=lua.suid
            WHERE
                {where_filter}
                lua.land_use_id = ANY (ARRAY[{self.land_use}]) 
            GROUP BY
	            lua.land_use_id, lu.name
            ORDER BY
	            lua.land_use_id ASC;
        """

        df = self.resultset_as_dataframe(sql)
        df.columns = ['Categoria Fundiária', 'Área da Categoria (km²)', 'Área da Unidade Espacial (km²)']
        return df

    def risk_expiration_date(self):        
        sql = """SELECT TO_CHAR(expiration_date, 'DD/MM/YYYY') as expdate
        FROM risk.risk_ibama_date
        ORDER BY id DESC
        LIMIT 1;"""
        return self.execute_sql(sql=sql)

    def form_title(self):
        """
        gets the main title for profile form
        """
        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        last_date=self.format_date(self._start_date)
        
        if self._name == '*':
            spatial_unit = 'para todo o bioma' if self._municipalities_group == 'ALL' else 'dos municípios de interesse'
            spatial_description = f" ({self._appBiome})" if self._municipalities_group == 'ALL' else ""
        else:
            spatial_unit = f"com recorte na unidade espacial <b>{self._name}</b>"
            spatial_description = f" ({self._tableinfo[self._spatial_unit]['description']})"

        temporal_unit=self._temporal_units[self._temporal_unit]

        datasource="do DETER"
        if(self._classname==self._fire_classname):
            title=f"""Usando dados de <b>{indicador}</b> de Queimadas até <b>{last_date}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas
            e unidade temporal <b>{temporal_unit}</b>.
            """

        elif self._classname == self._risk_classname:
            expiration_date = self.risk_expiration_date()
            expiration_date = expiration_date if expiration_date is not None else "falhou ao obter a data"
            title = f"""Usando dados de Risco de desmatamento (IBAMA), {spatial_unit}{spatial_description},
            para as categorias fundiárias selecionadas, valor maior ou igual a <b>{self._risk_threshold}</b> e validade até <b>{expiration_date}</b>."""
        else:
            title=f"""Usando dados de <b>{indicador}</b> {datasource} até <b>{last_date}</b>,
            {spatial_unit}{spatial_description}, para as categorias fundiárias selecionadas
            e unidade temporal <b>{temporal_unit}</b>.
            """

        return title

    def fig_area_per_land_use(self):
        label = "Categoria Fundiária"
        km2 = "km²"
        ha = "ha"
        default_col_name = self.default_col_name

        # loading and mergin data
        df1 = self.classname_area_per_land_use()
        df2 = self.area_per_land_use()

        # validation
        land_uses = df1[df1[default_col_name] > 0][label].tolist()
        for _ in land_uses:
            assert _ in df2[label].tolist()

        df = pd.merge(df1, df2, on=label, how='outer') 

        df.update(df.select_dtypes(include=['float']).fillna(0.0))
        df = df.round({col: 0 if col=="Unidades" else 2 for col in df.select_dtypes(include=['float']).columns})

        # converting to ha
        if self.data_unit == ha:
            columns = {col: col.replace(km2, ha) for col in df.columns if km2 in col}
            df.rename(columns=columns, inplace=True)
            default_col_name = default_col_name.replace(km2, ha)
            for _, col in columns.items():
                df[col] = df[col] * 100

        indicator = self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        unid_temp = self._temporal_units[self._temporal_unit]
        total = df[default_col_name].sum()

        fire_or_risk = self._classname in [self._fire_classname, self._risk_classname]

        # generating the graphics
        graph_label = "<b>%{label}</b>"
        graph_value = "%{value}"
        graph_unit =  "" if fire_or_risk else f" {self.data_unit}"
        graph_area_unit = km2 if self.data_unit != ha else ha
        graph_percent = "%{percent:.2%}"
        graph_custom_data = "%{customdata:.2%}"
        _ = {self._risk_classname: "pontos de risco", self._fire_classname: "focos"}
        graph_indicator = _[self._classname] if self._classname in _  else "alertas"
        graph_total = (
            f"Contagem de {graph_indicator}: {total}" if self._classname in [self._fire_classname, self._risk_classname] else
            f"Área total: {total:.2f} {graph_area_unit}"
        )
        graph_colors = ["#658faa", "#8c8185", "#53606e", "#998e8f", "#90c0c9", "#d7d9d5", "#ccddee", "#f8edd3", "#efeae1"]

        graph_spatial_unit = "a Unidade Espacial"
        if self._name == '*':
            graph_spatial_unit = 'o Bioma' if self._municipalities_group == 'ALL' else 'os Municípios de Interesse'        

        title1 = f'<i>Informação fundiária de referência</i><br><b>Percentual da Área da Categoria<br>n{graph_spatial_unit}</b>'
        title2 = f'<i>Informação dinâmina</i><br><b>Percentual de {graph_indicator.title()}<br>em Relação ao Total de {graph_indicator.title()}</b>'

        fig = make_subplots(
            rows=2, cols=1,
            specs=[[{'type':'domain'}], [{'type':'domain'},]], 
            subplot_titles=[title2, title1],
        )

        # graph 1
        template1 = f"{graph_percent} da área total d{graph_spatial_unit.lower()} {graph_value} {graph_area_unit},<br>é {graph_label}"
        fig.add_trace(
            go.Pie(
                labels=df[label],
                values=df[f'Área da Categoria ({graph_area_unit})'],
                hole=0.4,
                name=title1,
                hovertemplate=template1,                
            ),
            row=2, col=1
        )

        # graph 2
        custom_data = (
            None if self._classname in [self._fire_classname, self._risk_classname] else 
            df[f'Área ({graph_area_unit})'] / df[f'Área da Categoria ({graph_area_unit})']
        )

        template2 = f"Do total de {graph_indicator}, {graph_value}{graph_unit}, o que corresponde a {graph_percent},<br>estão em {graph_label}. "
        template2 += (
            "" if fire_or_risk else
            f"Os {graph_value}{graph_unit} representam {graph_custom_data}<br>da área total dessa categoria "
            f"n{graph_spatial_unit}."
        )
        fig.add_trace(
            go.Pie(
                labels=df[label],
                values=df[default_col_name],
                hole=0.4,
                name=title2,
                customdata=custom_data,
                hovertemplate=template2,
            ),
            row=1, col=1
        )

        title = f"<b>{indicator}</b> por categoria fundiária<br>"
        title += f"no último período do <b>{unid_temp}. <b>{graph_total}</b>"

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
            height=600,
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

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON

    def fig_area_by_period(self):

        def getIndexes(df):
            refDate=df.tail(1).values[0][1]
            prev=refDate.strftime('%Y-%m')

            index=[]*len(df['Data de referência'])
            for i in range(len(df['Data de referência'])-1,-1,-1):
                if prev == (df['Data de referência'][i]).strftime('%Y-%m'):
                    index.append(i)
                    prev=self.get_previous_date(ref_date=df['Data de referência'][i])
            return index

        df = self.__area_by_period()
        # set bar colors
        color_discrete_sequence = ['#609cd4'] * len(df)
        # highlight the bars
        color_change_items = getIndexes(df)
        for i in color_change_items:
            color_discrete_sequence[i] = '#ec7c34'

        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        unid_temp=self._temporal_units[self._temporal_unit]
        chart_title=f"""Evolução temporal de <b>{indicador}</b> para os períodos do
        <br><b>{unid_temp}</b> (limitado aos últimos {self._query_limit} períodos)."""

        cto=df['Data de referência'].to_list()
        df['Data de referência']=df['Data de referência'].apply(self.formatDate)
        
        # duplicate series to use in label chart
        df["label"]=df[self.default_col_name]

        if(self._classname==self._fire_classname):
            df[self.default_col_name]=df[self.default_col_name].astype(int)
            df["label"]=df["label"].astype(int).astype(str)
        else:
            if(self.data_unit=="ha"):
                df[self.default_col_name]=df[self.default_col_name]*100
                df["label"] = df["label"]*100
                self.round_factor=1
            # apply rounding factor to normalize values
            df[self.default_col_name]=df[self.default_col_name].round(self.round_factor)
            # adjust values for label use only
            df["label"] = df["label"].mask(df["label"]<1, df["label"].round(2))
            df["label"] = df["label"].mask((df["label"]>1) & (df["label"]<100), df["label"].round(1))
            df["label"] = df["label"].mask(df["label"]>=100, df["label"].round(0))
            df["label"] = df["label"].astype(str).apply(lambda x: re.sub( r'\.0$', '', x) )

        fig = px.bar(df, x='Data de referência', y=self.default_col_name, title=chart_title,
                     category_orders = {'Data de referência': cto},
                     color='Data de referência',
                     color_discrete_sequence=color_discrete_sequence,
                     hover_data=["Período"])

        offset_annotation = df[self.default_col_name].max() * 0.03
        fig.update_layout(
            paper_bgcolor='#f3f9f8',
            plot_bgcolor='#f3f9f8',
            height=300,
            width=700,
            xaxis=layout.XAxis(
                linecolor='#000',
                tickcolor='#C0C0C0',
                ticks='outside',
                type='category',
                tickangle=45,
                title_text="Data de início de cada período"),
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
                for x, total, totall in zip(df.index, df[self.default_col_name], df["label"])
            ]
        )
        fig.update_yaxes(
            rangemode= "tozero",
            linecolor='#000',
            tickcolor='#C0C0C0',
            ticks='outside'
        )
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON
