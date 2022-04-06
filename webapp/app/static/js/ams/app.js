var ams = ams || {};

ams.App = {

	zoomThreshold: 11, // used to change the zIndex of the DETER layer in the map layer stack.
	_addedLayers: [],
	_appClassGroups: null,
	_suViewParams: null,
	_priorViewParams: null,
	_wfs: null,
	_dateControl: null,
	_baseURL: null,
	_propertyName: null,
	_referenceLayerName: null,
	_currentSULayerName: null,
	_hasClassFilter: false,// if reference layer is DETER, so, has class filter.
	_suSource: null,
	_priorSource: null,
	_suLayerMinArea: 0,
	_diffOn: false,

	run: function(geoserverUrl, spatialUnits, appClassGroups) {

		this._appClassGroups=appClassGroups;

		this._wfs = new ams.Map.WFS(geoserverUrl);
		var ldLayerName = ams.Auth.getWorkspace() + ":last_date";

		var temporalUnits = new ams.Map.TemporalUnits();
		this._dateControl = new ams.Date.DateController();
		let anonimousLastDate = this._wfs.getLastDate(ldLayerName);
		anonimousLastDate = anonimousLastDate?anonimousLastDate:spatialUnits.default.last_date;
		var currStartdate = spatialUnits.default.last_date; // TODO: uncoment this line (ams.Auth.isAuthenticated())?(spatialUnits.default.last_date):(anonimousLastDate);
		var currAggregate = temporalUnits.getAggregates()[0].key;
		this._dateControl.setPeriod(currStartdate, currAggregate);
		this._baseURL = geoserverUrl + "/wms";
		this._propertyName = ( (ams.Config.defaultFilters.indicator=='AF')?(ams.Config.propertyName.af):(ams.Config.propertyName.deter) );
		this._referenceLayerName = ( (ams.Config.defaultFilters.indicator=='AF')?(ams.Config.defaultLayers.activeFireAmz):(ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.deterAmz) );
		this._hasClassFilter = ( (ams.Config.defaultFilters.indicator=='AF')?(false):(true) );

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
		var tbDeterAlertsLayer = tbDeterAlertsSource.getLayer(tbDeterAlertsLayerName);
		let AFLayer = AFSource.getLayer(AFLayerName);
		if(this._referenceLayerName==tbDeterAlertsLayerName) {
			tbDeterAlertsLayer.addTo(map);
			tbDeterAlertsLayer.bringToBack();
		}else{
			AFLayer.addTo(map);
			AFLayer.bringToBack();
		}
		// Store source to handler layer after controls change
		this._addedLayers[tbDeterAlertsLayerName]=tbDeterAlertsLayer;
		this._addedLayers[AFLayerName]=AFLayer;

		// DEFAULT SPATIAL UNIT LAYER
		var suLayerName = ams.Auth.getWorkspace() + ":" + spatialUnits.default.dataname;
		this._currentSULayerName = suLayerName + "_view";
		ams.Config.defaultFilters.spatialUnit=this._currentSULayerName;// update the default for later use in filter change in control.

		var suLayerMaxArea = this._wfs.getMax(this._currentSULayerName, this._propertyName, this._suViewParams); 
		var suLayerStyle = new ams.SLDStyles.AreaStyle(this._currentSULayerName, this._propertyName, 0, suLayerMaxArea);
		var wmsOptions = {
				"opacity": 0.8,
				"viewparams": this._suViewParams.toWmsFormat(),
				"sld_body": suLayerStyle.getSLD()
		};
		ams.App._addWmsOptionsBase(wmsOptions);
		this._suSource = new ams.LeafletWms.Source(this._baseURL, wmsOptions, appClassGroups);
		var suLayer = this._suSource.getLayer(this._currentSULayerName);
		suLayer.addTo(map);
		this._addedLayers[this._currentSULayerName]=suLayer;
		// adding "_diff_view" layer variation to use later
		let suLayerDiff = this._suSource.getLayer(suLayerName+"_diff_view");
		this._addedLayers[suLayerName+"_diff_view"]=suLayerDiff;

		var priorLayerStyle = new ams.SLDStyles.AreaStyle(this._currentSULayerName, this._propertyName, 0, 
															suLayerMaxArea, 
															true, "#ff0000");
		this._priorViewParams = new ams.Map.ViewParams(appClassGroups.at(0).acronym, 
															ams.App._dateControl, "10");
		var priorWmsOptions = {
			"viewparams": this._priorViewParams.toWmsFormat(),
			"sld_body": priorLayerStyle.getSLD(),
		};
		ams.App._addWmsOptionsBase(priorWmsOptions);

		this._priorSource = L.WMS.source(this._baseURL, priorWmsOptions);
		var priorLayer = this._priorSource.getLayer(this._currentSULayerName);
		priorLayer.bringToFront();
		priorLayer.addTo(map);
		this._addedLayers[this._currentSULayerName+'_prior']=priorLayer;
		// adding "_diff_view" layer variation to use later
		let suPriorLayerDiff = this._priorSource.getLayer(suLayerName+"_diff_view");
		this._addedLayers[suLayerName+"_diff_view_prior"]=suPriorLayerDiff;

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
				propertyName:this._propertyName
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
			let layer = this._suSource.getLayer(layerName);
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

		var legendControl = new ams.Map.LegendController(map, this._baseURL);
		legendControl.init(this._currentSULayerName, suLayerStyle);

		(function addPriorizationControl() {
			$('<div class="leaflet-control-layers-group" id="prioritization-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Prioriza&#231;&#227;o </span>'
				+ '<input type="number" id="prioritization-input" min="1" style="width:45px" title="Alterar o número de unidades espaciais consideradas na priorização de exibição do mapa." value=' 
				+ ams.App._priorViewParams.limit + ' />'
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

		//-- mgd T6 v  keeps an (almost) updated copy of the legend Control's inputs (app.js:legendControl). See app.js:map.on() (-->
		this._suSource.viewConfig = {
			className : this._suViewParams.classname,
			spatialUnit : spatialUnits.default.dataname,
			limit : this._suViewParams.limit,
			tempUnit : currAggregate,
			diffOn : this._diffOn,
			startDate : null,
			endDate :  null,
			prevDate :  null,
			updateDates : function(/* ams.Date.DateController */ dateControll) {
				this.startDate = dateControll.startdate;
				this.endDate = dateControll.enddate;
				this.prevDate = dateControll.prevdate;
			}
		};
		this._suSource.viewConfig.updateDates(ams.App._dateControl);

		map.on('changectrl', function(e) {
			if(spatialUnits.isSpatialUnit(e.name)) {
				ams.App._suSource.viewConfig.spatialUnit =  spatialUnits.getDataName(e.name);  // T6
				suLayerName = ams.Auth.getWorkspace() + ":" + spatialUnits.getDataName(e.name);
				if(ams.App._diffOn) {
					ams.App._currentSULayerName = suLayerName + "_diff_view"; 
				} 
				else {
					ams.App._currentSULayerName = suLayerName + "_view";
					ams.App._suLayerMinArea = 0
				}
			}
			else if(temporalUnits.isAggregate(e.name)) {
				ams.App._suSource.viewConfig.tempUnit= e.layer._name;
				ams.App._suSource.viewConfig.updateDates(ams.App._dateControl);
				currAggregate = e.layer._name;
				ams.App._dateControl.setPeriod(ams.App._dateControl.startdate, currAggregate);
				ams.App._suViewParams.updateDates(ams.App._dateControl);
				ams.App._priorViewParams.updateDates(ams.App._dateControl);
				ams.App._updateReferenceLayer();
			}	
			else if(temporalUnits.isDifference(e.name)) {
				if(e.name == temporalUnits.getCurrentName()) {
					ams.App._currentSULayerName = suLayerName + "_view";
					ams.App._suLayerMinArea = 0;
					ams.App._diffOn = false;
				}
				else {
					ams.App._currentSULayerName =  suLayerName + "_diff_view"; 
					ams.App._diffOn = true;
				}
				ams.App._suSource.viewConfig.diffOn = ams.App._diffOn;  // T6
			}
			else {// is indicator, so set into active layers
				let acronym = e.layer._name;
				ams.App._suSource.viewConfig.className = acronym; // T6
				ams.App._suViewParams.classname = acronym;
				ams.App._priorViewParams.classname = acronym;
				ams.App._updateReferenceLayer();
			}

			if(ams.App._diffOn) {
				ams.App._suLayerMinArea = ams.App._wfs.getMin(ams.App._currentSULayerName, ams.App._propertyName, ams.App._suViewParams);
			}

			ams.App._updateSULayer();
			
			ams.App._updateAll(ams.App._suSource, ams.App._currentSULayerName, ams.App._suViewParams, ams.App._suLayerMinArea, 
					ams.App._priorSource, ams.App._priorViewParams, legendControl);
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
				ams.App._suSource.viewConfig.updateDates(ams.App._dateControl); // T6
				ams.App._suViewParams.updateDates(ams.App._dateControl);
				ams.App._priorViewParams.updateDates(ams.App._dateControl);
				if(ams.App._currentSULayerName.includes("diff")) {
					ams.App._suLayerMinArea = ams.App._wfs.getMin(ams.App._currentSULayerName, ams.App._propertyName, ams.App._suViewParams);	
				}
				else {
					ams.App._suLayerMinArea = 0;
				}

				ams.App._updateAll(ams.App._suSource, ams.App._currentSULayerName, ams.App._suViewParams, ams.App._suLayerMinArea, 
						ams.App._priorSource, ams.App._priorViewParams, legendControl);
				ams.App._updateReferenceLayer();
			},
			beforeShow: function() {
				setTimeout(function() {
					$('.ui-datepicker').css('z-index', 99999999999999);
				}, 0);
			}
		}).val(defaultDate.toLocaleDateString("pt-BR"));		

		function updatePriorization() {
			let limit = document.getElementById("prioritization-input").value;
			ams.App._priorViewParams.limit = limit;
			ams.Map.update(ams.App._priorSource, ams.App._currentSULayerName, ams.App._priorViewParams);	
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
			ams.App._wfs.getShapeZip(ams.App._currentSULayerName, ams.App._suViewParams);	
			return false;
		});		

		$("#csv-download-button").click(function() {
			ams.App._wfs.getCsv(ams.App._currentSULayerName, ams.App._priorViewParams);	
			return false;
		});		

		$("#deter-checkbox").change(function() {
			if(this.checked) 
			{
				ams.App._updateReferenceLayer();//tbDeterAlertsLayer, appClassGroups);
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
		let suLayerMaxArea = ams.App._wfs.getMax(currSuLayerName, ams.App._propertyName, suViewParams);
		if(suLayerMaxArea == suLayerMinArea) 
		{
			alert("Não existem dados para o periodo selecionado.");
			return;
		}else if(ams.App._diffOn && suLayerMinArea>=0){
			alert("Não há redução de valores para o periodo selecionado.");
			return;
		}
		let suLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, ams.App._propertyName,
												suLayerMinArea, 
												suLayerMaxArea);
		legendControl.update(currSuLayerName, suLayerStyle);
		ams.Map.update(suSource, currSuLayerName, suViewParams, suLayerStyle);
		priorLayerStyle = new ams.SLDStyles.AreaStyle(currSuLayerName, ams.App._propertyName,
											suLayerMinArea, 
											suLayerMaxArea, 
											true, "#ff0000");
		ams.Map.update(priorSource, currSuLayerName, priorViewParams, priorLayerStyle);
		let priorLayer=this._addedLayers[currSuLayerName+'_prior']
		if(typeof priorLayer!='undefined') priorLayer.bringToFront();
	},

	/**
	* Update the reference data layer by change CQL filter params
	*/
	_updateReferenceLayer: function() {
		this._hasClassFilter=( (this._referenceLayerName==ams.Config.defaultLayers.activeFireAmz)?(false):(true) );
		let l=this._getLayerByName(this._referenceLayerName);
		if(l && this._map.hasLayer(l)){
			l._source.options["cql_filter"] = ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, this._hasClassFilter);
			l._source._overlay.setParams({
				"cql_filter": ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, this._hasClassFilter)
			});	
			l.bringToBack();
		}
	},

	/**
	 * Update the Spatial Unit layer by change the viewsParams with the new selected class name.
	 * Must change the priority layer associated to Spatial unit layer too.
	 */
	_updateSULayer: function() {
		let l=ams.App._getLayerByName(this._currentSULayerName);
		let suLayerMax=0;
    	if(l && this._map.hasLayer(l)) {
			suLayerMax = this._wfs.getMax(this._currentSULayerName, this._propertyName, this._suViewParams);
			let suLayerStyle = new ams.SLDStyles.AreaStyle(this._currentSULayerName, this._propertyName, 0, suLayerMax);

			let wmsOptions = {
				"opacity": 0.8,
				"viewparams": this._suViewParams.toWmsFormat(),
				"sld_body": suLayerStyle.getSLD()
			};
			this._addWmsOptionsBase(wmsOptions);
			l._source._overlay.setParams(wmsOptions);
			l.bringToFront();
		}
		l=ams.App._getLayerByName(this._currentSULayerName+'_prior');
    	if(l && this._map.hasLayer(l)) {
			let priorLayerStyle = new ams.SLDStyles.AreaStyle(this._currentSULayerName, this._propertyName, 0, suLayerMax, true, "#ff0000");
			let wmsOptions = {
				"opacity": 0.8,
				"viewparams": this._priorViewParams.toWmsFormat(),
				"sld_body": priorLayerStyle.getSLD()
			};
			this._addWmsOptionsBase(wmsOptions);
			l._source._overlay.setParams(wmsOptions);
			l.bringToFront();
		}
	},

	_updateClassFilter: function(classname) {
		if(classname){
			ams.App._suViewParams.setClassname(classname);
			ams.App._priorViewParams.setClassname(classname);
		}
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

	/**
	 * Changes the reference layer on map.
	 * @param {*} layerName can be, deter or queimadas, see the names on Config.js
	 * @param {*} hasClassFilter A boolean value, if reference layer is deter, has class filter, otherwise not.
	 * @param {*} propertyName A column name used to group values, can be, "area" or "counts" if deter or queimadas respectively.
	 */
	_displayReferenceLayer: function(layerName, hasClassFilter, propertyName){
		this._propertyName=propertyName;
		this._referenceLayerName=layerName;
		this._hasClassFilter=hasClassFilter;
		let layer = this._getLayerByName(layerName);
		if(layer) {
			let cql = this._appClassGroups.getCqlFilter(this._suViewParams, this._hasClassFilter);
			layer._source.options["cql_filter"] = cql;
			let cqlobj = {"cql_filter": cql};
			this._addWmsOptionsBase(cqlobj);
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
		if(!layer) {// if not exists
			let priorLayerStyle = new ams.SLDStyles.AreaStyle(layerName, propertyName, 0, suLayerMax, true, "#ff0000");
			let priorWmsOptions = {
				"viewparams": this._priorViewParams.toWmsFormat(),
				"sld_body": priorLayerStyle.getSLD(),
			};
			this._addWmsOptionsBase(priorWmsOptions);

			this._priorSource = L.WMS.source(this._baseURL, priorWmsOptions);
			layer = this._priorSource.getLayer(layerName);
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
