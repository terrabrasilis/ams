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
		assert sus[0]['last_date'] == '2021-02-28'
		assert sus[1]['dataname'] == 'csAmz_300km'
		assert sus[1]['center_lat'] == -5.491382969006503
		assert sus[1]['center_lng'] == -57.792239759933764
		assert sus[1]['last_date'] == '2021-02-28'
		deter_classes = context['deter_class_groups']
		assert deter_classes[0]['name'] == 'DS'
		assert deter_classes[1]['name'] == 'DG'
		assert deter_classes[2]['name'] == 'CS'
		assert deter_classes[3]['name'] == 'MN'
		ds_classes = deter_classes[0]['classes']
		dg_classes = deter_classes[1]['classes']
		cs_classes = deter_classes[2]['classes']
		mn_classes = deter_classes[3]['classes']
		assert dg_classes[0] == 'CICATRIZ_DE_QUEIMADA'
		assert dg_classes[1] == 'DEGRADACAO'
		assert ds_classes[0] == 'DESMATAMENTO_CR'
		assert ds_classes[1] == 'DESMATAMENTO_VEG'
		assert cs_classes[0] == 'CS_DESORDENADO'
		assert cs_classes[1] == 'CS_GEOMETRICO'	
		assert mn_classes[0] == 'MINERACAO'	
