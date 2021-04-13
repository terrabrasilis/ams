import os
from geo.Geoserver import Geoserver


url = 'http://127.0.0.1:8080/geoserver'
workspace = 'ams'
store_name = 'AMS'
username = 'admin'
password = 'geoserver'
this_dir = os.path.dirname(__file__)

geo = Geoserver(url, username=username, password=password)
geo.delete_workspace(workspace=workspace)
geo.delete_featurestore(featurestore_name=store_name, workspace=workspace)
geo.delete_style(style_name='ams_percentage', workspace=workspace)
geo.create_workspace(workspace=workspace)
geo.create_featurestore(store_name=store_name, workspace=workspace, db=store_name, host='localhost', 
	pg_user='postgres', pg_password='postgres')
geo.publish_featurestore(workspace=workspace, store_name=store_name, pg_table='csAmz_150km')
geo.publish_featurestore(workspace=workspace, store_name=store_name, pg_table='csAmz_150km_risk_indicators')
geo.publish_featurestore(workspace=workspace, store_name=store_name, pg_table='csAmz_300km')
geo.publish_featurestore(workspace=workspace, store_name=store_name, pg_table='csAmz_300km_risk_indicators')
# TODO(#20): sql reading from file is not working
# sql = open(f'{this_dir}/sqlviews/csAmz-150km-view.sql').read()
# sqlviews must be configured manually
sql = 'SELECT'
geo.publish_featurestore_sqlview(store_name=store_name, name='csAmz_150km_view', sql=sql, workspace=workspace, 
	key_column='', geom_name='geometry', geom_type='Polygon')
geo.upload_style(path=f'{this_dir}/styles/ams-percentage.sld', name='ams_percentage', workspace=workspace, 
	sld_version='1.1.0')
geo.publish_style(layer_name='csAmz_150km_view', style_name='ams_percentage', workspace=workspace)
