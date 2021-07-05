var ams = ams || {};

ams.App = {
	/**
	 * Default GeoServer workspace for anonymous users.
	 */
	gsWorkspace:'ams',
	/**
	 * Default is no suffix. TO authenticate the suffix is "_auth"
	 */
	gsAuthSuffix:'',

	/**
	 * Evaluates user authentication status and sets appropriate suffix
	 * 
	 * When starting the application or after user login, changes the default suffix
	 * to the suffix suitable for authenticated users.
	 * 
	 * The GeoServer workspace name for AMS or the layer name for Official DETER
	 * for authenticated users uses "_auth" by convention.
	 */
	evaluateAuth: function() {
		ams.App.gsAuthSuffix=( (typeof Authentication!="undefined" && Authentication.hasToken())?("_auth"):("") );
		ams.App.defineWorkspace();// reset workspace name when suffix changes
	},

	/**
	 * Evaluates user authentication status and sets appropriate workspace
	 * 
	 * The GeoServer workspace name for authenticated users is "ams_auth" by convention.
	 */
	defineWorkspace: function() {
		ams.App.gsWorkspace=ams.App.gsWorkspace+ams.App.gsAuthSuffix;
	},

	run: function(geoserverUrl, gsWorkspace, sus, spatialUnits, deterClassGroups) {
		
		ams.App.gsWorkspace=gsWorkspace;
		this.evaluateAuth();

		const updateAll = function(suSource, currSuLayerName, suViewParams, 
								suLayerMinArea, priorSource, priorViewParams, 
								legendControl, map) {
			map.closePopup();
			let suLayerMaxArea = wfs.getMax(currSuLayerName, "area", suViewParams);
			if(suLayerMaxArea == suLayerMinArea) 
			{
				alert("Não existem dados para o periodo selecionado!");
				return;
			}
			let suLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, 
																suLayerMinArea, 
																suLayerMaxArea);	
		 	legendControl.update(currSuLayerName, suLayerStyle);
			ams.Map.update(suSource, currSuLayerName, suViewParams, suLayerStyle);	
			priorLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, 
															suLayerMinArea, 
															suLayerMaxArea, 
															true, "#ff0000");
			ams.Map.update(priorSource, currSuLayerName, priorViewParams, priorLayerStyle);	
			priorLayer.bringToFront();		
		}

		const updateDeterAlerts = function(deterAlertsLayer, deterClassGroups, suViewParams) {
			let source = deterAlertsLayer._source
			source.options["cql_filter"] = deterClassGroups.getCqlFilter(suViewParams);
			source._overlay.setParams({
				"cql_filter": deterClassGroups.getCqlFilter(suViewParams),
			});	
			deterAlertsLayer.bringToBack();
		}

		const addWmsOptionsBase = function(options, identity) {
			let wmsOptionsBase = {
				"transparent": true, 
				"tiled": true, 
				"format": "image/png", 
				"identify": identity,
			}
			for(let k in wmsOptionsBase) {
				options[k] = wmsOptionsBase[k];
			}
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
		var suLayerName = ams.App.gsWorkspace + ":" + spatialUnits.default.dataname;
		var currSuLayerName = suLayerName + "_view";
		var suLayerMaxArea = wfs.getMax(currSuLayerName, "area", 
											suViewParams); 
		var suLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, 0, 
															suLayerMaxArea);
		var wmsUrl = geoserverUrl + "/wms?"
		var wmsOptions = {
				"opacity": 0.8,
				"viewparams": suViewParams.toWmsFormat(),
				"sld_body": suLayerStyle.getSLD(),
		};
		addWmsOptionsBase(wmsOptions, true);
		var suSource = new ams.LeafletWms.Source(wmsUrl, wmsOptions, deterClassGroups); //L.WMS.source(wmsUrl, wmsOptions);
		var suLayer = suSource.getLayer(currSuLayerName);
		suLayer.addTo(map);	

		var priorLayerName = currSuLayerName;
		var priorLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, 0, 
															suLayerMaxArea, 
															true, "#ff0000");
		var priorViewParams = new ams.Map.ViewParams(deterClassGroups.at(0).acronym, 
															dateControll, "10");	
		var priorWmsOptions = {
			"viewparams": priorViewParams.toWmsFormat(),
			"sld_body": priorLayerStyle.getSLD(),
		};
		addWmsOptionsBase(priorWmsOptions, false);

		var priorSource = L.WMS.source(wmsUrl, priorWmsOptions);
		var priorLayer = priorSource.getLayer(currSuLayerName);
		priorLayer.bringToFront();
		priorLayer.addTo(map);

		var tbBiomeLayerName = "prodes-amz:brazilian_amazon_biome_border";
		var onlyWmsBase = {};
		addWmsOptionsBase(onlyWmsBase, false);
		var tbWmsUrl = "http://terrabrasilis.dpi.inpe.br/geoserver/ows";
		var tbBiomeSource = L.WMS.source(tbWmsUrl, onlyWmsBase);
		var tbBiomeLayer = tbBiomeSource.getLayer(tbBiomeLayerName).addTo(map);
		tbBiomeLayer.bringToBack();

		var tbDeterAlertsLayerName = "deter-amz:deter-ams" + ams.App.gsAuthSuffix;
		var tbDeterAlertsWmsOptions = {
			"cql_filter": deterClassGroups.getCqlFilter(suViewParams),
		};		
		addWmsOptionsBase(tbDeterAlertsWmsOptions, true);
		var tbDeterAlertsSource = new ams.LeafletWms.Source(tbWmsUrl, tbDeterAlertsWmsOptions, deterClassGroups); //L.WMS.source(tbWmsUrl, tbDeterAlertsWmsOptions);
		var tbDeterAlertsLayer = tbDeterAlertsSource.getLayer(tbDeterAlertsLayerName).addTo(map);
		tbDeterAlertsLayer.bringToBack();

		var groupedOverlays = {
			"INDICADOR (&#193;rea Km&#178;)": {},
			"UNIDADE ESPACIAL": {
				[spatialUnits.default.name]: suLayer
			},
			"UNIDADE TEMPORAL": {},
			"": {},
		};

		for(var i = 1; i < spatialUnits.length(); i++) {
			let layerName = ams.App.gsWorkspace + ":" + spatialUnits.at(i).dataname + "_view";
			let layer = suSource.getLayer(layerName);
			groupedOverlays["UNIDADE ESPACIAL"][spatialUnits.at(i).name] = layer;
		}

		var classLayer = new L.WMS.Layer(wmsUrl, deterClassGroups.at(0).acronym, 
										onlyWmsBase).addTo(map);	
		groupedOverlays["INDICADOR (&#193;rea Km&#178;)"][deterClassGroups.at(0).name] = classLayer;	

		for(var i = 1; i < deterClassGroups.length(); i++)
		{
			let layer = new L.WMS.Layer(wmsUrl, deterClassGroups.at(i).acronym, onlyWmsBase);	
			groupedOverlays["INDICADOR (&#193;rea Km&#178;)"][deterClassGroups.at(i).name] = layer;
		}

		var temporalUnitAggregates = temporalUnits.getAggregates();
		var tempUnitLayer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[0].key,
											onlyWmsBase).addTo(map);	
		groupedOverlays["UNIDADE TEMPORAL"][temporalUnitAggregates[0].value] = tempUnitLayer;	

		for(var i = 1; i < Object.keys(temporalUnitAggregates).length; i++)
		{
			let layer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[i].key, onlyWmsBase);	
			groupedOverlays["UNIDADE TEMPORAL"][temporalUnitAggregates[i].value] = layer;
		}	

		var temporalUnitsDifferences = temporalUnits.getDifferences();
		var diffLayer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[0].value, 
										onlyWmsBase).addTo(map);
		groupedOverlays[""][temporalUnitsDifferences[0].value] = diffLayer;		
		for(var i = 1; i < Object.keys(temporalUnitsDifferences).length; i++)
		{
			let layer = new L.WMS.Layer(wmsUrl, temporalUnitAggregates[i].value, onlyWmsBase);	
			groupedOverlays[""][temporalUnitsDifferences[i].value] = layer;
		}

		var groupControl = L.control.groupedLayers(null, groupedOverlays, {
			exclusiveGroups: [
				"UNIDADE ESPACIAL", 
				"INDICADOR (&#193;rea Km&#178;)", 
				"UNIDADE TEMPORAL", 
				"",
			],
			collapsed: false,
			position: "topleft",
		}).addTo(map);

		// to apply new heigth for groupControl UI component when window is resized
		ams.groupControl=groupControl;
		
		L.control.coordinates({
			position: "bottomright",
			decimals: 2,
			decimalSeperator:",",
			enableUserInput: false,
			centerUserCoordinates: true,
			useLatLngOrder: false,
			labelTemplateLat: "Latitude: {y}",
			labelTemplateLng: "Longitude: {x}"
		}).addTo(map);				

		var legendControl = new ams.Map.LegendController(map, wmsUrl);
		legendControl.init(currSuLayerName, suLayerStyle);

		(function addPriorizationControl() {
			$('<div class="leaflet-control-layers-group" id="prioritization-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Prioriza&#231;&#227;o </span>'
				+ '<input type="number" id="prioritization-input" min="1" style="width:45px" title="Prioriza&#231;&#227;o" value=' 
				+ priorViewParams.limit + ' />'
				+ '<button id="prioritization-button"> Ok </button>'
				+ '</label></div>').insertAfter("#leaflet-control-layers-group-1");	
		})();	

		(function addDateControl() {
			$('<div class="leaflet-control-layers-group" id="datepicker-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Dados DETER At&#233; </span>'
				+ '<input type="text" id="datepicker" size="7" />'
				+ '<input type="checkbox" id="deter-checkbox" title="Exibir Alertas" checked />'
				+ '</label></div>').insertAfter("#leaflet-control-layers-group-3");
		})();	
		
		(function addFileDownloadControl() {
			$('<div class="leaflet-control-layers-group" id="shapezip-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">BAIXAR</span><br>'
				+ '<button id="csv-download-button"> CSV </button>'
				+ '&nbsp;'
				+ '<button id="shapezip-download-button"> Shapefile </button>'
				+ '</label></div>').insertAfter("#datepicker-control-layers-group");	
		})();				

		var suLayerMinArea = 0;
		var diffON = false;

		map.on('overlayadd', function(e) {
			if(spatialUnits.isSpatialUnit(e.name)) {
				suLayerName = ams.App.gsWorkspace + ":" + spatialUnits.getDataName(e.name);
				if(diffON) {
					currSuLayerName = suLayerName + "_diff_view"; 
				} 
				else {
					currSuLayerName = suLayerName + "_view";
					suLayerMinArea = 0
				}
			}
			else if(temporalUnits.isAggregate(e.name)) {
				currAggregate = e.layer._name;
				dateControll.setPeriod(dateControll.startdate, currAggregate);
				suViewParams.updateDates(dateControll);
				priorViewParams.updateDates(dateControll);	
				updateDeterAlerts(tbDeterAlertsLayer, deterClassGroups, suViewParams);			
			}	
			else if(temporalUnits.isDifference(e.name)) {
				if(e.name == temporalUnits.getCurrentName()) {
					currSuLayerName = suLayerName + "_view";
					suLayerMinArea = 0;
					diffON = false;
				}
				else {
					currSuLayerName =  suLayerName + "_diff_view"; 
					diffON = true;
				}
			}
			else {
				let acronym = e.layer._name;
				suViewParams.classname = acronym;
				priorViewParams.classname = acronym;
				updateDeterAlerts(tbDeterAlertsLayer, deterClassGroups, suViewParams);	
			}

			if(diffON) {
				suLayerMinArea = wfs.getMin(currSuLayerName, "area", suViewParams);
			}			
			
			updateAll(suSource, currSuLayerName, suViewParams, suLayerMinArea, 
					priorSource, priorViewParams, legendControl, map); 			
		});

		map.whenReady(()=>{
			// This approach is necessary because we must wait for the UI control to be rendered to get the actual height.
			window.setTimeout(
				()=>{
					// set control div to available height
					ams.App._onWindowResize();
				},500
			);
		});

		var defaultDate = new Date(currStartdate + "T00:00:00")
		var datepicker = new ams.datepicker.Datepicker();
		$.datepicker.regional['br'] = datepicker.regional("br");
		$.datepicker.setDefaults($.datepicker.regional["br"]);

		$('#datepicker').datepicker({
			showButtonPanel: true,
			defaultDate: new Date(currStartdate + "T00:00:00"),
			minDate: new Date("2017-01-01T00:00:00"),
			maxDate: defaultDate,
			changeMonth: true,
			changeYear: true,	
			todayBtn: "linked",	
			onSelect: function() {
				let selected = $(this).val().split("/");
				let date = selected[2] + "-" + selected[1] + "-" + selected[0];
				dateControll.setPeriod(date, currAggregate);
				suViewParams.updateDates(dateControll);
				priorViewParams.updateDates(dateControll);
				if(currSuLayerName.includes("diff")) {
					suLayerMinArea = wfs.getMin(currSuLayerName, "area", suViewParams);	
				}
				else {
					suLayerMinArea = 0;
				}	

				updateAll(suSource, currSuLayerName, suViewParams, suLayerMinArea, 
						priorSource, priorViewParams, legendControl, map); 
				updateDeterAlerts(tbDeterAlertsLayer, deterClassGroups, suViewParams);										
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

		$("#shapezip-download-button").click(function() {
			wfs.getShapeZip(currSuLayerName, suViewParams);	
			return false;
		});		

		$("#csv-download-button").click(function() {
			wfs.getCsv(currSuLayerName, priorViewParams);	
			return false;
		});		

		$("#deter-checkbox").change(function() {
			if(this.checked) 
			{
				updateDeterAlerts(tbDeterAlertsLayer, deterClassGroups, suViewParams);
				map.addControl(tbDeterAlertsLayer);
			}
			else {
				map.removeControl(tbDeterAlertsLayer);
			}
			return false;
		});
	},

	_onWindowResize: function () {
		ams.groupControl._onWindowResize();
	}
};
