from geo.Geoserver import Geoserver


geo = Geoserver('http://127.0.0.1:8080/geoserver', username='admin', password='geoserver')
geo.delete_workspace(workspace='ams')
geo.delete_featurestore(featurestore_name='AMS', workspace='ams')
geo.create_workspace(workspace='ams')
geo.create_featurestore(store_name='AMS', workspace='ams', db='AMS', host='localhost', 
	pg_user='postgres', pg_password='postgres')
geo.publish_featurestore(workspace='ams', store_name='AMS', pg_table='csAmz_150km')
