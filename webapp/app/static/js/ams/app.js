var ams = ams || {};

ams.App = {
	run: function(geoserverUrl, gsWorkspace, sus, spatialUnits, deterClassGroups) {
		const updateAll = function(suSource, currSuLayerName, suViewParams, 
								suLayerMinPercentage, priorSource, priorViewParams, 
								legendControl) {
			let suLayerMaxPercentage = wfs.getMax(currSuLayerName, "percentage", suViewParams);
			if(suLayerMaxPercentage == suLayerMinPercentage) 
			{
				alert("Não existem dados para o periodo selecionado!");
				return;
			}
			let suLayerStyle = new ams.SLDStyles.PercentageStyle(currSuLayerName, 
																suLayerMinPercentage, 
																suLayerMaxPercentage);	
		 	legendControl.update(currSuLayerName, suLayerStyle);
			ams.Map.update(suSource, currSuLayerName, suViewParams, suLayerStyle);	
			priorLayerStyle = new ams.SLDStyles.PercentageStyle(currSuLayerName, 
															suLayerMinPercentage, 
															suLayerMaxPercentage, 
															true, "#ff0000");
			ams.Map.update(priorSource, currSuLayerName, priorViewParams, priorLayerStyle);	
			priorLayer.bringToFront();		
		}

		var temporalUnits = new ams.Map.TemporalUnits();
		var dateControll = new ams.Date.DateController();
		var currStartdate = spatialUnits.default.last_date;
		var currAggregate = temporalUnits.getAggregates()[0].key;
		dateControll.setPeriod(currStartdate, currAggregate);

		var wfs = new ams.Map.WFS(geoserverUrl);
		
		var map = new L.Map("map", {
		    zoomControl: false
		});

		map.setView([spatialUnits.default.center_lat, 
					spatialUnits.default.center_lng], 5);

		var osmLayer = new L.TileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
			maxZoom: 18,
			crs: L.CRS.EPSG4326,
		}).addTo(map);

		L.control.zoom({
			position: 'topright'
		}).addTo(map);

		var suViewParams = new ams.Map.ViewParams(deterClassGroups.at(0).acronym, 
												dateControll, "ALL");
		var suLayerName = gsWorkspace + ":" + spatialUnits.default.dataname;
		var currSuLayerName = suLayerName + "_view";
		var suLayerMaxPercentage = wfs.getMax(currSuLayerName, "percentage", 
											suViewParams); 
		var suLayerStyle = new ams.SLDStyles.PercentageStyle(currSuLayerName, 0, 
															suLayerMaxPercentage);
		var wmsUrl = geoserverUrl + "/wms?"
		var wmsOptions = {
			"transparent": true, 
			"tiled": true, 
			"format": "image/png", 
			// "identify": false
			"opacity": 0.8,
			"viewparams": suViewParams.toWmsFormat(),
			"sld_body": suLayerStyle.getSLD(),
		};
		var suSource = L.WMS.source(wmsUrl, wmsOptions);
		var suLayer = suSource.getLayer(currSuLayerName);
		suLayer.addTo(map);	

		var priorLayerName = currSuLayerName;
		var priorLayerStyle = new ams.SLDStyles.PercentageStyle(currSuLayerName, 0, 
															suLayerMaxPercentage, 
															true, "#ff0000");
		var priorViewParams = new ams.Map.ViewParams(deterClassGroups.at(0).acronym, 
															dateControll, "10");	
		var priorWmsOptions = {
			"transparent": true, 
			"tiled": true, 
			"format": "image/png", 
			// "identify": false
			"viewparams": priorViewParams.toWmsFormat(),
			"sld_body": priorLayerStyle.getSLD(),

		};
		var priorSource = L.WMS.source(wmsUrl, priorWmsOptions);
		var priorLayer = priorSource.getLayer(currSuLayerName);
		priorLayer.bringToFront();
		priorLayer.addTo(map);

		var tbBiomeLayerName = "prodes-amz:brazilian_amazon_biome_border";
		var tbWmsOptions = {
			"transparent": true, 
			"tiled": true, 
			"format": "image/png",
		};
		var tbWmsUrl = "http://terrabrasilis.dpi.inpe.br/geoserver/ows";
		var tbSource = L.WMS.source(tbWmsUrl, tbWmsOptions);
		var tbBiomeLayer = tbSource.getLayer(tbBiomeLayerName).addTo(map);
		tbBiomeLayer.bringToBack();

		var groupedOverlays = {
			"INDICADOR": {},
			"UNIDADE ESPACIAL": {
				[spatialUnits.default.name]: suLayer
			},
			"INDICADOR": {},
			"UNIDADE TEMPORAL": {},
			"": {},
		};

		for(var i = 1; i < spatialUnits.length(); i++) {
			let layerName = gsWorkspace + ":" + spatialUnits.at(i).dataname + "_view";
			let layer = suSource.getLayer(layerName);
			groupedOverlays["UNIDADE ESPACIAL"][spatialUnits.at(i).name] = layer;
		}

		var classLayer = new L.WMS.Layer(wmsUrl, deterClassGroups.at(0).acronym, 
										wmsOptions).addTo(map);	
		groupedOverlays["INDICADOR"][deterClassGroups.at(0).name] = classLayer;	

		for(var i = 1; i < deterClassGroups.length(); i++)
		{
			let layer = new L.WMS.Layer(wmsUrl, deterClassGroups.at(i).acronym, wmsOptions);	
			groupedOverlays["INDICADOR"][deterClassGroups.at(i).name] = layer;
		}

		var temporalUnitAggregates = temporalUnits.getAggregates();
		var tempUnitLayer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[0].key,
											wmsOptions).addTo(map);	
		groupedOverlays["UNIDADE TEMPORAL"][temporalUnitAggregates[0].value] = tempUnitLayer;	

		for(var i = 1; i < Object.keys(temporalUnitAggregates).length; i++)
		{
			let layer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[i].key, wmsOptions);	
			groupedOverlays["UNIDADE TEMPORAL"][temporalUnitAggregates[i].value] = layer;
		}	

		var temporalUnitsDifferences = temporalUnits.getDifferences();
		var diffLayer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[0].value, 
										wmsOptions).addTo(map);
		groupedOverlays[""][temporalUnitsDifferences[0].value] = diffLayer;		
		for(var i = 1; i < Object.keys(temporalUnitsDifferences).length; i++)
		{
			let layer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[i].value, wmsOptions);	
			groupedOverlays[""][temporalUnitsDifferences[i].value] = layer;
		}

		var groupControl = L.control.groupedLayers(null, groupedOverlays, {
			exclusiveGroups: ["UNIDADE ESPACIAL", "Indicator", "INDICADOR", "UNIDADE TEMPORAL", ""],
			collapsed: false,
			position: "topleft",
		});

		groupControl.addTo(map);

		var legendControl = new ams.Map.LegendController(map, wmsUrl);
		legendControl.init(currSuLayerName, suLayerStyle);

		(function addDateControl() {
			$('<div class="leaflet-control-layers-group" id="datepicker-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Dados DETER At&#233; </span>'
				+ '<input type="text" id="datepicker" size="7" />'
				+ '</label></div>').insertAfter("#leaflet-control-layers-group-3");
		})();

		(function addPriorizationControl() {
			$('<div class="leaflet-control-layers-group" id="prioritization-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Prioritiza&#231;&#227;o </span>'
				+ '<input type="number" id="prioritization-input" min="1" max="50" value=' 
				+ priorViewParams.limit + ' />'
				+ '<button id="prioritization-button"> Ok </button>'
				+ '</label></div>').insertAfter("#leaflet-control-layers-group-1");	
		})();	

		var suLayerMinPercentage = 0;
		var diffON = false;

		map.on('overlayadd', function(e) {	
			if(spatialUnits.isSpatialUnit(e.name)) {
				suLayerName = gsWorkspace + ":" + e.name;
				if(diffON) {
					currSuLayerName = suLayerName + "_diff_view"; 
					suLayerMinPercentage = wfs.getMin(currSuLayerName, "percentage", suViewParams);
				} 
				else {
					currSuLayerName = suLayerName + "_view";
					suLayerMinPercentage = 0
				}
			}
			else if(temporalUnits.isAggregate(e.name)) {
				currAggregate = e.layer._name;
				dateControll.setPeriod(dateControll.startdate, currAggregate);
				suViewParams.updateDates(dateControll);
				priorViewParams.updateDates(dateControll);
			}	
			else if(temporalUnits.isDifference(e.name)) {
				if(e.name == "NO PER&#205;ODO") {
					currSuLayerName = suLayerName + "_view";
					suLayerMinPercentage = 0;
					diffON = false;
				}
				else {
					currSuLayerName =  suLayerName + "_diff_view"; 
					suLayerMinPercentage = wfs.getMin(currSuLayerName, "percentage", suViewParams);
					diffON = true;
				}
			}
			else {
				let acronym = e.layer._name;
				suViewParams.classname = acronym;
				priorViewParams.classname = acronym;
			}
			
			updateAll(suSource, currSuLayerName, suViewParams, suLayerMinPercentage, 
					priorSource, priorViewParams, legendControl); 			
		});	

		var defaultDate = new Date(currStartdate + "T00:00:00")

		$.datepicker.regional['br'] = {
			closeText: 'Fechar',
			currentText: 'Hoje',
			monthNames: ['Janeiro','Fevereiro','Mar&#231;o','Abril','Maio','Junho', 
						'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'],
			monthNamesShort: ['Jan','Fev','Mar','Abr','Mai','Jun',
							'Jul','Ago','Set','Out','Nov','Dez'],
			dayNames: ['Domingo','Segunda','Ter&#231;a','Quarta','Quinta','Sexta','S&#225;bado'],
			dayNamesShort: ['Dom','Seg','Ter','Qua','Qui','Sex','Sab'],
			dayNamesMin: ['D','S','T','Q','Q','S','S'],
			dateFormat: 'dd/mm/yy',
		};

		$.datepicker.setDefaults($.datepicker.regional["br"]);

		$('#datepicker').datepicker({
			disabled: true,
			showButtonPanel: true,
			defaultDate: new Date(currStartdate + "T00:00:00"),
			minDate: new Date("2017-01-01T00:00:00"),
			maxDate: defaultDate,
			changeMonth: true,
			changeYear: true,			
			onSelect: function() {
				let selected = $(this).val().split("/");
				let date = selected[2] + "-" + selected[1] + "-" + selected[0];
				dateControll.setPeriod(date, currAggregate);
				suViewParams.updateDates(dateControll);
				priorViewParams.updateDates(dateControll);
				if(currSuLayerName.includes("diff")) {
					suLayerMinPercentage = wfs.getMin(currSuLayerName, "percentage", suViewParams);	
				}
				else {
					suLayerMinPercentage = 0;
				}	

				updateAll(suSource, currSuLayerName, suViewParams, suLayerMinPercentage, 
						priorSource, priorViewParams, legendControl); 								
			},
			beforeShow: function() {
				setTimeout(function() {
					$('.ui-datepicker').css('z-index', 99999999999999);
				}, 0);
			}
		}).val(defaultDate.toLocaleDateString("pt-BR"));		

		function updatePriorization() {
			let limit = document.getElementById("prioritization-input").value;
			priorViewParams.limit = limit;
			ams.Map.update(priorSource, currSuLayerName, priorViewParams);	
		}

		$("#prioritization-input").keypress(function(e) {
			if (e.which == 13) {
				updatePriorization();
				return false;
			}
		});

		$("#prioritization-button").click(function() {
			updatePriorization();	
			return false;
		});		

		$(function() {
			$("#prioritization-input").dblclick(false);
		});			
	}
};