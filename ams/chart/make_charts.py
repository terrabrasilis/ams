# -*- coding: utf-8 -*-
from dataclasses import replace
from unicodedata import category
from plotly.graph_objs import layout
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from psycopg2 import connect
import pandas as pd
import plotly
import plotly.express as px
from datetime import datetime
import json
import re
from dateutil.relativedelta import relativedelta

class MakeCharts():
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
        params['unit'], The current unit measure in the App. Ex.: {'km²','ha','focos'}
        params['targetbiome'], The selected biome. Ex.: {'Cerrado', 'Amazônia'}
    """

    def __init__(self, config, params):
        self._config = config
        self._appBiome = params['targetbiome']
        self._dburl = self._config.DB_CERRADO_URL if (self._appBiome=='Cerrado') else self._config.DB_AMAZON_URL
        self._conn = connect(self._dburl)
        self._query_limit = 20
        self._classname = params['className']
            
        # default column to sum statistics
        self.default_column="area"
        self.default_col_name="Área (km²)"
        if(self._classname=='AF'):
            self.default_column="counts"
            self.default_col_name="Unidades"

        # standard area rounding
        self.round_factor=2
        if(self._classname=='AF'):
            self.round_factor=0

        self._spatial_unit = params['spatialUnit']
        if(self._spatial_unit==self._appBiome):
            self._spatial_unit = 'cer_states' if (self._appBiome=='Cerrado') else 'amz_states'

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
            self.area_unit="km²"
        else:
            self.area_unit=unit

        sql="""
        SELECT string_agg('"'||dataname||'":{"description":"'||description||'", "key":"'||as_attribute_name||'"}', ', ')
        FROM public.spatial_units
        """
        suinfo = self._execute_sql(sql=sql)
        self._tableinfo = json.loads("{"+suinfo+"}")

        self._classes = pd.DataFrame(
            {'code': pd.Series(['DS','DG', 'CS', 'MN', 'AF'], dtype='str'),
             'name': pd.Series(['Desmatamento','Degrada&#231;&#227;o',
                      'Corte-Seletivo','Minera&#231;&#227;o', 'Focos'], dtype='str'),
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

    def format_date(self, date: str)->str:
        return f'{date[8:10]}/{date[5:7]}/{date[0:4]}'

    def formatDate(self, date: datetime)->str:
        return self.format_date(date.isoformat())

    def get_previous_date(self, ref_date: datetime)->str:
        """
        Gets the previous date based on reference date using a rule for each temporal unit.
        It's result is used to highlight bars
        """
        if self._temporal_unit == '7d': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')
        elif self._temporal_unit == '15d': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')
        elif self._temporal_unit == '1m': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')
        elif self._temporal_unit == '3m': return (ref_date - relativedelta(years = +1)).strftime('%Y-%m')

    def get_prev_date_temporal_unit(self, temporal_unit: str)->str:
        start_date_date = datetime.strptime(self._start_date, '%Y-%m-%d')
        if temporal_unit == '7d': return (start_date_date + relativedelta(days = -7)).strftime('%Y-%m-%d')
        elif temporal_unit == '15d': return (start_date_date + relativedelta(days = -15)).strftime('%Y-%m-%d')
        elif temporal_unit == '1m': return (start_date_date + relativedelta(days = -30)).strftime('%Y-%m-%d')
        elif temporal_unit == '3m': return (start_date_date + relativedelta(days = -90)).strftime('%Y-%m-%d')
        elif temporal_unit == '1y': return (start_date_date + relativedelta(days = -365)).strftime('%Y-%m-%d')

    def _period_where_clause(self):
        return f" date > '{self._start_period_date}' and date <= '{self._start_date}'"

    def _get_period_settings(self):
        if self._temporal_unit == '7d': return 7,'day',self._query_limit*7
        elif self._temporal_unit == '15d': return 15,'day',self._query_limit*15
        elif self._temporal_unit == '1m': return 30,'day',self._query_limit*30
        elif self._temporal_unit == '3m': return 90,'day',self._query_limit*90
        elif self._temporal_unit == '1y': return 365,'day',self._query_limit*365

    def _get_temporal_unit_sql(self):
        # local round factor used into SQL to read data from database
        round_factor=4
        if(self._classname=='AF'):
            round_factor=0
        
        interval_val,period_unit,period_series=self._get_period_settings()
        calendar=f"""
        SELECT ((ld::date - interval '{interval_val} {period_unit}') + interval '1 day')::date as fd,
        ld::date as ld
        FROM generate_series(('{self._start_date}'::date - interval '{period_series} {period_unit}')::date,
        date '{self._start_date}', interval '{interval_val} {period_unit}') as t(ld)
        ORDER BY 1 DESC LIMIT {self._query_limit}"""

        where_group="" if(self._name=='*') else f"""b.\"{self._tableinfo[self._spatial_unit]['key']}\" = '{self._name}' AND"""
        group_by_periods=f"""
        WITH calendar AS ({calendar}),
        bar_chart AS (
            SELECT (calendar.fd || '/' || calendar.ld) as period, ROUND(sum(a.{self.default_column})::numeric,{round_factor}) as resultsum
            FROM calendar, "{self._spatial_unit}_land_use" a inner join "{self._spatial_unit}" b on a.suid = b.suid
            WHERE {where_group} classname = '{self._classname}'
            AND date >= calendar.fd
            AND date <= calendar.ld
            AND a.land_use_id = ANY (array[{self.land_use}])
            GROUP BY period
            ORDER BY period DESC LIMIT {self._query_limit}
        )
        SELECT TO_CHAR(cd.fd::date, 'dd/mm/yyyy')|| '-' ||TO_CHAR(cd.ld::date, 'dd/mm/yyyy') as period,
        cd.fd as firstday, COALESCE(bc.resultsum,0) as resultsum
        FROM calendar cd left join bar_chart bc on (cd.fd || '/' || cd.ld)=bc.period
        ORDER BY 2 ASC"""

        return group_by_periods

    def _execute_sql(self, sql):
        curr = None
        try:
            curr = self._conn.cursor()
            curr.execute(sql)
            rows = curr.fetchall()
            return rows[0][0]
        except Exception as e:
            raise e
        finally:
            if(not self._conn.closed): self._conn.close()

    def _resultset_as_dataframe(self, sql):
        return pd.read_sql(sql, self._dburl)

    def _area_by_period(self):
        df = self._resultset_as_dataframe(self._get_temporal_unit_sql())
        df.columns = ['Período', 'Data de referência', self.default_col_name]
        return df

    def _area_per_land_use(self):
        where_if="" if(self._name=='*') else f"""b.\"{self._tableinfo[self._spatial_unit]['key']}\" = '{self._name}' AND"""

        df = self._resultset_as_dataframe(
            f"select a.name,coalesce(resultsum, 0) as resultsum from land_use a "
            f"left join "
            f"(select a.land_use_id, sum(a.{self.default_column}) as resultsum from \"{self._spatial_unit}_land_use\" a "
            f"inner join \"{self._spatial_unit}\" b on a.suid = b.suid "
            f"where {where_if} "
            f" {self._period_where_clause()} "
            f"and classname = '{self._classname}' "
            f"and a.land_use_id = ANY (array[{self.land_use}]) "
            f"group by a.land_use_id) b on a.id = b.land_use_id "
            f"WHERE a.id = ANY (array[{self.land_use}]) "
            f"ORDER BY a.priority ASC "
        )
        df.columns = ['Categoria Fundiária', self.default_col_name]
        return df

    def _area_per_spatial_units(self):
        """
        get spatial units and relative areas for each, sorted by major values
        used at ratio weight chart
        """

        df = self._resultset_as_dataframe(
            f"select suid, coalesce(resultsum, 0) as resultsum "
            f"from "
            f"( "
            f"	select a.suid, sum(a.{self.default_column}) as resultsum "
            f"	from \"{self._spatial_unit}_land_use\" a "
            f"	inner join \"{self._spatial_unit}\" b on a.suid = b.suid "
            f"	where {self._period_where_clause()} "
            f"	and classname = '{self._classname}' "
            f"	and a.land_use_id = ANY (array[{self.land_use}]) "
            f"	group by a.suid "
            f") tb1 "
            f"ORDER BY 2 DESC "
        )
        df.columns = ['Unidade Espacial', self.default_col_name]
        return df

    def get_title4profile(self):
        """
        gets the main title for profile charts
        """
        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        last_date=self.format_date(self._start_date)
        spatial_unit='para todo o bioma' if(self._name=='*') else f"""com recorte na unidade espacial <b>{self._name}</b>"""
        spatial_description=self._appBiome if(self._name=='*') else self._tableinfo[self._spatial_unit]['description']
        temporal_unit=self._temporal_units[self._temporal_unit]

        datasource="do DETER"
        if(self._classname=='AF'):
            datasource="de Queimadas"

        title=f"""Usando dados de <b>{indicador}</b> {datasource} até <b>{last_date}</b>,
        {spatial_unit} ({spatial_description}), para as categorias fundiárias selecionadas
        e unidade temporal <b>{temporal_unit}</b>.
        """

        return title

    def get_title4ratio(self):
        """
        gets the main title for ratio weight chart
        """
        title=""

        return title

    def fig_area_per_land_use(self):
        """
        Pie chart structs to construct chart in frontend with plotly
        """
        df = self._area_per_land_use()
        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        unid_temp=self._temporal_units[self._temporal_unit]
        total_area = df[self.default_col_name].sum()

        if(self._classname!='AF' and self.area_unit=="ha"):
            df["Área (ha)"]=df[self.default_col_name]*100
            self.default_col_name="Área (ha)"
            total_area = df[self.default_col_name].sum()
            self.round_factor=1
        
        # area values rounded off only after treating the appropriate scale unit
        df[self.default_col_name] = df[self.default_col_name].round(self.round_factor)

        # default column to sum statistics
        abstract_data=f"Área total: {total_area.round(self.round_factor)} {self.area_unit}"
        if(self._classname=='AF'):
            abstract_data=f"Total de focos: {total_area.round(self.round_factor)} "

        chart_title=f"""Porcentagem de <b>{indicador}</b> por categoria fundiária<br>"""
        chart_title=f"""{chart_title}no último período do <b>{unid_temp}. {abstract_data}</b>"""

        fig = px.pie(df, values=self.default_col_name, names='Categoria Fundiária', template='plotly',
                     color_discrete_sequence=px.colors.sequential.RdBu,
                     title=chart_title )
 
        # sort=False is used to keep legend order like ordered in dataset
        fig.update_traces(
            sort=False,
            textposition='inside',
            textfont_size=14,
            marker=dict(colors=px.colors.sequential.RdBu, line=dict(color='#C0C0C0', width=1))
        )
        fig.update_layout(
            paper_bgcolor='#f3f9f8',
            height=300,
            width=700,
            uniformtext_minsize=10,
            uniformtext_mode='hide',
            legend=dict(font=dict(size=12)),
            margin=dict(
                l=0,
                r=0,
                b=20,
                t=105,
                pad=10
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

        df = self._area_by_period()
        # set bar colors
        color_discrete_sequence = ['#609cd4'] * len(df)
        # highlight the bars
        color_change_items = getIndexes(df)
        for i in color_change_items:
            color_discrete_sequence[i] = '#ec7c34'

        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        unid_temp=self._temporal_units[self._temporal_unit]
        chart_title=f"""Evolução temporal de <b>{indicador}</b>
        <br>para os períodos do <b>{unid_temp}</b>
        (limitado aos últimos {self._query_limit} períodos)."""

        cto=df['Data de referência'].to_list()
        df['Data de referência']=df['Data de referência'].apply(self.formatDate)
        
        # duplicate series to use in label chart
        df["label"]=df[self.default_col_name]

        if(self._classname=='AF'):
            df[self.default_col_name]=df[self.default_col_name].astype(int)
            df["label"]=df["label"].astype(int).astype(str)
        else:
            if(self.area_unit=="ha"):
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



    # WARNING
    def fig_area_by_ratio_weight(self):
        """
        https://plotly.com/python/multiple-axes/
        
        Note: At this time, Plotly Express does not support multiple Y axes on a single figure.
        To make such a figure, use the make_subplots() function in conjunction with graph objects as documented below.
        
        """

        # get spatial units and relative areas for each sorted by major values
        df = self._area_per_spatial_units()

        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        unid_temp=self._temporal_units[self._temporal_unit]
        chart_title=f"""Evolução temporal de <b>{indicador}</b> para o período <b>{unid_temp}</b>."""

        aBarChart = px.bar(df, x='Unidade Espacial', y=self.default_col_name, title=chart_title)

        aBarChart.update_layout(
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
                title_text="Lista de todas as unidades espaciais"),
            showlegend=False,
            hovermode="x unified",
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=60,
                pad=0
            ),
            modebar=dict(
                remove="zoomout"
            )
        )
        aBarChart.update_yaxes(
            rangemode= "tozero",
            linecolor='#000',
            tickcolor='#C0C0C0',
            ticks='outside'
        )

        aLineChart = go.Scatter(x=df['Unidade Espacial'], y=df[self.default_col_name], mode = 'lines')

        # Create figure with secondary y-axis
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        #fig.add_traces(aBarChart)
        fig.add_traces(aLineChart,secondary_y=True)

        graphJSON = json.dumps(aBarChart, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON


    def get_csv_to_composite_chart(self):
        """
        -- get mun percents
        WITH for_each_su AS (
            select b.nome || ':' || b.cod_ibge as name, coalesce(sum(a.area),0) as resultsum
                from amz_municipalities_land_use a 
                inner join amz_municipalities b on a.suid = b.suid 
                where classname = 'DS'
                group by 1 
        ), for_all as (
            select SUM(resultsum) as total from for_each_su
        ), results as (
            select tb1.name, ROUND((tb1.resultsum*100/tb2.total)::numeric, 4) as perc
            from for_each_su tb1, for_all tb2
        )
        select * FROM results


        -- get mun areas
        select name, ROUND( coalesce(resultsum, 0)::numeric, 2) as resultsum 
            from 
            (
                select b.nome || ':' || b.cod_ibge as name, sum(a.area) as resultsum
                from amz_municipalities_land_use a 
                inner join amz_municipalities b on a.suid = b.suid 
                where classname = 'DS'
                group by 1 
            ) tb1 
        ORDER BY 2 DESC
        """