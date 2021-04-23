import os
from geo.Geoserver import Geoserver


url = 'http://127.0.0.1:8080/geoserver'
workspace = 'ams'
store_name = 'AMS'
username = 'admin'
password = 'geoserver'
this_dir = os.path.dirname(__file__)
spatial_units = ['csAmz_150km', 'csAmz_300km']

geo = Geoserver(url, username=username, password=password)
geo.delete_workspace(workspace=workspace)
geo.delete_featurestore(featurestore_name=store_name, workspace=workspace)
geo.create_workspace(workspace=workspace)
geo.create_featurestore(store_name=store_name, workspace=workspace, db=store_name, host='localhost', 
	pg_user='postgres', pg_password='postgres')

for spatial_unit in spatial_units:
	geo.publish_featurestore(workspace=workspace, store_name=store_name, pg_table=spatial_unit)
	geo.publish_featurestore(workspace=workspace, store_name=store_name, pg_table=f'{spatial_unit}_risk_indicators')
	# TODO(#20): sql reading from file is not working
	# sql = open(f'{this_dir}/sqlviews/csAmz-150km-view.sql').read()
	# sqlviews must be configured manually
	sql = 'SELECT'
	geo.publish_featurestore_sqlview(store_name=store_name, name=f'{spatial_unit}_view', sql=sql, workspace=workspace, 
		key_column='', geom_name='geometry', geom_type='Polygon')
