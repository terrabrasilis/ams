var ams = ams || {};

ams.App = {

	zoomThreshold: 11, // used to change the zIndex of the DETER layer in the map layer stack.
	_layerControl: null,
	_baseLayers: [],
	_addedLayers: [],
	_biomeLayer: null,
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
	_diffOn: false,
	_currentTemporalAggregate: null,
	_currentClassify: null,

	run: function(geoserverUrl, spatialUnits, appClassGroups) {

		this._appClassGroups=appClassGroups;

		this._wfs = new ams.Map.WFS(geoserverUrl);
		var ldLayerName = ams.Auth.getWorkspace() + ":last_date";

		// set the appropriate workspace name if it is homologation environment
		if(ams.Utils.isHomologationEnvironment()){
			ams.Config.defaultLayers.activeFireAmz=ams.Config.defaultLayers.activeFireAmz.replace('ams','amsh');
		}

		var temporalUnits = new ams.Map.TemporalUnits();
		this._dateControl = new ams.Date.DateController();
		let anonimousLastDate = this._wfs.getLastDate(ldLayerName);
		anonimousLastDate = anonimousLastDate?anonimousLastDate:spatialUnits.default.last_date;
		var currStartdate = (ams.Auth.isAuthenticated())?(spatialUnits.default.last_date):(anonimousLastDate);
		this._currentTemporalAggregate = temporalUnits.getAggregates()[0].key;
		this._dateControl.setPeriod(currStartdate, this._currentTemporalAggregate);
		this._baseURL = geoserverUrl + "/wms";
		this._propertyName = ( (ams.Config.defaultFilters.indicator=='AF')?(ams.Config.propertyName.af):(ams.Config.propertyName.deter) );
		this._referenceLayerName = ( (ams.Config.defaultFilters.indicator=='AF')?(ams.Config.defaultLayers.activeFireAmz):(ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.deterAmz) );
		this._hasClassFilter = ( (ams.Config.defaultFilters.indicator=='AF')?(false):(true) );
		this._currentClassify=ams.Config.defaultFilters.diffClassify;

		var map = new L.Map("map", {
		    zoomControl: false
		});
		this._map=map;

		// improve control positions for Leaflet
		ams.LeafletControlPosition.addNewPositions(map);

		map.setView([spatialUnits.default.center_lat, spatialUnits.default.center_lng], 5);

		this._baseLayers["osm"] = new L.TileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
			attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
			maxZoom: 18,
			crs: L.CRS.EPSG4326,
		}).addTo(map);

		this._baseLayers["blank"] = new L.TileLayer("");

		// L.control.zoom({
		// 	position: 'topright'
		// }).addTo(map);

		L.control.scale({position: 'bottomright'}).addTo(map);
    
		map.on('zoomend',function(e){
			let currZoom = map.getZoom();
			let l=ams.App._getLayerByName(ams.App._referenceLayerName);
			if(!l) return;
			if(currZoom >= ams.App.zoomThreshold) l.bringToFront();
			else l.bringToBack();
		});

		// Starting viewParams
		this._suViewParams = new ams.Map.ViewParams(ams.Config.defaultFilters.indicator, ams.App._dateControl, ams.App._propertyName, "ALL");
		this._priorViewParams = new ams.Map.ViewParams(ams.Config.defaultFilters.indicator, ams.App._dateControl, ams.App._propertyName, ams.Config.defaultFilters.priorityLimit);

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
		// Store layers to handler after controls change
		this._addedLayers[tbDeterAlertsLayerName]=tbDeterAlertsLayer;
		this._addedLayers[AFLayerName]=AFLayer;

		// Start the legend control
		this._legendControl = new ams.Map.LegendController(map, this._baseURL);

		// Default Spatial Unit layer
		this._currentSULayerName = ams.Auth.getWorkspace() + ":" + spatialUnits.default.dataname;
		ams.Config.defaultFilters.spatialUnit=this._currentSULayerName;// update the default for later use in filter change in control.
		this._addSpatialUnitLayer(this._getLayerPrefix(),this._propertyName);

		// Fixed biome border layer
		var tbBiomeLayerName = ams.Config.defaultLayers.biomeBorder;
		var onlyWmsBase = {identify:false};// set this to disable GetFeatureInfo
		ams.App._addWmsOptionsBase(onlyWmsBase);
		var tbBiomeSource = new ams.LeafletWms.Source(this._baseURL, onlyWmsBase, this._appClassGroups);
		ams.App._biomeLayer = tbBiomeSource.getLayer(tbBiomeLayerName);
		ams.App._biomeLayer.addTo(map).bringToBack();

		// ---------------------------------------------------------------------------------
		// this structure is used into leaflet.groupedlayercontrol.js to create controls for filters panel...
		var controlGroups = {
			"INDICADOR": {
				defaultFilter:ams.Config.defaultFilters.indicator,
				propertyName:this._propertyName
			},
			"UNIDADE ESPACIAL": {
				defaultFilter: ams.Config.defaultFilters.spatialUnit
			},
			"UNIDADE TEMPORAL": {defaultFilter:ams.Config.defaultFilters.temporalUnit},
			"CLASSIFICAÇÃO DO MAPA": {defaultFilter:ams.Config.defaultFilters.diffClassify},
		};

		for(var i = 0; i < spatialUnits.length(); i++) {
			let layerName = ams.Auth.getWorkspace() + ":" + spatialUnits.at(i).dataname;
			controlGroups["UNIDADE ESPACIAL"][spatialUnits.at(i).name] = layerName;
		}

		for(var i = 0; i < appClassGroups.length(); i++) {
			controlGroups["INDICADOR"][appClassGroups.at(i).name] = appClassGroups.at(i).acronym;
		}

		var temporalUnitAggregates = temporalUnits.getAggregates();
		for(var i = 0; i < Object.keys(temporalUnitAggregates).length; i++) {
			controlGroups["UNIDADE TEMPORAL"][temporalUnitAggregates[i].value] = temporalUnitAggregates[i].key;
		}	

		var temporalUnitsDifferences = temporalUnits.getDifferences();
		for(var i = 0; i < Object.keys(temporalUnitsDifferences).length; i++) {
			controlGroups["CLASSIFICAÇÃO DO MAPA"][temporalUnitsDifferences[i].value] = temporalUnitsDifferences[i].key;
		}
		// ---------------------------------------------------------------------------------

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

		// Adding period control over map
		ams.PeriodHandler.init(map);

		// Adding control layer over map
		this._addControlLayer();

		(function addPriorizationControl() {
			$('<div class="leaflet-control-layers-group" id="prioritization-control-layers-group">'
				+ '<label class="leaflet-control-layers-group-name">'
				+ '<span class="leaflet-control-layers-group-name">Prioriza&#231;&#227;o </span>'
				+ '<input type="number" id="prioritization-input" min="1" style="width:45px" title="Alterar o número de unidades espaciais consideradas na priorização de exibição do mapa." value=' 
				+ ams.App._priorViewParams.limit + ' />'
				+ '<button class="btn btn-primary-p" id="prioritization-button" style="margin-left: 10px;"> Ok </button>'
				+ '</label></div>').insertAfter("#leaflet-control-layers-group-1");	
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
				+ '</div>').insertAfter("#leaflet-control-layers-group-3");
				//insertAfter("#datepicker-control-layers-group");
		})();

		map.on('changectrl', function(e) {
			let layerToAdd,layerToDel,needUpdateSuLayers=true;
			// change reference layer (deter or fires)?
			if(e.group.name=='INDICADOR'){
				if(e.acronym=='AF'){
					// the reference layer should be active-fires
					layerToAdd=ams.Config.defaultLayers.activeFireAmz;
					layerToDel=ams.Auth.getWorkspace() + ":" + ams.Config.defaultLayers.deterAmz;
					ams.App._propertyName=ams.Config.propertyName.af;
					ams.App._hasClassFilter=false;
				}else{
					// the reference layer should be deter
					layerToAdd=ams.Auth.getWorkspace() + ":" + ams.Config.defaultLayers.deterAmz;
					layerToDel=ams.Config.defaultLayers.activeFireAmz;
					ams.App._propertyName=ams.Config.propertyName.deter;		
					ams.App._hasClassFilter=true;
				}
				if(ams.App._suViewParams.classname != e.acronym){
					ams.App._suViewParams.classname = e.acronym;
					ams.App._priorViewParams.classname = e.acronym;
					ams.App._suViewParams.updatePropertyName(ams.App._propertyName);
					ams.App._priorViewParams.updatePropertyName(ams.App._propertyName);
				}
				// reference layer was changes, so propertyName changes too
				if(ams.App._referenceLayerName!=layerToAdd){
					ams.App._exchangeReferenceLayer(layerToDel, layerToAdd);
				}else if(ams.App._hasClassFilter){
					// apply change filters on reference layer
					ams.App._updateReferenceLayer();
				}
			}else if(e.group.name=='UNIDADE ESPACIAL'){
				// spatial unit layer was changes
				if(ams.App._currentSULayerName!=e.acronym){
					// old layer to remove
					let oLayerName=ams.App._getLayerPrefix();
					// set the new name
					ams.App._currentSULayerName=e.acronym;
					//  new layer to insert
					let nLayerName=ams.App._getLayerPrefix();
					ams.App._exchangeSpatialUnitLayer(oLayerName,nLayerName);
					needUpdateSuLayers=false;// no need to update because SU layers were swapped by previous command
				}
			}else if(e.group.name=='CLASSIFICAÇÃO DO MAPA'){
				ams.App._diffOn = ( (e.acronym=="onPeriod")?(false):(true) );
				// diff classify was changes
				if(ams.App._currentClassify!=e.acronym){
					// remove and insert the same layer, but on reinsert the correct prefix is used to apply the right classification
					let oLayerName=ams.App._getLayerPrefix();
					ams.App._currentClassify=e.acronym;// change for new classify method to get the new layer prefix
					let nLayerName=ams.App._getLayerPrefix();
					ams.App._exchangeSpatialUnitLayer(oLayerName,nLayerName);
					needUpdateSuLayers=false;// no need to update because SU layers were swapped by previous command
				}
			}else if(temporalUnits.isAggregate(e.name)) {// time aggregate selects: weekly, monthly, yearly...
				ams.App._currentTemporalAggregate = e.acronym;
				ams.PeriodHandler.changeDate(ams.App._dateControl.startdate);// Internally invokes layer update.
				needUpdateSuLayers=false;
			}

			if(needUpdateSuLayers) ams.App._updateSpatialUnitLayer();
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

		function updatePriorization() {
			let limit = document.getElementById("prioritization-input").value;
			ams.App._priorViewParams.limit = limit;
			ams.App._updateSpatialUnitLayer(true);
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
			ams.App._wfs.getShapeZip(ams.App._getLayerPrefix(), ams.App._suViewParams);	
			return false;
		});		

		$("#csv-download-button").click(function() {
			ams.App._wfs.getCsv(ams.App._getLayerPrefix(), ams.App._priorViewParams);	
			return false;
		});

		$("#threshold").on("change", ()=>{
			let v=+$("#threshold").val();
			ams.Config.general.area.threshold=v;
			localStorage.setItem('ams.Config.general.area.threshold', v);
		});

		$("#changeunit").on("change", ()=>{
			let v=$("#changeunit")[0].checked;
			if(v) ams.Config.general.area.changeunit="auto";
			else ams.Config.general.area.changeunit="no";
			localStorage.setItem('ams.Config.general.area.changeunit', ams.Config.general.area.changeunit);
		});

		$(function() {
			if(localStorage.getItem('ams.Config.general.area.changeunit')!==null){
				ams.Config.general.area.changeunit=localStorage.getItem('ams.Config.general.area.changeunit');
			}
			if(localStorage.getItem('ams.Config.general.area.threshold')!==null){
				ams.Config.general.area.threshold=localStorage.getItem('ams.Config.general.area.threshold');
			}
			$("#threshold").val(ams.Config.general.area.threshold);
			$("#changeunit")[0].checked=ams.Config.general.area.changeunit=="auto";
		});
	},// end of run method

	/**
	* Update the reference data layer by change CQL filter params
	*/
	_updateReferenceLayer: function() {
		let l=this._getLayerByName(this._referenceLayerName);
		if(l && this._map.hasLayer(l)) {
			let cql=ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, this._hasClassFilter);
			l._source.options["cql_filter"] = cql;
			l._source._overlay.setParams({
				"cql_filter": cql
			});	
			l.bringToBack();
		}
	},

	/**
	 * Update the Spatial Unit layer by change the viewsParams with the new selected class name.
	 * Must change the priority layer associated to Spatial Unit layer too.
	 * Some filters is applied only in priority layer, so use the parameter onlyPriority.
	 * @param {boolean} onlyPriority to control whether both layers are updated or just the priority layer. The default is false.
	 */
	_updateSpatialUnitLayer: function(onlyPriority) {
		this._map.closePopup();// any filter change forces the popup to close

		onlyPriority=(typeof onlyPriority=='undefined')?(false):(onlyPriority);
		let l=null;
		let mm=this._getMinMax(this._getLayerPrefix(), this._propertyName);
		if(!mm) return;// abort if no valid values

		if(!onlyPriority) {
			l=this._getLayerByName(this._getLayerPrefix());
			if(l && this._map.hasLayer(l)) {
				let suLayerStyle = new ams.SLDStyles.AreaStyle(this._getLayerPrefix(), this._propertyName, mm.suLayerMin, mm.suLayerMax);
				let wmsOptions = {
					"opacity": 0.8,
					"viewparams": this._suViewParams.toWmsFormat(),
					"sld_body": suLayerStyle.getSLD()
				};
				this._addWmsOptionsBase(wmsOptions);
				l._source._overlay.setParams(wmsOptions);
				Object.assign(l.options,wmsOptions);// to update layer options
				Object.assign(l._source.options,wmsOptions);// to update layer options
				l.bringToFront();
				this._legendControl.update(this._getLayerPrefix(), suLayerStyle);
			}
		}
		l=this._getLayerByName(this._getLayerPrefix()+'_prior');
    	if(l && this._map.hasLayer(l)) {
			let priorLayerStyle = new ams.SLDStyles.AreaStyle(this._getLayerPrefix(), this._propertyName, mm.suLayerMin, mm.suLayerMax, true, "#ff0000");
			let wmsOptions = {
				"viewparams": this._priorViewParams.toWmsFormat(),
				"sld_body": priorLayerStyle.getSLD()
			};
			this._addWmsOptionsBase(wmsOptions);
			l._source._overlay.setParams(wmsOptions);
			Object.assign(l.options,wmsOptions);// to update layer options
			Object.assign(l._source.options,wmsOptions);// to update layer options
			l.bringToFront();
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

	_addControlLayer: function(){
		if(ams.App._layerControl){
			ams.App._map.removeControl(ams.App._layerControl);
		}
		let bs={
			"OpenStreetMap": ams.App._baseLayers["osm"],
			"Em branco": ams.App._baseLayers["blank"]
		};
		let ol={};
		for (let ll in ams.App._addedLayers) {
			let lname=( (ll.includes('deter'))?("DETER"):( (ll.includes('fire'))?("Focos"):(false) ) );
			if(ams.App._map.hasLayer(ams.App._addedLayers[ll])){
				if(lname!=false) ol[lname]=ams.App._addedLayers[ll];
			}
		}
		if(ams.App._biomeLayer) {
			ol["Amazônia"]=ams.App._biomeLayer;
		}
		ams.App._layerControl=L.control.layers(bs,ol).addTo(ams.App._map);
	},

	/**
	 * Changes the reference layer on map.
	 * Both layerToDel and layerToAdd can be, deter or queimadas, see the names on Config.js
	 * @param {*} layerToDel the name of the reference layer to be removed
	 * @param {*} layerToAdd the name of the reference layer to be added
	 */
	_exchangeReferenceLayer: function(layerToDel, layerToAdd){
		ams.App._removeLayer(layerToDel);
		this._referenceLayerName=layerToAdd;
		let layer = this._getLayerByName(layerToAdd);
		if(layer) {
			let cql = this._appClassGroups.getCqlFilter(this._suViewParams, this._hasClassFilter);
			layer._source.options["cql_filter"] = cql;
			let cqlobj = {"cql_filter": cql};
			this._addWmsOptionsBase(cqlobj);
			layer._source._overlay.setParams(cqlobj);
			layer.addTo(this._map);
			layer.bringToBack();
		}
		this._addControlLayer();
	},

	/**
	 * Adding the spatial Unit layer into map using updated viewParams and selected filters
	 * @param {string} layerName the name for a layer that will be added on map.
	 * @param {*} propertyName column "area" or "counts"
	 */
	_addSpatialUnitLayer: function(layerName, propertyName){
		// verify if exists on layers list
		let l1 = this._getLayerByName(layerName);
		let l2 = this._getLayerByName(layerName+'_prior');
		// if exists on list, remove
		if(l1) delete this._addedLayers[layerName];
		if(l2) delete this._addedLayers[layerName+'_prior'];

		let mm=this._getMinMax(layerName, propertyName);
		if(!mm) return;// abort if no valid values

		//insert spatial unit layer
		let layer=this._createSULayer(layerName, propertyName, mm);
		layer.addTo(this._map);

		//insert spatial unit priority layer
		layer=this._createPriorSULayer(layerName, propertyName, mm);
		layer.addTo(this._map);
		layer.bringToFront();
	},

	_getWmsOptions: function(layerName, propertyName, minMax, viewParams, isPriority) {
		isPriority = ( (typeof isPriority=='undefined')?(false):(isPriority) );
		let s = ( (isPriority)?
		(new ams.SLDStyles.AreaStyle(layerName, propertyName, minMax.suLayerMin, minMax.suLayerMax, true, "#ff0000")):
		(new ams.SLDStyles.AreaStyle(layerName, propertyName, minMax.suLayerMin, minMax.suLayerMax)) );
		if(!isPriority) this._legendControl.init(layerName, s);
		let wmsOptions = {
			"viewparams": viewParams.toWmsFormat(),
			"sld_body": s.getSLD()
		};
		if(!isPriority) wmsOptions["opacity"]=0.8;
		else wmsOptions["identify"]=false;// set this to disable GetFeatureInfo
		this._addWmsOptionsBase(wmsOptions);
		return wmsOptions;
	},

	_createSULayer: function(layerName, propertyName, minMax) {
		let wop=this._getWmsOptions(layerName, propertyName, minMax, this._suViewParams);
		let sl = new ams.LeafletWms.Source(this._baseURL, wop, this._appClassGroups);
		layer = sl.getLayer(layerName);
		this._addedLayers[layerName]=layer;
		return layer;
	},

	_createPriorSULayer: function(layerName, propertyName, minMax) {
		let wop=this._getWmsOptions(layerName, propertyName, minMax, this._priorViewParams, true);
		let sl = new ams.LeafletWms.Source(this._baseURL, wop, this._appClassGroups);
		layer = sl.getLayer(layerName);
		this._addedLayers[layerName+'_prior']=layer;
		return layer;
	},

	_getLayerByName: function(layerName){
		return ( (typeof this._addedLayers[layerName]=='undefined')?(false):(this._addedLayers[layerName]) );
	},

	_getLayerPrefix: function(){
		return this._currentSULayerName + ( (this._currentClassify=="onPeriod")?("_view"):("_diff_view") );
	},

	_getMinMax: function(layerName, propertyName){
		let min=( (ams.App._diffOn)?(ams.App._wfs.getMin(layerName, propertyName, ams.App._suViewParams)):(0) );
		let max=ams.App._wfs.getMax(layerName, propertyName, ams.App._suViewParams);
		let mm={
			suLayerMin:min,
			suLayerMax:max
		};
		if(mm.suLayerMax == mm.suLayerMin) {
			$('.toast').toast('show');
			$('.toast-body').html("Não existem dados para o periodo selecionado.");
			this._resetMap();
			return false;
		}else if(ams.App._diffOn && mm.suLayerMin>=0) {
			$('.toast').toast('show');
			$('.toast-body').html("Não há redução de valores para o periodo selecionado.");
			this._resetMap();
			return false;
		}
		let l=ams.App._getLayerByName(ams.App._getLayerPrefix());
		if(l && !ams.App._map.hasLayer(l)){
			ams.App._addSpatialUnitLayer(ams.App._getLayerPrefix(),ams.App._propertyName);
		}
		return mm;
	},

	_resetMap: function() {
		let oLayerName=ams.App._getLayerPrefix();
		// remove the main spatial unit layer, and
		this._removeLayer(oLayerName);
		// each spatial unit layer has an priority layer to display the highlight border, should be remove too
		this._removeLayer(oLayerName+'_prior');
		ams.App._legendControl.disable();
	},

	/**
	 * Remove layers from the map and reinsert the same or another.
	 * When the same name is used, the expected behavior is that a difference in
	 * the final layer name is applied when the classification type changes. 
	 * Look for this changes on ams.App._addSpatialUnitLayer
	 * @param {*} lr the layer name to be removed
	 * @param {*} li the layer name to be inserted
	 */
	_exchangeSpatialUnitLayer: function(lr,li) {
		// remove the main spatial unit layer, and
		this._removeLayer(lr);
		// each spatial unit layer has an priority layer to display the highlight border, should be remove too
		this._removeLayer(lr+'_prior');
		ams.App._addSpatialUnitLayer(li, this._propertyName);
	},

	_removeLayer: function(layerName){
		let l=ams.App._getLayerByName(layerName);
		if(l && this._map.hasLayer(l)){
			// remove all sublayers for a layer
			this._removeSubLayer(l);
		}
		this._map.closePopup();
	},

	_removeSubLayer: function(l){
		let ll=[];
		ll.push(l._leaflet_id);
		ll.push(l._source._leaflet_id);
		ll.push(l._source._overlay._leaflet_id);
		while(ll.length){
			let lid=ll.pop();
			let lm=this._map._layers[lid];
			if(lm){
				if(typeof lm.onRemove=='undefined') delete this._map._layers[lid];
				else if(this._map.hasLayer(lm)) this._map.removeLayer(lm);
			}
		}
	},	

	_onWindowResize: function () {
		ams.groupControl._onWindowResize();
	},

	displayGraph: function( jsConfig ) {
		async function getGraphics(  jsConfig ) {
			jsConfig["unit"]=ams.Map.PopupControl._unit;
			let jsConfigStr = JSON.stringify(jsConfig);
			let response = await fetch("callback/spatial_unit_profile?sData=" + jsConfigStr);
			$("#loading_data_info").css('display','none')
			if (response.ok) {
				let profileJson = await response.json();
				if (response.ok) {
					document.getElementById("txt3a").innerHTML = profileJson['FormTitle'];
					Plotly.react('AreaPerYearTableClass', JSON.parse(profileJson['AreaPerYearTableClass']), {});
					Plotly.react('AreaPerLandUse', JSON.parse(profileJson['AreaPerLandUse']), {});
					$('#modal-container-general-info').modal();
					// for adding tooltip on pie chart legend
					let leg=$('g.legend');
					leg.attr('data-html','true');
					leg.attr('title', 'Descrição das categorias fundiárias.<br />'+
					'-----------------------------------------------------------------------<br />'+
					'TI: Terras Indígenas;<br />'+
					'UC: Unidades de Conservação;<br />'+
					'Assentamentos: Projetos de assentamentos de todos os tipos;<br />'+
					'APA: Área de Proteção Ambiental;<br />'+
					'CAR: Cadastro Ambiental Rural;<br />'+
					'FPND: Florestas Públicas Não Destinadas;<br />'+
					'Indefinida: Todas as demais áreas');
					leg.mouseover(function(){
						let l=$('g.legend');
						l.tooltip('show');
					});
				} else {
					console.log("HTTP-Error: " + response.status + " on spatial_unit_profile");
					$('.toast').toast('show');
					$('.toast-body').html("Encontrou um erro na solicitação ao servidor.");
				}
			} else {
				console.log("HTTP-Error: " + response.status + " on spatial_unit_profile");
				$('.toast').toast('show');
				$('.toast-body').html("Encontrou um erro na solicitação ao servidor.");
			}
		}
		if (jsConfig.className != 'null'){
			$("#loading_data_info").css('display','block');
			getGraphics(jsConfig);
		}
	}
};
