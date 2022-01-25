# -*- coding: utf-8 -*-
from unicodedata import category

from plotly.graph_objs import layout
from psycopg2.extras import DictCursor
import pandas as pd
import numpy as np
import plotly
import plotly.express as px
from datetime import datetime
import json
from ams.dataaccess import AlchemyDataAccess
from dateutil.relativedelta import relativedelta

class AreaProfile():
    """Profile"""

    def __init__(self, config, params):
        self._config = config
        self._db = AlchemyDataAccess()
        self._classname = params['className']
        self._spatial_unit = params['spatialUnit']
        self._start_date = params['startDate']
        self._temporal_unit = params['tempUnit']
        self._start_period_date = self.get_prev_date_temporal_unit(temporal_unit=self._temporal_unit)
        self._name=params['click']['name'].replace('|',' ')
        self._tableinfo = {
            'csAmz_150km': {'description': 'C&#233;lula 150x150 Km&#178',
                            'key' : 'id'},
            'csAmz_300km': {'description': 'C&#233;lula 300x300 Km&#178',
                            'key' : 'id'},
            'amz_municipalities': {'description': 'Município',
                            'key' : 'nm_municip'},
            'amz_states': {'description': 'Estado',
                            'key' : 'NM_ESTADO'}
        }
        self._classes = pd.DataFrame(
            {'code': pd.Series(['DS','DG', 'CS', 'MN'], dtype='str'),
             'name': pd.Series(['Desmatamento','Degrada&#231;&#227;o',
                      'Corte-Seletivo','Minera&#231;&#227;o'], dtype='str'),
             'color': pd.Series(['#0d0887', '#46039f', '#7201a8', '#9c179e'], dtype='str')})
        self._temporal_units = {
            "7d": "Agregado Semanal",
            "15d": "Agregado 15 Dias",
            "1m": "Agregado Mensal",
            "3m": "Agregado 3 Meses",
            "1y": "Agregado Anual"}
        self._temporal_unit_sql = {
7:'''select TO_CHAR(date, 'YYYY/WW') as period,classname,sum(area) as 
area from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
group by TO_CHAR(date, 'YYYY/WW'), classname
order by 1 desc limit 20''',
15: '''select concat(TO_CHAR(date, 'YYYY'),'/',to_char(TO_CHAR(date, 'WW')::int/2+1,'FM00')) as period,
classname,sum(area) as area from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
group by concat(TO_CHAR(date, 'YYYY'),'/',to_char(TO_CHAR(date, 'WW')::int/2+1,'FM00')), classname
order by 1 desc limit 20''',
31: '''select TO_CHAR(date, 'YYYY/MM') as period,classname,sum(area) as 
area from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
group by TO_CHAR(date, 'YYYY/MM'), classname
order by 1 desc limit 20''',
124: '''select TO_CHAR(date, 'YYYY/Q') as period,classname, sum(area) as 
area from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
group by TO_CHAR(date, 'YYYY/Q'),classname
order by 1 desc limit 20''',
366: '''select TO_CHAR(date, 'YYYY') as period,classname,sum(area) as 
area from "{0}_land_use" a inner join "{0}" b on a.suid = b.suid where {1} 
group by TO_CHAR(date, 'YYYY'),classname
order by 1 desc limit 20'''}

    def format_date(self, date: str)->str:
        return f'{date[8:10]}/{date[5:7]}/{date[0:4]}'

    def get_prev_date_temporal_unit(self, temporal_unit: str)->str:
        start_date_date = datetime.strptime(self._start_date, '%Y-%m-%d')
        if temporal_unit == '7d': return (start_date_date + relativedelta(days = -7)).strftime('%Y-%m-%d')
        elif temporal_unit == '15d': return (start_date_date + relativedelta(days = -15)).strftime('%Y-%m-%d')
        elif temporal_unit == '1m': return (start_date_date + relativedelta(months = -1)).strftime('%Y-%m-%d')
        elif temporal_unit == '3m': return (start_date_date + relativedelta(months = -3)).strftime('%Y-%m-%d')
        elif temporal_unit == '1y': return (start_date_date + relativedelta(years = -1)).strftime('%Y-%m-%d')

    def period_where_clause(self):
        return f" date >= '{self._start_period_date}' and date <= '{self._start_date}'"

    def get_temporal_unit_sql(self):
        delta = datetime.strptime(self._start_date, '%Y-%m-%d') - datetime.strptime(self._start_period_date, '%Y-%m-%d')
        for key, value in self._temporal_unit_sql.items():
            if delta.days <= key:
                where = f"b.\"{self._tableinfo[self._spatial_unit]['key']}\" = '{self._name}' " \
                        f"and classname = '{self._classname}' " \
                        f"and date <= '{self._start_date}'"
                return f"select * from ({value.format(self._spatial_unit,where)}) a order by 1"

    def execute_sql(self, sql, cursor_factory=None, return_headers=False):
        conn = self._db.engine.connect()
        try:
            if cursor_factory is None:
                curr = conn.cursor()
            else:
                curr = conn.cursor(cursor_factory=cursor_factory)
                conn.commit()
            curr.execute(sql)
            rows = curr.fetchall()
            return (rows, curr.description) if return_headers else rows
        except Exception as e:
            raise e

    def resultset_as_dict(self, sql):
        return {row[0]: row[1] for row in self.execute_sql(sql, cursor_factory=DictCursor)}

    def resultset_as_dataframe(self, sql):
        return pd.read_sql(sql, self._config.DATABASE_URL)

    def resultset_as_list(self, sql):
        return [row[0] for row in self.execute_sql(sql)]

    def area_per_year_table_class(self):
        df = self.resultset_as_dataframe(
            self.get_temporal_unit_sql())
        df.columns = ['Período', 'Classe', 'Área (km²)']
        df['Área (km²)'] = df['Área (km²)'].round(3)
        return df

    '''
    def area_per_class(self, suid, table):
        df = self.resultset_as_dataframe(
            'select classname as code, sum(a.area) as area '                                                   
            f'from "{table}_land_use" a '
            f'inner join "csAmz_150km" b on a.suid = b.suid '
            f"where b.\"{self._tableinfo[table]['key']}\" = '{suid}' " 
            f'group by classname order by classname'
        )
        df = pd.merge(self._classes, df, on='code')
        df.columns = ['code', 'Name', 'color', 'Área (km²)']
        df['Área (km²)'] = df['Área (km²)'].round(3)
        return df
    '''

    def area_per_land_use(self):
        df = self.resultset_as_dataframe(
            f"select a.name,coalesce(Area, 0) as Area from land_use a "
            f"left join "
            f"(select a.land_use_id, sum(area) as Area from \"{self._spatial_unit}_land_use\" a "
            f"inner join \"{self._spatial_unit}\" b on a.suid = b.suid "
            f"where b.\"{self._tableinfo[self._spatial_unit]['key']}\" = '{self._name.replace('|',' ')}' "
            f"and {self.period_where_clause()} "
            f"group by a.land_use_id) b on a.id = b.land_use_id ORDER BY a.priority ASC "
        )
        df.columns = ['Categorias Fundiárias', 'Área (km²)']
        df['Área (km²)'] = df['Área (km²)'].round(3)
        return df

    def form_title(self):
        """
        gets the main title for profile form
        """
        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        last_date=self.format_date(self._start_date)
        spatial_unit=self._tableinfo[self._spatial_unit]['description']
        temporal_unit=self._temporal_units[self._temporal_unit]

        title="""Usando dados de <b>{0}</b> do DETER até <b>{1}</b>,
        com recorte na unidade espacial <b>{2}</b>
        e unidade temporal <b>{3}</b>.
        """.format(indicador,last_date,spatial_unit,temporal_unit)

        return title
        
        # date_label = f"Dados DETER at&eacute;: {self.format_date(self._start_date)}"
        # return f"{self._tableinfo[self._spatial_unit]['description']}: " \
        #        f"{self._name}, Indicador: " \
        #        f"{self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']}" \
        #        f"<br>{date_label}, Unidade temporal: {self._temporal_units[self._temporal_unit]}"

    def fig_area_per_land_use(self):
        df = self.area_per_land_use()
        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        unid_temp=self._temporal_units[self._temporal_unit]
        chart_title="Porcentagem de <b>{0}</b><br>por categoria fundiária<br>no último período do <b>{1}</b>".format(indicador,unid_temp)

        fig = px.pie(df, values='Área (km²)', names='Categorias Fundiárias', template='plotly',
                     color_discrete_sequence=px.colors.sequential.RdBu,
                     title=chart_title )
        #  Dois gráficos cada um com width=400 e' para maiores > 1000px. Height 300, foi um bom aspect ratio
        #  Para calcular o width ideal, a gente pode enviar o device width na requisição
        #    (https://stackoverflow.com/questions/1248081/how-to-get-the-browser-viewport-dimensions)

        # sort=False is used to keep legend order like ordered in dataset
        fig.update_traces(sort=False,textposition='inside')
        fig.update_layout(
            legend_traceorder='normal',
            height=400,
            width=430,
            uniformtext_minsize=10, uniformtext_mode='hide',
            legend=dict(font=dict(size=12)),
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=70,
                pad=0
            ),

            #paper_bgcolor="LightSteelBlue",
        )
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON

    '''
    def fig_area_per_class(self, params):
        df = self.area_per_class(params['click']['name'], params['spatialUnit'])

        fig = px.pie(df, values='Área (km²)', names='Name', template='ggplot2', title='Indicador DETER')
        #  Dois gráficos cada um com width=400 e' para maiores > 1000px. Height 300, foi um bom aspect ratio
        #  Para calcular o width ideal, a gente pode enviar o device width na requisição
        #    (https://stackoverflow.com/questions/1248081/how-to-get-the-browser-viewport-dimensions)
        fig.update_layout(
            height=400,
            width=330,
            title_x=0.5,
            legend=dict(font=dict(size=10))
            #paper_bgcolor="LightSteelBlue",
        )
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON
    '''

    def fig_area_per_year_table_class(self):
        df = self.area_per_year_table_class()
        # set bar colors
        last_period = df.tail(1).values[0][0]
        last_period_items = last_period.split('/')
        precedent_period = f"{int(last_period_items[0])- 1}/{last_period_items[1]}" \
            if len(last_period_items) > 1 else f"{int(last_period_items[0]) - 10}"
        color_discrete_sequence = ['#609cd4'] * len(df)
        color_change_items = df.index[(df['Período']==last_period) | (df['Período']==precedent_period)].tolist()
        for i in color_change_items:
            color_discrete_sequence[i] = '#ec7c34'

        indicador=self._classes.loc[self._classes['code'] == self._classname].iloc[0]['name']
        unid_temp=self._temporal_units[self._temporal_unit]
        chart_title="Evolução temporal de <b>{0}</b> nos períodos do <b>{1}</b><br>(limitado aos últimos 20 períodos).".format(indicador,unid_temp)

        fig = px.bar(df, x='Período', y='Área (km²)', title=chart_title,
                     category_orders = {'Período': df['Período'].to_list()},
                     #height=260,
                     color='Período',
                     color_discrete_sequence=color_discrete_sequence)
                     #title=f"{self._temporal_units[self._temporal_unit]}",)
        offset_annotation = df['Área (km²)'].max() * 0.03
        fig.update_layout(
            height=300,   #acho que ficou melhor que autosize (= que a linha superior)
            width=700,
            xaxis=layout.XAxis(
                type='category',
                tickangle=45,
                title_text="Data de início de cada período"),
            showlegend=False,
            margin=dict(
                l=0,
                r=0,
                b=0,
                t=60,
                pad=0
            ),
            annotations=[
                {'x': x, 'y': total + offset_annotation, 'text': f'{total}', 'showarrow': False}
                for x, total in zip(df.index, df['Área (km²)'].astype(float).round(1))
            ]
        )
        fig.update_yaxes(rangemode= "tozero")
        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return graphJSON
