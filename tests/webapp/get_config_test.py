from appconftest import get_context_variables


def test_get_config(app, client, app_startup):
	with get_context_variables(app) as context:
		client.get('/')
		context = next(context)
		assert context['geoserver_url'] != ''
		assert context['workspace'] == 'ams'
		sus = context['spatial_units_info']
		assert sus[0]['dataname'] == 'csAmz_150km'
		assert sus[0]['center_lat'] == -5.491382969006503
		assert sus[0]['center_lng'] == -58.467185764253415
		assert sus[0]['last_date'] == '2021-01-31'
		assert sus[1]['dataname'] == 'csAmz_300km'
		assert sus[1]['center_lat'] == -5.491382969006503
		assert sus[1]['center_lng'] == -57.792239759933764
		assert sus[1]['last_date'] == '2021-01-31'
		deter_classes = context['deter_class_groups']
		assert deter_classes[0]['name'] == 'DS'
		assert deter_classes[1]['name'] == 'DG'
		assert deter_classes[2]['name'] == 'CS'
		assert deter_classes[3]['name'] == 'MN'
