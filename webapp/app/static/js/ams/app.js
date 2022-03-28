var ams = ams || {};

ams.App = {

	zoomThreshold: 11, // used to change the zIndex of the DETER layer in the map layer stack.
	_addedLayers: [],
	_appClassGroups: null,
	_suViewParams: null,
	_wfs: null,
	_dateControl: null,
	_baseURL: null,

	run: function(geoserverUrl, spatialUnits, appClassGroups) {

		this._appClassGroups=appClassGroups;

		this._wfs = new ams.Map.WFS(geoserverUrl);
		var ldLayerName = ams.Auth.getWorkspace() + ":last_date";

		var temporalUnits = new ams.Map.TemporalUnits();
		this._dateControl = new ams.Date.DateController();
		let anonimousLastDate = this._wfs.getLastDate(ldLayerName)
		anonimousLastDate = anonimousLastDate?anonimousLastDate:spatialUnits.default.last_date;
		var currStartdate = (ams.Auth.isAuthenticated())?(spatialUnits.default.last_date):(anonimousLastDate);
		var currAggregate = temporalUnits.getAggregates()[0].key;
		this._dateControl.setPeriod(currStartdate, currAggregate);
		this._baseURL = geoserverUrl + "/wms";
		
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

		L.control.scale({position: 'bottomright'}).addTo(map);
    
		map.on('zoomend',function(e){
			let currZoom = map.getZoom();
			if(currZoom >= ams.App.zoomThreshold){
				if(tbDeterAlertsLayer) tbDeterAlertsLayer.bringToFront();
			}else if(currZoom < ams.App.zoomThreshold) {
				if(tbDeterAlertsLayer) tbDeterAlertsLayer.bringToBack();
			}
		});

		// Starting viewParams
		this._suViewParams = new ams.Map.ViewParams(appClassGroups.at(0).acronym, ams.App._dateControl, "ALL");

		// Adding reference layers
		var tbDeterAlertsLayerName = ams.Auth.getWorkspace() + ":" + ams.Config.defaultLayers.deterAmz;
		var AFLayerName = ams.Config.defaultLayers.activeFireAmz;
		var tbDeterAlertsWmsOptions = {
			"cql_filter": appClassGroups.getCqlFilter(this._suViewParams, true)
		};
		ams.App._addWmsOptionsBase(tbDeterAlertsWmsOptions);
		var AFWmsOptions = {
			"cql_filter": appClassGroups.getCqlFilter(this._suViewParams, false)
		};
		ams.App._addWmsOptionsBase(AFWmsOptions);
		var tbDeterAlertsSource = new ams.LeafletWms.Source(this._baseURL, tbDeterAlertsWmsOptions, appClassGroups);
		var AFSource = new ams.LeafletWms.Source(this._baseURL, AFWmsOptions, appClassGroups);
		var tbDeterAlertsLayer = tbDeterAlertsSource.getLayer(tbDeterAlertsLayerName).addTo(map);
		tbDeterAlertsLayer.bringToBack();
		// Store source to handler layer after controls change
		this._addedLayers[tbDeterAlertsLayerName]=tbDeterAlertsLayer;
		this._addedLayers[AFLayerName]=AFSource.getLayer(AFLayerName);

		// DEFAULT SPATIAL UNIT LAYER
		var suLayerName = ams.Auth.getWorkspace() + ":" + spatialUnits.default.dataname;
		var currSuLayerName = suLayerName + "_view";
		ams.Config.defaultFilters.spatialUnit=currSuLayerName;// update the default for later use in filter change in control.

		var suLayerMaxArea = this._wfs.getMax(currSuLayerName, "area", this._suViewParams); 
		var suLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, "area", 0, suLayerMaxArea);
		var wmsOptions = {
				"opacity": 0.8,
				"viewparams": this._suViewParams.toWmsFormat(),
				"sld_body": suLayerStyle.getSLD()
		};
		ams.App._addWmsOptionsBase(wmsOptions);
		var suSource = new ams.LeafletWms.Source(this._baseURL, wmsOptions, appClassGroups);
		var suLayer = suSource.getLayer(currSuLayerName);
		suLayer.addTo(map);
		this._addedLayers[currSuLayerName]=suLayer;

		var priorLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, "area", 0, 
															suLayerMaxArea, 
															true, "#ff0000");
		var priorViewParams = new ams.Map.ViewParams(appClassGroups.at(0).acronym, 
															ams.App._dateControl, "10");	
		var priorWmsOptions = {
			"viewparams": priorViewParams.toWmsFormat(),
			"sld_body": priorLayerStyle.getSLD(),
		};
		ams.App._addWmsOptionsBase(priorWmsOptions);

		var priorSource = L.WMS.source(this._baseURL, priorWmsOptions);
		var priorLayer = priorSource.getLayer(currSuLayerName);
		priorLayer.bringToFront();
		priorLayer.addTo(map);
		this._addedLayers[currSuLayerName+'_prior']=priorLayer;

		// Fixed biome border layer
		var tbBiomeLayerName = ams.Config.defaultLayers.biomeBorder;
		var onlyWmsBase = {};
		ams.App._addWmsOptionsBase(onlyWmsBase);
		var tbBiomeSource = L.WMS.source(this._baseURL, onlyWmsBase);
		var tbBiomeLayer = tbBiomeSource.getLayer(tbBiomeLayerName).addTo(map);
		tbBiomeLayer.bringToBack();

		// this structure is used into leaflet.groupedlayercontrol.js
		var controlGroups = {
			"INDICADOR": {
				defaultFilter:ams.Config.defaultFilters.indicator,
				propertyName:( (ams.Config.defaultFilters.indicator=='AF')?('counts'):('area') )
			},
			"UNIDADE ESPACIAL": {
				defaultFilter: ams.Config.defaultFilters.spatialUnit,
				[spatialUnits.default.name]: suLayer
			},
			"UNIDADE TEMPORAL": {defaultFilter:ams.Config.defaultFilters.temporalUnit},
			"CLASSIFICAÇÃO DO MAPA": {defaultFilter:ams.Config.defaultFilters.diffClassify},
		};

		for(var i = 1; i < spatialUnits.length(); i++) {
			let layerName = ams.Auth.getWorkspace() + ":" + spatialUnits.at(i).dataname + "_view";
			let layer = suSource.getLayer(layerName);
			controlGroups["UNIDADE ESPACIAL"][spatialUnits.at(i).name] = layer;
			this._addedLayers[layerName]=layer;
		}

		// TODO: Avoid this creation layer, it's wrong!!
		var classLayer = new L.WMS.Layer(this._baseURL, appClassGroups.at(0).acronym, 
										onlyWmsBase);//.addTo(map);	
		controlGroups["INDICADOR"][appClassGroups.at(0).name] = classLayer;	

		for(var i = 1; i < appClassGroups.length(); i++)
		{
			let layer = new L.WMS.Layer(this._baseURL, appClassGroups.at(i).acronym, onlyWmsBase);	
			controlGroups["INDICADOR"][appClassGroups.at(i).name] = layer;
		}

		var temporalUnitAggregates = temporalUnits.getAggregates();
		var tempUnitLayer = new L.WMS.Layer(this._baseURL, temporalUnitAggregates[0].key,
											onlyWmsBase);//.addTo(map);	
		controlGroups["UNIDADE TEMPORAL"][temporalUnitAggregates[0].value] = tempUnitLayer;	

		for(var i = 1; i < Object.keys(temporalUnitAggregates).length; i++)
		{
			let layer = new L.WMS.Layer(this._baseURL, temporalUnitAggregates[i].key, onlyWmsBase);	
			controlGroups["UNIDADE TEMPORAL"][temporalUnitAggregates[i].value] = layer;
		}	

		var temporalUnitsDifferences = temporalUnits.getDifferences();
		var diffLayer = new L.WMS.Layer(this._baseURL, temporalUnitsDifferences[0].key, 
										onlyWmsBase);//.addTo(map);
		controlGroups["CLASSIFICAÇÃO DO MAPA"][temporalUnitsDifferences[0].value] = diffLayer;		
		for(var i = 1; i < Object.keys(temporalUnitsDifferences).length; i++)
		{
			let layer = new L.WMS.Layer(this._baseURL, temporalUnitsDifferences[i].key, onlyWmsBase);	
			controlGroups["CLASSIFICAÇÃO DO MAPA"][temporalUnitsDifferences[i].value] = layer;
		}

		var groupControl = L.control.groupedLayers(controlGroups, {
			exclusiveGroups: [
				"UNIDADE ESPACIAL", 
				"INDICADOR", 
				"UNIDADE TEMPORAL", 
				"CLASSIFICAÇÃO DO MAPA",
			],
			collapsed: false,
			position: "topleft",
		}, tbDeterAlertsLayerName).addTo(map);

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

		var legendControl = new ams.Map.LegendController(map, this._baseURL);
		legendControl.init(currSuLayerName, suLayerStyle);

		(function addPriorizationControl() {
			$('<div class="leaflet-control-layers-group" id="prioritization-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Prioriza&#231;&#227;o </span>'
				+ '<input type="number" id="prioritization-input" min="1" style="width:45px" title="Alterar o número de unidades espaciais consideradas na priorização de exibição do mapa." value=' 
				+ priorViewParams.limit + ' />'
				+ '<button class="btn btn-primary-p" id="prioritization-button" style="margin-left: 10px;"> Ok </button>'
				+ '</label></div>').insertAfter("#leaflet-control-layers-group-1");	
		})();	

		(function addDateControl() {
			$('<div class="leaflet-control-layers-group" id="datepicker-control-layers-group">'
			    + '<label class="leaflet-control-layers-group-label">'
				+ '<span class="leaflet-control-layers-group-name">DADOS DETER</span></label>'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Exibir camada DETER </span>'
				+ '<input type="checkbox" id="deter-checkbox" title="Ligar/desligar camada DETER." checked /></label>'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Usar DETER at&#233; </span>'
				+ '<input type="text" id="datepicker" size="7" /></label>'
				+ '</div>').insertAfter("#leaflet-control-layers-group-3");
		})();	
		
		(function addFileDownloadControl() {
			$('<div class="leaflet-control-layers-group" id="shapezip-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-label">'
				+ '<span class="leaflet-control-layers-group-name">DOWNLOAD</span></label>'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span style="white-space: pre-wrap;">'
				+ 'Baixar arquivo da unidade\nespacial selecionada.</span></label>'
				+ '<label class="leaflet-control-layers-group-name btn-download">'
				+ '<button class="btn btn-primary-p btn-success" id="csv-download-button"> CSV </button>'
				+ '&nbsp;&nbsp;'
				+ '<button class="btn btn-primary-p btn-success" id="shapezip-download-button"> Shapefile </button>'
				+ '</label>'
				+ '</div>').insertAfter("#datepicker-control-layers-group");	
		})();

		var suLayerMinArea = 0;
		var diffON = false;


		//-- mgd T6 v  keeps an (almost) updated copy of the legend Control's inputs (app.js:legendControl). See app.js:map.on() (-->
		suSource.viewConfig = {
			className : this._suViewParams.classname,
			spatialUnit : spatialUnits.default.dataname,
			limit : this._suViewParams.limit,
			tempUnit : currAggregate,
			diffOn : diffON,
			startDate : null,
			endDate :  null,
			prevDate :  null,
			updateDates : function(/* ams.Date.DateController */ dateControll) {
				this.startDate = dateControll.startdate;
				this.endDate = dateControll.enddate;
				this.prevDate = dateControll.prevdate;
			}
		};
		suSource.viewConfig.updateDates(ams.App._dateControl);
		// -- ^ -->

		//map.on('overlayadd', function(e) {
		map.on('changectrl', function(e) {
			if(spatialUnits.isSpatialUnit(e.name)) {
				suSource.viewConfig.spatialUnit =  spatialUnits.getDataName(e.name);  // T6
				suLayerName = ams.Auth.getWorkspace() + ":" + spatialUnits.getDataName(e.name);
				if(diffON) {
					currSuLayerName = suLayerName + "_diff_view"; 
				} 
				else {
					currSuLayerName = suLayerName + "_view";
					suLayerMinArea = 0
				}
			}
			else if(temporalUnits.isAggregate(e.name)) {
				suSource.viewConfig.tempUnit= e.layer._name;  // T6
				suSource.viewConfig.updateDates(ams.App._dateControl); // T6
				currAggregate = e.layer._name;
				ams.App._dateControl.setPeriod(ams.App._dateControl.startdate, currAggregate);
				ams.App._suViewParams.updateDates(ams.App._dateControl);
				priorViewParams.updateDates(ams.App._dateControl);	
				ams.App._updateReferenceLayer(tbDeterAlertsLayer, appClassGroups);			
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
				suSource.viewConfig.diffOn = diffON;  // T6
			}
			else {
				let acronym = e.layer._name;
				suSource.viewConfig.className = acronym; // T6
				ams.App._suViewParams.classname = acronym;
				priorViewParams.classname = acronym;
				ams.App._updateReferenceLayer(tbDeterAlertsLayer, appClassGroups);	
			}

			if(diffON) {
				suLayerMinArea = ams.App._wfs.getMin(currSuLayerName, "area", ams.App._suViewParams);
			}			
			
			ams.App._updateAll(suSource, currSuLayerName, ams.App._suViewParams, suLayerMinArea, 
					priorSource, priorViewParams, legendControl); 			
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
				ams.App._dateControl.setPeriod(date, currAggregate);
				suSource.viewConfig.updateDates(ams.App._dateControl); // T6
				ams.App._suViewParams.updateDates(ams.App._dateControl);
				priorViewParams.updateDates(ams.App._dateControl);
				if(currSuLayerName.includes("diff")) {
					suLayerMinArea = ams.App._wfs.getMin(currSuLayerName, "area", ams.App._suViewParams);	
				}
				else {
					suLayerMinArea = 0;
				}	

				ams.App._updateAll(suSource, currSuLayerName, ams.App._suViewParams, suLayerMinArea, 
						priorSource, priorViewParams, legendControl);
				ams.App._updateReferenceLayer(tbDeterAlertsLayer, appClassGroups);
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
			ams.App._wfs.getShapeZip(currSuLayerName, ams.App._suViewParams);	
			return false;
		});		

		$("#csv-download-button").click(function() {
			ams.App._wfs.getCsv(currSuLayerName, priorViewParams);	
			return false;
		});		

		$("#deter-checkbox").change(function() {
			if(this.checked) 
			{
				ams.App._updateReferenceLayer(tbDeterAlertsLayer, appClassGroups);
				map.addControl(tbDeterAlertsLayer);
			}
			else {
				map.removeControl(tbDeterAlertsLayer);
			}
			return false;
		});
		this._map=map;
	},

	_updateAll: function(suSource, currSuLayerName, suViewParams, 
		suLayerMinArea, priorSource, priorViewParams, 
		legendControl) {
		this._map.closePopup();
		let suLayerMaxArea = ams.App._wfs.getMax(currSuLayerName, "area", suViewParams);
		if(suLayerMaxArea == suLayerMinArea) 
		{
			alert("Não existem dados para o periodo selecionado."); // mgd T6 Change an exclamation point to a period
			return;
		}
		let suLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, "area",
												suLayerMinArea, 
												suLayerMaxArea);
		legendControl.update(currSuLayerName, suLayerStyle);
		ams.Map.update(suSource, currSuLayerName, suViewParams, suLayerStyle);
		priorLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, "area",
											suLayerMinArea, 
											suLayerMaxArea, 
											true, "#ff0000");
		ams.Map.update(priorSource, currSuLayerName, priorViewParams, priorLayerStyle);
		// let priorLayer=this._addedLayers[currSuLayerName+'_prior']
		// priorLayer.bringToFront();
	},

	/**
	* Update the reference data layer by change CQL filter params
	* @param {*} refLayer, the reference layer can be: Alerts or Active fires
	*/
	_updateReferenceLayer: function(refLayer, hasClassFilter) {
		refLayer._source.options["cql_filter"] = ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, hasClassFilter);
		refLayer._source._overlay.setParams({
			"cql_filter": ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, hasClassFilter),
		});	
		refLayer.bringToBack();
	},

	_updateFilter: function(filters) {
		if(filters.classname)
			ams.App._suViewParams.setClassname(filters.classname);		
	},

	_addAutorizationToken: function(options) {
		if(ams.Auth.isAuthenticated()){
			if(!options) options={};
			options["access_token"]=Authentication.getToken();
		}
	},

	_addWmsOptionsBase: function(options) {
		this._addAutorizationToken(options);
		let wmsOptionsBase = {
			"transparent": true, 
			"tiled": true, 
			"format": "image/png"
		}
		for(let k in wmsOptionsBase) {
			options[k] = wmsOptionsBase[k];
		}
	},

	_displayReferenceLayer: function(layerName, hasClassFilter){
		hasClassFilter=hasClassFilter?hasClassFilter:false;// do not use class filter by default
		let layer = this._getLayerByName(layerName);
		if(layer) {
			let cql = ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, hasClassFilter);
			layer._source.options["cql_filter"] = cql;
			let cqlobj = {"cql_filter": cql};
			ams.App._addWmsOptionsBase(cqlobj);
			layer._source._overlay.setParams(cqlobj);
			layer.addTo(this._map);
			layer.bringToBack();
		}
	},

	/**
	 * Adding the spatial unit layer into map using updated viewParams
	 * @param {*} layerName the spatial unit layer name
	 * @param {*} propertyName column "area" or "counts"
	 */
	_displaySpatialUnitLayer: function(layerName, propertyName){
		let layer = this._getLayerByName(layerName);
		let suLayerMax=0;
		if(layer) {
			suLayerMax = this._wfs.getMax(layerName, propertyName, this._suViewParams);
			let suLayerStyle = new ams.SLDStyles.AreaStyle(layerName, propertyName, 0, suLayerMax);

			let wmsOptions = {
				"opacity": 0.8,
				"viewparams": this._suViewParams.toWmsFormat(),
				"sld_body": suLayerStyle.getSLD()
			};
			this._addWmsOptionsBase(wmsOptions);
			layer._source._overlay.setParams(wmsOptions);
			layer.addTo(this._map);
		}

		//insert spatial unit priority layer
		layer = this._getLayerByName(layerName+'_prior');
		if(!layer) {
			let priorLayerStyle = new ams.SLDStyles.AreaStyle(layerName, propertyName, 0, suLayerMax, true, "#ff0000");
			let priorViewParams = new ams.Map.ViewParams(this._suViewParams.getClassname(), this._dateControl, "10");
			let priorWmsOptions = {
				"viewparams": priorViewParams.toWmsFormat(),
				"sld_body": priorLayerStyle.getSLD(),
			};
			this._addWmsOptionsBase(priorWmsOptions);

			let priorSource = L.WMS.source(this._baseURL, priorWmsOptions);
			layer = priorSource.getLayer(layerName);
			this._addedLayers[layerName+'_prior']=layer;
		}
		layer.addTo(this._map);
		layer.bringToFront();
	},

	_getLayerByName: function(layerName){
		return ( (typeof this._addedLayers[layerName]=='undefined')?(false):(this._addedLayers[layerName]) );
	},

	_onWindowResize: function () {
		ams.groupControl._onWindowResize();
	},

	displayGraph: function( jsConfig ) {
		async function getGraphics(  jsConfig ) {
			let jsConfigStr = JSON.stringify(jsConfig);
			let response = await fetch("callback/area_profile?sData=" + jsConfigStr);
			$("#loading_data_info").css('display','none')
			if (response.ok) {
				let profileJson = await response.json();
				if (response.ok) {
					document.getElementById("txt3a").innerHTML = profileJson['FormTitle'];
					Plotly.react('AreaPerYearTableClass', JSON.parse(profileJson['AreaPerYearTableClass']), {});
					Plotly.react('AreaPerLandUse', JSON.parse(profileJson['AreaPerLandUse']), {});
					$('#modal-container-general-info').modal();
				} else {
					console.log("HTTP-Error: " + response.status + " on area_profile");
					alert("Encontrou um erro na solicitação ao servidor.");
				}
			} else {
				console.log("HTTP-Error: " + response.status + " on area_profile");
				alert("Encontrou um erro na solicitação ao servidor.");
			}
		}
		if (jsConfig.click.classname != 'null'){
			$("#loading_data_info").css('display','block');
			getGraphics(jsConfig);
		}
	}
};
