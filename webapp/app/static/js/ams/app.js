var ams = ams || {};

ams.App = {

    zoomThreshold: 11, // used to change the zIndex of the DETER layer in the map layer stack.
    _layerControl: null,
    _baseLayers: [],
    _addedLayers: [],
    _borderLayer: null,
    _appClassGroups: null,
    _suViewParams: null,
    _priorViewParams: null,
    _wfs: null,
    _dateControl: null,
    _baseURL: null,
    _indicator: null,
    _propertyName: null,
    _riskThreshold: 0.0,
    _referenceLayerName: null,
    _currentSULayerName: null,
    _hasClassFilter: false,// if reference layer is DETER, so, has class filter.
    _diffOn: false,
    _currentTemporalAggregate: null,
    _currentClassify: null,
    _spatialUnits: null,
    _landUseList: [],
    _biomes: [],
    _subset: null,
    _municipalitiesGroup: null,
    _geocodes: null,

    run: function(geoserverUrl, spatialUnits, appClassGroups) {

        this._spatialUnits=spatialUnits;
        this._appClassGroups=appClassGroups;
        // start land use list with default itens to use in viewparams at start App
        this._landUseList=ams.Config.landUses.map((lu)=>{return(lu.id);});

        this._biomes=ams.Config.appSelectedBiomes;
        this._subset=ams.Config.appSelectedSubset;
        this._municipalitiesGroup=ams.Config.appSelectedMunicipalitiesGroup;
        this._geocodes=ams.Config.appSelectedGeocodes;

    	// REMOVE ME (Debug Purposes)
        // if(ams.Auth.isAuthenticated()==false) {
        // geoserverUrl = "http://127.0.0.1/geoserver";
        // }

        this._wfs = new ams.Map.WFS(geoserverUrl);
        var ldLayerName = ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.lastDate;
        var temporalUnits = new ams.Map.TemporalUnits();
        this._dateControl = new ams.Date.DateController();
        let lastDateDynamic = this._wfs.getLastDate(ldLayerName);
        lastDateDynamic = lastDateDynamic?lastDateDynamic:this._spatialUnits.getDefault().last_date;
        ams.PeriodHandler.setMaxDate(lastDateDynamic);

        let startDate = ams.Config.startDate;
        let tempUnit = ams.Config.tempUnit;
        this._currentTemporalAggregate = temporalUnits.getAggregates()[0].key;

        if (startDate && ams.Date.isAfter(lastDateDynamic, startDate) && tempUnit !== "custom") {
            ams.App._dateControl.setPeriod(startDate, tempUnit);
            this._currentTemporalAggregate = tempUnit;
        } else {            
            ams.App._dateControl.setPeriod(lastDateDynamic, this._currentTemporalAggregate);
        }

        this._baseURL = geoserverUrl + "/wms";
        
        this._setIndicator(ams.Config.defaultFilters.indicator);

        var map = new L.Map("map", {
            zoomControl: false,
            minZoom: 4
        });
        this._map=map;

        // improve control positions for Leaflet
        ams.LeafletControlPosition.addNewPositions(map);

        // bounding
        map.fitBounds(
            [[ams.Config.bbox[2], ams.Config.bbox[0]], [ams.Config.bbox[3], ams.Config.bbox[1]]],
            {
                padding: [
                    (this._geocodes.length == 1 && this._geocodes[0].length > 0) * 100,
                    (this._geocodes.length == 1 && this._geocodes[0].length > 0) * 100
                ]
            }
        );

        // crs: L.CRS.EPSG4326,
        this._baseLayers["osm"] = new L.TileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
            maxZoom: 18,
            minZoom: 4
        }).addTo(map);

        // google maps
        let options = {
            attribution: '&copy; <a href="https://www.google.com/maps/">Google Maps</a>',
            maxZoom: 18,
            minZoom: 4,
            subdomains: ['mt0','mt1','mt2','mt3']
        };
        let googlelayers=[
            {"index":"gs","name":"Google Satellite","param":"s"},
            {"index":"gh","name":"Google Hybrid","param":"s,h"},
            {"index":"gst","name":"Google Streets","param":"m"},
            {"index":"gte","name":"Google Terrain","param":"p"}
        ];
        for(let i in googlelayers){
            let host = "https://{s}.google.com/vt/lyrs="+googlelayers[i].param+"&x={x}&y={y}&z={z}";
            options["name"]=googlelayers[i].name;
            this._baseLayers[googlelayers[i].index] = new L.TileLayer(host, options);
        }

        this._baseLayers["blank"] = new L.TileLayer("");

        L.control.zoom({position: 'topright'}).addTo(map);
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
        var tbDeterAlertsLayerName = ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.deter;
        var tbDeterAlertsWmsOptions = {
            "cql_filter": appClassGroups.getCqlFilter(this._suViewParams, true),
            "viewparams": (
                "landuse:" + ams.App._landUseList.join('\\,') + ";" +
                "biomes:" + ams.App._biomes.join('\\,') + ";" +
                "municipality_group_name:" + ams.App._municipalitiesGroup + ";" +
                "geocodes:" + ams.App._geocodes.join('\\,')
            )
        };
        ams.App._addWmsOptionsBase(tbDeterAlertsWmsOptions);

        var AFLayerName = ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.activeFire;
        var AFWmsOptions = {
            "cql_filter": appClassGroups.getCqlFilter(this._suViewParams, false),
            "viewparams": (
                "landuse:" + ams.App._landUseList.join('\\,')  + ";" +
                "biomes:" + ams.App._biomes.join('\\,') + ";" +
                "municipality_group_name:" + ams.App._municipalitiesGroup + ";" +
                "geocodes:" + ams.App._geocodes.join('\\,')
            )
        };
        ams.App._addWmsOptionsBase(AFWmsOptions);

        var riskLayer = ams.Config.defaultRiskFilter.source === "inpe"? ams.Config.defaultLayers.inpeRisk : ams.Config.defaultLayers.ibamaRisk;
        var RKLayerName = ams.Auth.getWorkspace() + ":" + riskLayer;
        var RKWmsOptions = {
            "cql_filter": "(risk >= " + ams.Config.defaultRiskFilter.threshold + ")",
            "viewparams": (
                "landuse:" + ams.App._landUseList.join('\\,') +  ";" +
                "biomes:" + ams.App._biomes.join('\\,') + ";" +
                "municipality_group_name:" + ams.App._municipalitiesGroup + ";" +
                "geocodes:" + ams.App._geocodes.join('\\,')
            )
        };
        ams.App._addWmsOptionsBase(RKWmsOptions);

        var tbDeterAlertsSource = new ams.LeafletWms.Source(this._baseURL, tbDeterAlertsWmsOptions, appClassGroups);
        var AFSource = new ams.LeafletWms.Source(this._baseURL, AFWmsOptions, appClassGroups);
        var RKSource = new ams.LeafletWms.Source(this._baseURL, RKWmsOptions, appClassGroups);
        var tbDeterAlertsLayer = tbDeterAlertsSource.getLayer(tbDeterAlertsLayerName);
        let AFLayer = AFSource.getLayer(AFLayerName);
        let RKLayer = RKSource.getLayer(RKLayerName);
        if(this._referenceLayerName==tbDeterAlertsLayerName) {
            tbDeterAlertsLayer.addTo(map);
            tbDeterAlertsLayer.bringToBack();
        }else if(this._referenceLayerName==AFLayerName){
            AFLayer.addTo(map);
            AFLayer.bringToBack();
        }else if(this._referenceLayerName==RKLayerName){
            RKLayer.addTo(map);
            RKLayer.bringToBack();
        } else {
            ams.Utils.assert(false, "invalid layer name");
        }
        // Store layers to handler after controls change
        this._addedLayers[tbDeterAlertsLayerName]=tbDeterAlertsLayer;
        this._addedLayers[AFLayerName]=AFLayer;
        this._addedLayers[RKLayerName]=RKLayer;

        // Start the legend control
        this._legendControl = new ams.Map.LegendController(map, this._baseURL);

        // Default Spatial Unit layer
        this._currentSULayerName = ams.Auth.getWorkspace() + ":" + this._spatialUnits.getDefault().dataname;
        ams.Config.defaultFilters.spatialUnit=this._spatialUnits.getDefault().dataname;// update the default for later use in filter change in control.
        this._addSpatialUnitLayer(this._getLayerPrefix(),this._propertyName);

        var tbBorderLayerName = ams.Auth.getWorkspace() + ":" + ((this._subset == "Bioma") ? ams.Config.defaultLayers.biomeBorder : ams.Config.defaultLayers.municipalitiesBorder);
        var onlyWmsBase = {
            identify: false,
            "viewparams": (
                "biomes:" + ams.App._biomes.join('\\,') + ";" +
                "municipality_group_name:" + ams.App._municipalitiesGroup + ";" +
                "geocodes:" + ams.App._geocodes.join('\\,')
            )
        }; // set this to disable GetFeatureInfo
        ams.App._addWmsOptionsBase(onlyWmsBase);
        
        var tbBorderSource = new ams.LeafletWms.Source(this._baseURL, onlyWmsBase, this._appClassGroups);
        ams.App._borderLayer = tbBorderSource.getLayer(tbBorderLayerName);
        ams.App._borderLayer.addTo(map).bringToBack();

        // ---------------------------------------------------------------------------------
        // this structure is used into leaflet.groupedlayercontrol.js to create controls for filters panel...
        var controlGroups = {
            "RECORTE BIOMA": {
                type: "selectControl",
                defaultFilter: ams.Config.appSelectedBiomes[0],
                defaultSubset: ams.Config.appSelectedSubset,
                group: "RECORTE",
                name: "Bioma",
                values: ams.Config.allBiomes,
            },
            "RECORTE MUNICIPIOS": {
                type: "selectControl",
                defaultFilter: ams.Config.appSelectedMunicipalitiesGroup,
                defaultSubset: ams.Config.appSelectedSubset,
                group: "RECORTE",
                name: "Municípios de Interesse",
                values: ams.Config.allMunicipalitiesGroup,
            },
            "INDICADOR": {
                defaultFilter:ams.Config.defaultFilters.indicator,
                propertyName:this._propertyName,
                type: "simpleControl"
            },
            "CATEGORIA FUNDIÁRIA":{
                defaultFilter: '',
                type: "simpleControl"
            },
            "UNIDADE ESPACIAL": {
                defaultFilter: ams.Config.defaultFilters.spatialUnit,
                type: "simpleControl"
            },
            "UNIDADE TEMPORAL": {
                defaultFilter:ams.Config.defaultFilters.temporalUnit,
                type: "simpleControl"
            },
            "CLASSIFICAÇÃO DO MAPA": {
                defaultFilter:ams.Config.defaultFilters.diffClassify,
                type: "simpleControl"
            },
        };

        for (let p in ams.Config.landUses) {
            if(ams.Config.landUses.hasOwnProperty(p)&&ams.Config.landUses[p]){
                controlGroups["CATEGORIA FUNDIÁRIA"]["defaultFilter"]+=((controlGroups["CATEGORIA FUNDIÁRIA"]["defaultFilter"]=='')?(''):(','))+ams.Config.landUses[p].id;
                controlGroups["CATEGORIA FUNDIÁRIA"][ams.Config.landUses[p].name] = ''+ams.Config.landUses[p].id;
            }
        }

        let sulen = this._spatialUnits.length();
        for(var i = 0; i < sulen; i++) {
            let layerName = ams.Auth.getWorkspace() + ":" + this._spatialUnits.at(i).dataname;
            controlGroups["UNIDADE ESPACIAL"][this._spatialUnits.at(i).description] = layerName;
        }

        let cglen = appClassGroups.length();
        for(var i = 0; i < cglen; i++) {
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

        var groupControl = L.control.groupedLayers(
            controlGroups, {
                exclusiveGroups: [
                    "UNIDADE ESPACIAL", 
                    "INDICADOR", 
                    "UNIDADE TEMPORAL", 
                    "CLASSIFICAÇÃO DO MAPA",
                ],
                collapsed: false,
                position: "topleft",
            }
        ).addTo(map);

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

        // Enable/disable risk
        ams.Utils.handleRiskIndicator();

        // Adding period control over map
        ams.PeriodHandler.init(map);

        // Adding control layer over map
        this._addControlLayer();

        // control handler of main panel
        map.on('changectrl', function(evn) {
            
            $("#loading_data_info").css('display','block');

            let changeCtrlFun=function(e){

                if(ams.App._landUseList.length==0 &&
                    e.group.name!='CATEGORIA FUNDIÁRIA' && e.group.name!='BIOMA'){
                    ams.App._resetMap("O filtro deve incluir ao menos uma categoria fundiária. A solicitação não foi concluída.");
                    return;// abort if no filters
                }

                let layerToAdd,needUpdateSuLayers=true;

                var startDate = ams.App._dateControl.startdate;
                var endDate = ams.App._dateControl.enddate;
                var tempUnit = ams.App._dateControl.period;
               
                if(e.group.name=='BIOMA'){
                    if(e.acronym==ams.Config.biome && e.subsetChanged===false){
                        return;
                    }
                    if(ams.App._landUseList.length!=ams.Config.landUses.length){
                        $('.toast').toast('show');
                        $('.toast-body').html("O filtro por categorias fundiárias foi restaurado ao padrão.");
                        // to avoid the toast msg at _updateSpatialUnitLayer
                        ams.App._landUseList=ams.Config.landUses.map((lu)=>{return(lu.id);});
                    }
                    // reset some data to avoid getting wrong data
                    ams.App._suViewParams=null;
                    ams.App._priorViewParams=null;
                    ams.App._diffOn = ( (ams.Config.defaultFilters.diffClassify=="onPeriod")?(false):(true) );
                    // write on local storage

                    localStorage.setItem('ams.previous.biome.setting.selection', e.acronym);

                    needUpdateSuLayers=false;// disable the call at the end because the call is inside the Promise callback below
                    ams.Utils.updateMap(e.acronym, e.subset, undefined, undefined, startDate, endDate, tempUnit).then(
                        ()=>{
                            ams.App._updateSpatialUnitLayer();
                        }
                    );

                } else if(e.group.name =='MUNIC\xcdPIOS DE INTERESSE'){
                    if(ams.App._landUseList.length!=ams.Config.landUses.length){
                        $('.toast').toast('show');
                        $('.toast-body').html("O filtro por categorias fundiárias foi restaurado ao padrão.");
                        // to avoid the toast msg at _updateSpatialUnitLayer
                        ams.App._landUseList=ams.Config.landUses.map((lu)=>{return(lu.id);});
                    }
                    // reset some data to avoid getting wrong data
                    ams.App._suViewParams=null;
                    ams.App._priorViewParams=null;
                    ams.App._diffOn = ( (ams.Config.defaultFilters.diffClassify=="onPeriod")?(false):(true) );

                    var geocodes = "";
                    if (e.name == "customizado") {
                        geocodes = e.customized.join(',');
                    }

                    // disable the call at the end because the call is inside the Promise callback below
                    needUpdateSuLayers=false;
                    ams.Utils.updateMap("all", e.subset, e.name, geocodes, startDate, endDate, tempUnit).then(
                        ()=>{
                            ams.App._updateSpatialUnitLayer();
                        }
                    );

                } else if(e.group.name=='INDICADOR'){// change reference layer (deter, fires or risk)?
                    ams.App._riskThreshold=0.0; // reset the risk limit so as not to interfere with the min max query
                    ams.App._indicator = e.acronym;
                    if(e.acronym=='RK'){
                        layerToAdd=ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.ibamaRisk;
                        ams.App._propertyName=ams.Config.propertyName.rk;
                        ams.App._riskThreshold=ams.Config.defaultRiskFilter.threshold;
                        ams.App._hasClassFilter=false;
                    }else if(e.acronym=='RI'){
                        layerToAdd=ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.inpeRisk;
                        ams.App._propertyName=ams.Config.propertyName.ri;
                        ams.App._riskThreshold=ams.Config.defaultRiskFilter.threshold;
                        ams.App._hasClassFilter = false;
                    }else if(e.acronym=='AF'){
                        // the reference layer should be active-fires
                        layerToAdd=ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.activeFire;
                        ams.App._propertyName=ams.Config.propertyName.af;
                        ams.App._hasClassFilter=false;
                    }else{
                        // the reference layer should be deter
                        layerToAdd=ams.Auth.getWorkspace()+":"+ams.Config.defaultLayers.deter;
                        ams.App._propertyName=ams.Config.propertyName.deter;
                        ams.App._hasClassFilter=true;
                    }

                    // reference layer was changes, so propertyName changes too
                    if(ams.App._referenceLayerName!=layerToAdd){
                        ams.App._exchangeReferenceLayer(ams.App._referenceLayerName, layerToAdd);
                    }else if(ams.App._hasClassFilter){
                        // apply change filters on reference layer
                        ams.App._updateReferenceLayer();
                    }

                    if(ams.App._suViewParams.classname != e.acronym){
                        var keep_last_date = (
                            !["RI", "RK", "AF"].includes(e.acronym) && !["RI", "RK", "AF"].includes(ams.App._suViewParams.classname)
                        );

                        ams.App._suViewParams.classname = e.acronym;
                        ams.App._priorViewParams.classname = e.acronym;
                        ams.App._suViewParams.updatePropertyName(ams.App._propertyName);
                        ams.App._priorViewParams.updatePropertyName(ams.App._propertyName);
                        ams.App._suViewParams.updateRiskThreshold(ams.App._riskThreshold);
                        ams.App._priorViewParams.updateRiskThreshold(ams.App._riskThreshold);
                        // try update the last date for new classname
                        let lastDateDynamic = ams.App._wfs.getLastDate(ldLayerName);
                        lastDateDynamic = lastDateDynamic? lastDateDynamic : ams.App._spatialUnits.getDefault().last_date;
                        ams.PeriodHandler.setMaxDate(lastDateDynamic);

                        if (keep_last_date) {
                            lastDateDynamic = ams.Date.getMin(ams.App._dateControl.startdate, lastDateDynamic);
                        }

                        ams.App._dateControl.setPeriod(lastDateDynamic, ams.App._currentTemporalAggregate);
                        ams.PeriodHandler.changeDate(ams.App._dateControl.startdate);
                        needUpdateSuLayers=false; //no need because the changeDate Internally invokes layer update
                    }
                }else if(e.group.name=='CATEGORIA FUNDIÁRIA'){
                    let luid=+e.acronym;
                    if(e.inputtype=='checkbox'){
                        let index=ams.App._landUseList.findIndex((v)=>{
                            return v==luid;
                        });
                        if(e.checked && index<0){
                            ams.App._landUseList.push(luid);
                            ams.App._resetMap();
                        }
                        if(!e.checked && index>=0){
                            ams.App._landUseList.splice(index,1);
                            ams.App._resetMap();
                        }
                    }

                    needUpdateSuLayers=false;
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
                    ams.PeriodHandler.changeDate(ams.App._dateControl.startdate);
                    needUpdateSuLayers=false;// no need because the changeDate Internally invokes layer update.
                }

                if(needUpdateSuLayers) ams.App._updateSpatialUnitLayer();

                window.setTimeout(()=>{$("#loading_data_info").css('display','none');},500);
            };

            window.setTimeout(()=>{changeCtrlFun(evn);},100);
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

        // municipality panel
        function setMunicipalityPanelMode() {
            $(".hide-in-municipality-panel").css("display", "none")
            $("#header-panel-title").text("Sala de Situação Municipal | " + ams.Config.appSelectedMunicipality);

            let param = window.location.pathname.includes("panel")? "?geocode=" : "/panel?geocode=";
            const url = window.location.pathname.replace(/\/$/, '') + param + ams.Config.appSelectedGeocodes[0];
            window.history.pushState({}, '', url);
        }
        if (ams.Config.appMunicipalityPanelMode) {
            setMunicipalityPanelMode();
        }

        if (ams.Config.defaultFilters.indicator == 'RI') {
            let obj = ams.groupControl._getControlByName("RI");
            $("#ctrl" + obj.ctrlId).click();  // forcing to start risk environment
        }

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

        // error message
        function showErrorMsg(msg) {
	    $('.toast').toast({delay: 7000});
	    $('.toast-body').html(msg);
            $('.toast').toast('show');
        }
        if ($('meta[name="error-msg"]').length) {
            showErrorMsg($('meta[name="error-msg"]').attr('content'));
            $('meta[name="error-msg"]').remove();
        }
        
        let profileClick=function() {
            let conf={};

            conf["className"]=ams.App._suViewParams.classname;
            conf["spatialUnit"]=ams.Config.biome;
            conf["startDate"]=ams.App._dateControl.startdate;
            conf["tempUnit"]=ams.App._currentTemporalAggregate;

            if (conf["tempUnit"] === "custom") {
                conf["tempUnit"] = ams.App._dateControl.customDays + "d";
                conf["custom"] = true;
            }
            
            conf["suName"]=ams.Config.biome;
            conf["landUse"]=ams.App._landUseList.join(',');

            ams.App.displayGraph(conf);

            return false;
        };

        $("#profile-button").click(profileClick);

        let landUseFilterClick=function(evn) {
            $("#loading_data_info").css('display','block');

            let clickCtrlFun=function(e){
                if(ams.App._landUseList.length==0){
                    ams.App._resetMap("O filtro deve incluir ao menos uma categoria fundiária. A solicitação não foi concluída.");
                }else{
                    ams.App._updateSpatialUnitLayer();
                    // apply change filters on reference layer
                    ams.App._updateReferenceLayer();
                }
                window.setTimeout(()=>{$("#loading_data_info").css('display','none');},500);
            };
            window.setTimeout(()=>{clickCtrlFun(evn);},100);
            return false;
        };

        $("#landuse-categories-button").click(landUseFilterClick);

        let landUseSwapSelectionClick=function() {
            let ckbs=$('#ckb-itens');
            if(ckbs[0]){
                let itens=ckbs[0].getElementsByTagName('input');
                if(itens.length){
                    for (let i = 0; i < itens.length; i++) {
                        const iten = itens[i];
                        iten.checked=( (ams.App._landUseList.length)?(false):(true) );
                    }
                    ams.App._landUseList=( (ams.App._landUseList.length)?([]):(ams.Config.landUses.map((lu)=>{return(lu.id);})) );
                }
            }
            ams.App._resetMap();
            return false;
        };

        $("#all-categories-button").click(landUseSwapSelectionClick);

        let landUseUpDownClick=function(elem) {
            if(elem.target.innerText=='arrow_drop_down'){
                elem.target.innerText = 'arrow_drop_up';
                $("#landuse-itens")[0].style="display:flex;";
            }else{
                elem.target.innerText = 'arrow_drop_down';
                $("#landuse-itens")[0].style="display:none;";
            }
            
            return false;
        };

        $(".iconlanduse-updown").click(landUseUpDownClick);

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
            localStorage.setItem('ams.config.general.area.threshold', v);
        });

        $("#changeunit").on("change", ()=>{
            let v=$("#changeunit")[0].checked;
            if(v) ams.Config.general.area.changeunit="auto";
            else ams.Config.general.area.changeunit="no";
            localStorage.setItem('ams.config.general.area.changeunit', ams.Config.general.area.changeunit);
        });

        $("#modal-credits-check").click(
            function() {
                if ($("#modal-credits-check").prop('checked')) {
                    localStorage.setItem("ams.config.modal.noshowcredits", true);
                } else {
                    localStorage.removeItem("ams.config.modal.noshowcredits");
                }
                return true;
            }
        );

        $("#show-modal-credits").click(
            function() {
                $("#modal-container-credits").modal();
            }
        );

        $('#search-municipalities').on('input', function() {
            const query = $(this).val().toLowerCase();
            const $options = $('#select-municipalities option');

            if (query.length < 2) {
                $options.each(function () {
                    $(this).prop('disabled', false).show();
                });
            }

            $options.each(function () {
                const $opt = $(this);
                const match = $opt.text().toLowerCase().includes(query);

                if (match) {
                    $opt.prop('disabled', false).show();
                } else {
                    $opt.prop({disabled: true}).hide();
                }
            });
        });

        $('#select-municipalities').on('change', function() {
            const $select = $(this);
            const selected = $select.find('option:selected');
            const count = selected.length;
            const maxMunicipalities = 50;

            $('#municipalities-search-ok').prop('disabled', count==0);
            $('#municipalities-search-panel').prop('disabled', count!=1);
            
            $('#select-municipalities-msg').text(count > 1? `${count} municípios.` : '');
            if (count > maxMunicipalities) {
                $('#select-municipalities-msg').text(`Você só pode selecionar até ${maxMunicipalities} municípios.`)
                while($select.find('option:selected').length > maxMunicipalities) {
                    const lastSelected = $select.find('option:selected').last();
                    lastSelected.prop('selected', false);
                }
            }
        });

        $(function() {
            if(localStorage.getItem('ams.config.general.area.changeunit')!==null){
                ams.Config.general.area.changeunit=localStorage.getItem('ams.config.general.area.changeunit');
            }
            if(localStorage.getItem('ams.config.general.area.threshold')!==null){
                ams.Config.general.area.threshold=localStorage.getItem('ams.config.general.area.threshold');
            }
            $("#threshold").val(ams.Config.general.area.threshold);
            $("#changeunit")[0].checked=ams.Config.general.area.changeunit=="auto";

            if (localStorage.getItem('ams.config.modal.noshowcredits') == null) {
                $("#modal-container-credits").modal();
            }

            ams.App._populateMunicipalities();
        });

    }, // end of run method

    _setIndicator: function (indicator) {
        console.log("setting indicator " + indicator);

        ams.App._indicator = indicator;

        if (indicator == 'AF') {
            ams.App._propertyName =  ams.Config.propertyName.af;
            ams.App._referenceLayerName = ams.Auth.getWorkspace() + ":" + ams.Config.defaultLayers.activeFire;
            ams.App._hasClassFilter=false;

        } else if (indicator == 'RK') {
            ams.App._propertyName = ams.Config.propertyName.rk;
            ams.App._referenceLayerName = ams.Auth.getWorkspace() + ":" + ams.Config.defaultLayers.ibamaRisk;
            ams.App._hasClassFilter=false;
            ams.App._diffOn = false;

        } else if (indicator == 'RI') {
            ams.App._propertyName = ams.Config.propertyName.ri;
            ams.App._referenceLayerName = ams.Auth.getWorkspace() + ":" + ams.Config.defaultLayers.inpeRisk;
            ams.App._hasClassFilter=false;
            ams.App._diffOn = false;

        } else {
            ams.App._propertyName = ams.Config.propertyName.deter;
            ams.App._referenceLayerName = ams.Auth.getWorkspace() + ":" + ams.Config.defaultLayers.deter;                
            ams.App._hasClassFilter=true;
        }
        
        ams.App._currentClassify = ams.Config.defaultFilters.diffClassify;
    },

    _populateMunicipalities: function() {
        const $selectMunicipalities = $('#select-municipalities');
    
        $selectMunicipalities.empty();

        $.each(ams.Config.appAllMunicipalities, function(index, municipality) {
            const option = $('<option></option>')
                .val(municipality.geocode)
                .text(municipality.name);
            $selectMunicipalities.append(option);
        });
    },

    _getCustomizedMunicipalities: function() {
        const modal = $("#modal-container-municipalities");

        function _closeCustomizedMunicipalities() {
            modal.modal('hide');
            $('#search-municipalities').val("");
            $('#select-municipalities option').show();
            $('#select-municipalities option').prop('selected', false);     
            $('#municipalities-search-ok').prop('disabled', true);
            $('#municipalities-search-panel').prop('disabled', true);
            $('#select-municipalities-msg').text('');
        }

        return new Promise((resolve) => {
            modal.modal('show');

            $('#municipalities-search-ok').off('click').on('click', function() {
                const geocodes = $('#select-municipalities option:selected').map(function() {
                    return $(this).val();
                }).get();
                _closeCustomizedMunicipalities();            
                resolve(geocodes);
            });

            $('#municipalities-search-panel').off('click').on('click', function() {
                const geocodes = $('#select-municipalities option:selected').map(function() {
                    return $(this).val();
                }).get();
                _closeCustomizedMunicipalities();
                resolve([]);                
                ams.App.startMunicipalityPanel("geocode", geocodes[0]);
            });

            $('#municipalities-search-cancel').off('click').on('click', function() {
                _closeCustomizedMunicipalities();
                resolve([]);
            });
            
            $('#municipalities-search-close').off('click').on('click', function() {
                _closeCustomizedMunicipalities();
                resolve([]);
            });

        });
    },

    /**
    * Update the reference data layer by change CQL filter params
    */
    _updateReferenceLayer: function() {
        let l=this._getLayerByName(this._referenceLayerName);
        if(l) {
            let cqlobj = {};
            if(!this._referenceLayerName.includes(ams.Config.defaultLayers.ibamaRisk) &&
               !this._referenceLayerName.includes(ams.Config.defaultLayers.inpeRisk)) {
                let cql = ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, this._hasClassFilter);
                l._source.options["cql_filter"] = cql;
                cqlobj = {"cql_filter": cql};
            }
            cqlobj["viewparams"] = (
                "landuse:" + ams.App._landUseList.join('\\,') + ";" +
                "biomes:" + ams.App._biomes.join('\\,') + ";" +
                "municipality_group_name:" + ams.App._municipalitiesGroup + ";" +
                "geocodes:" + ams.App._geocodes.join('\\,')
            );
            this._addWmsOptionsBase(cqlobj);

            l._source._overlay.setParams(cqlobj);
            if(!this._map.hasLayer(l)) l.addTo(this._map);
            l.bringToBack();
        }
        $("#dataname-to-download").text(ams.App._appClassGroups.getGroupName(ams.App._suViewParams.classname));
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

    _addWmsOptionsBase: function(options) {
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
            "Google Satélite": ams.App._baseLayers["gs"],
            "Google Híbrido": ams.App._baseLayers["gh"],
            "Google Ruas": ams.App._baseLayers["gst"],
            "Google Terreno": ams.App._baseLayers["gte"],
            "Em branco": ams.App._baseLayers["blank"]
        };
        let ol={};
        for (let ll in ams.App._addedLayers) {
            let lname=( (ll.includes('deter'))?("DETER"):( (ll.includes('fire'))?("Focos"):( (ll.includes('ibama'))?("Risco (IBAMA)"):( (ll.includes('inpe'))?("Risco (INPE)"):(false) ) ) ) );
            if(ams.App._map.hasLayer(ams.App._addedLayers[ll])){
                if(lname!==false) ol[lname]=ams.App._addedLayers[ll];
            }
        }
        if(ams.App._borderLayer) {
            ol[ams.Config.biome]=ams.App._borderLayer;
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
        let cqlobj={};
        if(layer) {
            if(!layerToAdd.includes(ams.Config.defaultLayers.ibamaRisk) &&
               !layerToAdd.includes(ams.Config.defaultLayers.inpeRisk)) {
                let cql = this._appClassGroups.getCqlFilter(this._suViewParams, this._hasClassFilter);
                layer._source.options["cql_filter"] = cql;
                cqlobj = {"cql_filter": cql,"viewparams": "landuse:" + ams.App._landUseList.join('\\,')};
                this._addWmsOptionsBase(cqlobj);
            }
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
    
    hasSpatialUnitLayer: function () {
        return this._addedLayers.hasOwnProperty(ams.App._getLayerPrefix());
    },

    addSpatialUnitLayer: function() {
        this._addSpatialUnitLayer(this._getLayerPrefix(),this._propertyName);
    },

    _getMinMax: function(layerName, propertyName){
        let min=( (ams.App._diffOn)?(ams.App._wfs.getMin(layerName, propertyName, ams.App._suViewParams)):(0) );
        let max=ams.App._wfs.getMax(layerName, propertyName, ams.App._suViewParams);
        let mm={
            suLayerMin:min,
            suLayerMax:max
        };
        if(mm.suLayerMax == mm.suLayerMin) {
            let landUse="";
            if(ams.App._landUseList.length==0)
                landUse="<br /><br /><b>Atenção</b>: Deve selecionar ao menos um item no filtro por categorias fundiárias.";
            let msg = ams.App._indicator.includes('RI')? "Não existem dados de risco." : "Não existem dados para o período selecionado."+landUse;
            this._resetMap(msg);
            return false;
        }else if(ams.App._diffOn && mm.suLayerMin>=0) {
            this._resetMap("Não há redução de valores para o período selecionado.");
            return false;
        }
        let l=ams.App._getLayerByName(ams.App._getLayerPrefix());
        if(l && !ams.App._map.hasLayer(l)) {
            ams.App._addSpatialUnitLayer(ams.App._getLayerPrefix(),ams.App._propertyName);
        }

        return mm;
    },

    _resetMap: function(toast_msg) {
        if(typeof toast_msg!=='undefined'){
            $('.toast').toast('show');
            $('.toast-body').html(toast_msg);
        }
        let oLayerName=ams.App._getLayerPrefix();
        // remove the main spatial unit layer, and
        this._removeLayer(oLayerName);
        // each spatial unit layer has an priority layer to display the highlight border, should be remove too
        this._removeLayer(oLayerName+'_prior');
        ams.App._legendControl.disable();
        // remove reference layer
        ams.App._removeLayer(ams.App._referenceLayerName);
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
            jsConfig["targetbiome"]=ams.Config.biome;
            jsConfig["riskThreshold"]=ams.App._suViewParams.risk_threshold;
            jsConfig["municipalitiesGroup"]=ams.App._municipalitiesGroup;
            jsConfig["geocodes"]=ams.App._geocodes.join(',');

            let jsConfigStr = JSON.stringify(jsConfig);
            let response = await fetch("callback/spatial_unit_profile?sData=" + jsConfigStr).catch(
                ()=>{
                    console.log("The backend service may be offline or your internet connection has been interrupted.");
                }
            );
            $("#loading_data_info").css('display','none');
            if (response&&response.ok) {
                let profileJson = await response.json();

                Plotly.purge('AreaPerYearTableClass');
                if (profileJson['AreaPerYearTableClass']) {
                    Plotly.react('AreaPerYearTableClass', JSON.parse(profileJson['AreaPerYearTableClass']), {});
                }
                Plotly.purge('AreaPerLandUse');
                if (profileJson['AreaPerLandUse'] && ams.App._landUseList.length>1) {
                    Plotly.react('AreaPerLandUse', JSON.parse(profileJson['AreaPerLandUse']), {});
                }
                Plotly.purge('AreaPerLandUsePpcdam');
                if (profileJson['AreaPerLandUsePpcdam'] && ams.App._landUseList.length>1) {
                    Plotly.react('AreaPerLandUsePpcdam', JSON.parse(profileJson['AreaPerLandUsePpcdam']), {});
                }

                document.getElementById("txt3a").innerHTML = profileJson['FormTitle'];
                $('#modal-container-general-info').modal();
            }else{
                let emsg="";
                if(response) emsg="HTTP-Error: " + response.status + " on spatial_unit_profile";
                else emsg="O servidor está indisponível ou sua internet está desligada.";
                
                console.log(emsg);
                $('.toast').toast('show');
                $('.toast-body').html("Encontrou um erro na solicitação ao servidor.<br />"+emsg);
            }
        }
        if (jsConfig.className != 'null'){
            if(ams.App._landUseList.length>0){
                $("#loading_data_info").css('display','block');
                getGraphics(jsConfig);
            }else{
                ams.App._resetMap("O filtro deve incluir ao menos uma categoria fundiária. A solicitação não foi concluída.");
            }
        }
    },

    saveIndicators: function (jsConfig) {
        async function _saveIndicators (jsConfig) {
            $("#loading_data_info").css('display','block');

            // defining filename prefix
            let layerName = ams.App._getLayerPrefix();
            layerName = ams.App._spatialUnits.find(
                layerName.substring(layerName.indexOf(':') + 1).replace("_view", "")
            );
            layerName = (layerName)?(layerName.description):(baseName);
            layerName = layerName.replaceAll(" ", "_");

            let dataName = ams.App._appClassGroups.getGroupName(ams.App._suViewParams.classname);
            dataName = (dataName)?(dataName):(viewParams.classname);
            dataName=dataName.replaceAll(" ", "_");

            let sdt = ams.PeriodHandler._startdate.toLocaleDateString().replaceAll('/','-');
            let edt = ams.PeriodHandler._enddate.toLocaleDateString().replaceAll('/','-');

            let filenamePrefix = (
                ams.Config.biome + "_" + layerName + "-" + jsConfig["suName"] + "_" + dataName + "_" + edt + "_" + sdt
            );

            // defining params to send
            jsConfig["targetbiome"] = ams.Config.biome;
            jsConfig["isAuthenticated"] = ams.Auth.isAuthenticated();
            jsConfig["filenamePrefix"] = filenamePrefix;
            
            let jsConfigStr = JSON.stringify(jsConfig);
            let response = await fetch("indicators?sData=" + jsConfigStr).catch(
                ()=>{
                    console.log("The backend service may be offline or your internet connection has been interrupted.");
                }
            );

            $("#loading_data_info").css('display','none');
            
            if (response && response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const link = document.createElement('a');
                link.href = url;
                link.download = filenamePrefix + '.zip';
                link.click();
                window.URL.revokeObjectURL(url);
            } else {
                let emsg = "";
                if(response) emsg = "HTTP-Error: " + response.status + " on spatial_unit_profile";
                else emsg="O servidor está indisponível ou sua internet está desligada.";
                console.log(emsg);
                $('.toast').toast('show');
                $('.toast-body').html("Encontrou um erro na solicitação ao servidor.<br />"+emsg);
            }
        }
        
        _saveIndicators(jsConfig);
    },

    startMunicipalityPanel: function (name, value) {
        async function _startMunicipalityPanel (name, value) {
            let startDate = ams.App._dateControl.startdate;
            let endDate = ams.App._dateControl.enddate;
            let tempUnit = ams.App._dateControl.period;
            let response = await fetch(
                "panel?"+name+"="+value +
                "&startDate=" + ((startDate !== undefined)? startDate : "") +
                "&endDate=" + ((endDate !== undefined)? endDate : "") +
	            "&tempUnit=" + ((tempUnit !== undefined)? tempUnit : "") +
                "&classname=" + ams.App._suViewParams.classname
            ).catch(
                ()=>{
                    console.log("The backend service may be offline or your internet connection has been interrupted.");
                }
            );

            if (response && response.ok) {
                const html = await response.text();

                const newWindow = window.open('', '_blank');
                if (!newWindow) {
                    window.alert('Não foi possível abrir a nova janela. Verifique o bloqueador de pop-ups.');
                    return;
                }
                newWindow.document.write(html);
                newWindow.document.close();

            } else {
                let emsg = "";
                if(response) emsg = "HTTP-Error: " + response.status;
                else emsg="O servidor está indisponível ou sua internet está desligada.";
                console.log(emsg);
                $('.toast').toast('show');
                $('.toast-body').html("Encontrou um erro na solicitação ao servidor.<br />"+emsg);
            }
        }

        _startMunicipalityPanel(name, value);
    }

};
