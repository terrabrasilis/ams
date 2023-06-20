var ams = ams || {};

ams.Map = {
	/**
	 * Used to control the popup content
	 */
	PopupControl: {
		_popupReference:null,
		_unit:'km²',
		_infoBody:[]
	},
	ViewParams: function(classname, dateControll, propertyName, limit) {
		this.classname = classname;
		this.startdate = dateControll.startdate;
		this.enddate = dateControll.enddate;
		this.prevdate = dateControll.prevdate;
		this.propertyName = propertyName;
		this.limit = limit;
		this.toWmsFormat = function() {
			return "classname:" + this.classname
					+ ";startdate:" + this.startdate
					+ ";enddate:" + this.enddate
					+ ";prevdate:" + this.prevdate
					+ ";orderby:" + this.propertyName
					+ ";landuse:" + ams.App._landUseList.join('\\,')
					+ ";limit:" + this.limit;
		};

		this.updateDates = function(dateControll) {
			this.startdate = dateControll.startdate;
			this.enddate = dateControll.enddate;
			this.prevdate = dateControll.prevdate;
		};

		this.updatePropertyName = function(propertyName) {
			this.propertyName = propertyName;
		};
	},

	SpatialUnits: function(spatialUnits, suDefaultName) {
		this.spatialUnits = spatialUnits;
		this.defaultName = suDefaultName;
		this.default = null;

		this.getDefault = function(){
			if(!this.default)
				this.default = this.find(this.defaultName);
			return this.default;
		}

		/** Get Spatial Unit params by su layer name */
		this.find = function(dataname){
			return this.spatialUnits.find((suitem)=>{return suitem.dataname==dataname;});
		}

		this.length = function() {
			return this.spatialUnits.length;
		}

		this.at = function(pos) {
			return this.spatialUnits[pos];
		}
	},

	AppClassGroups: function(groups) {
		this._groupNamesMap = {};
		this._setNames = function(groups) {
			let risk_index=null;
			for(var i = 0; i < groups.length; i++) {
				// verify if risk data should be displayed. Use the group name 'RK' that need be defined into database.
				if(groups[i].name=='RK' && !ams.Auth.isAuthenticated()) risk_index=i;
				groups[i].acronym = groups[i].name;
				this._groupNamesMap[groups[i].name] = groups[i].title;
				groups[i].name = groups[i].title;
			}
			// remove the risk option if needed
			if(risk_index!==null) groups.splice(risk_index,1);
			this.groups = groups;
		}

		this._setNames(groups);
		
		this.length = function() {
			return this.groups.length;
		}
		
		this.at = function(pos) {
			return this.groups[pos];
		}	

		this.getGroup = function(acronym) {
			for(let i = 0; i < this.groups.length; i++) {
				if(this.groups[i].acronym == acronym) {
					return this.groups[i];
				}
			}
		}

		this._filterClasses = function(acronym) {
			let group = this.getGroup(acronym);
			let res = "";
			let classes = group.classes;
			for(let i = 0; i < classes.length; i++) {
				res += "classname='" + classes[i] + "'"
				if(i < group.classes.length - 1) {
					res += " OR ";
				}
			}
			return res;
		}

		this.getCqlFilter = function(viewParams, useClass) {
			useClass=(typeof useClass=='undefined')?(true):(useClass);
			let classFilter=((useClass)?("AND ("+this._filterClasses(viewParams.classname)+")"):(""));
			return "(view_date > " + viewParams.enddate
					+ ") AND (view_date <= "
					+ viewParams.startdate
					+ ") "
					+ classFilter;
		}	

		this.getGroupName = function(acronym) {
			return this._groupNamesMap[acronym];
		} 
	},

	WFS: function(baseUrl) {
		this.url = baseUrl + "/ows?SERVICE=WFS&REQUEST=GetFeature";
		this.getMinOrMax = function(layerName, propertyName, viewParams, isMin) {
			let wfsUrl = this.url 
						+ "&typeName=" + layerName
						+ "&propertyName=" + propertyName
						+ "&outputFormat=json"
						+ "&viewparams=classname:" + viewParams.classname
										+ ";startdate:" + viewParams.startdate
										+ ";enddate:" + viewParams.enddate
										+ ";prevdate:" + viewParams.prevdate
										+ ";order:" + (isMin ? 'ASC' : 'DESC')
										+ ";orderby:" + propertyName
										+ ";landuse:" + ams.App._landUseList.join('%5C,')
										+ ";limit:1";
			let res;
			$.ajax({
				dataType: "json",
				url: wfsUrl,
				async: false,
				headers: {
					'Authorization': 'Bearer '+
					( (ams.Auth.isAuthenticated())?(Authentication.getToken()):("") )
				},
				success: function(data) {
					res = (data.totalFeatures>0)?(data["features"][0]["properties"][propertyName]):(false);					  
				},
				error: function() {
					res = false;
				}
			});
			return res;
		}
		this.getMax = function(layerName, propertyName, viewParams) {		
			return this.getMinOrMax(layerName, propertyName, viewParams, false);
		}

		this.getMin = function(layerName, propertyName, viewParams) {
			return this.getMinOrMax(layerName, propertyName, viewParams, true);
		}

		this.getLastDate = function (layerName) {
			let propertyName = "last_date";
			let classname = (ams.App._suViewParams) ? (ams.App._suViewParams.classname) : (ams.Config.defaultFilters.indicator);
			let wfsUrl = this.url +
			"&typeName=" + layerName +
			"&propertyName=" + propertyName +
			"&outputFormat=json" +
			"&viewparams=classname:" + classname +
			";landuse:" + ams.App._landUseList.join('%5C,');
			let res;
			$.ajax({
			dataType: "json",
			url: wfsUrl,
			async: false,
			headers: {
				'Authorization': 'Bearer ' +
				((ams.Auth.isAuthenticated()) ? (Authentication.getToken()) : (""))
			},
			success: function (data) {
				res = data["features"][0]["properties"][propertyName];			
				last_date = res;
				
				if (res === null) {
				lastDateStatus = "Não há dados disponíveis";
				} else {
				let currentDate = new Date();
				let lastDate = new Date(res);
				let timeDifference = currentDate.getTime() - lastDate.getTime();
				let daysDifference = Math.floor(timeDifference / (1000 * 3600 * 24));
				
				if (daysDifference > 7) {
					lastDateStatus = "Data desatualizada:";
				} else {
					lastDateStatus = "Data atualizada:";
				}
				}
			},
			error: function () {
				res = false;
			}
			});
			return res;
		};
	  
	  

		this.getFile = function(layerName, viewParams, 
								outputFormat, extension,
								properties, propertyName){

			let baseName = layerName.substring(layerName.indexOf(':') + 1).replace("_view", "");
			let sdt=ams.PeriodHandler._startdate.toLocaleDateString().replaceAll('/','-');
			let edt=ams.PeriodHandler._enddate.toLocaleDateString().replaceAll('/','-');
			let pdt=ams.PeriodHandler._previousdate.toLocaleDateString().replaceAll('/','-');

			let diff = '';
			const _diff = "_diff";
			if (baseName.indexOf(_diff) > 0) {
				diff = "_" + pdt; //viewParams.prevdate;
				baseName = baseName.replace(_diff, "");
			}
			let suName = ams.App._spatialUnits.find(baseName);
			suName = (suName)?(suName.description):(baseName);
			suName=suName.replaceAll(" ", "_");
			let dataName = ams.App._appClassGroups.getGroupName(viewParams.classname);
			dataName = (dataName)?(dataName):(viewParams.classname);
			dataName=dataName.replaceAll(" ", "_");

			let filename = ams.Config.biome
				+ "_"	
				+ suName
				+ "_"
				+ dataName
				+ "_"
				+ edt
				+ "_"
				+ sdt
				+ diff
				+ "."
				+ extension;

			// operation type (optype) is used to get all spatial units on shapefile download. See SQL Views inside GeoServer.
			let wfsUrl = this.url 
						+ "&typeName=" + layerName
						+ "&outputFormat=" + outputFormat
						+ "&format_options=filename:" + filename
						+ "&version=1.0.0"
						+ "&propertyName=" + (properties ? properties : "")
						+ "&viewparams=classname:" + viewParams.classname
										+ ";startdate:" + viewParams.startdate
										+ ";enddate:" + viewParams.enddate
										+ ";prevdate:" + viewParams.prevdate
										+ ";orderby:" + propertyName
										+ ";landuse:" + ams.App._landUseList.join('%5C,')
										+ ";limit:" + viewParams.limit
										+ ((extension=='csv')?(""):(";optype:DOWNLOAD"));

			if (extension == 'csv') {
				$.ajax({
					url: wfsUrl,
					async: false,
					headers: {
						'Authorization': 'Bearer ' + ((ams.Auth.isAuthenticated()) ? (Authentication.getToken()) : (""))
					},
					success: function(data) {
						const blob = new Blob([data], {type: "application/octet-stream"});
						const url = window.URL.createObjectURL(blob);
						const a = document.createElement("a");
						a.href = url;
						a.download = filename;
						a.click();
					},
					error: function (jqXHR, textStatus) {
						window.console.log(textStatus);
					}
				});
			} else {
				let a = document.createElement("a");
				a.href = wfsUrl + ((ams.Auth.isAuthenticated())?("&access_token="+Authentication.getToken()):(""));
				a.setAttribute("download", filename);
				a.click();
			}
        }

		this.getShapeZip = function(layerName, viewParams) {
			let properties = "name,"+
			((ams.App._propertyName=="area")?("area,percentage"):(ams.App._propertyName))+
			",geometry";
			this.getFile(layerName, viewParams, "shape-zip", "zip", properties, ams.App._propertyName);
		} 

		this.getCsv = function(layerName, viewParams) {
			let properties = "name,"+
			((ams.App._propertyName=="area")?("area,percentage"):(ams.App._propertyName));
			this.getFile(layerName, viewParams, "csv", "csv", properties, ams.App._propertyName);
		} 
	},

	TemporalUnits: function() {
		this.aggregates = {
			0: {"key": "7d", "value": "Agregado 7 dias"},
			1: {"key": "15d", "value": "Agregado 15 dias"},
			2: {"key": "1m", "value": "Agregado 30 dias"},
			3: {"key": "3m", "value": "Agregado 90 dias"},
			4: {"key": "1y", "value": "Agregado 365 dias"},
		};

		this.differeces = {
			0: {"key": "onPeriod", "value": "No Per&#237;odo"},
			1: {"key": "periodDiff", "value": "Diferen&#231;a Per&#237;odo Anterior"}
		}

		this.getCurrentName = function() {
			return this.differeces[0].value;
		}

		this.getAggregates = function() {
			return this.aggregates;
		}

		this.getDifferences = function() {
			return this.differeces;
		}

		this.isAggregate = function(name) {
			for(let i = 0; i < Object.keys(this.aggregates).length; i++) {
				if(this.aggregates[i].value == name) {
					return true;
				} 
			}
			return false;
		}

		this.isDifference = function(name) {
			for(let i = 0; i < Object.keys(this.differeces).length; i++) {
				if(this.differeces[i].value == name) {
					return true;
				} 
			}
			return false;
		}		
	},

	LegendController: function(map, wmsUrl) {
		this._wmsLegendControl = new L.Control.WMSLegend;
		this._url;
		this._wmsUrl = wmsUrl;
		this._map = map;

		this.setUrl = function(layerName, layerStyle) {
			this._url = this._wmsUrl 
						+ "?REQUEST=GetLegendGraphic&FORMAT=image/png&WIDTH=20&HEIGHT=20"
						+ "&LAYER=" + layerName
						+ "&SLD_BODY=" + layerStyle.getEncodeURI()
						+ ((ams.Auth.isAuthenticated())?("&access_token="+Authentication.getToken()):(""));
		}

		this.init = function(layerName, layerStyle)	{
			this._setStaticLegends();// for default layers defined in config.js
			this._setWMSControl(layerName, layerStyle);
			this._map.addControl(this._wmsLegendControl);
		}

		this.disable = function(){
			this._map.removeControl(this._wmsLegendControl);
		}

		this.update = function(layerName, layerStyle) {
			this._setStaticLegends();
			this._setWMSControl(layerName, layerStyle);
			this._map.removeControl(this._wmsLegendControl);
			this._map.addControl(this._wmsLegendControl);
		}	

		this._setWMSControl = function(layerName, layerStyle) {
			this.setUrl(layerName, layerStyle);
			this._wmsLegendControl.options.uri = this._url;
			this._wmsLegendControl.options.position = "middleright";
		}

		/**
		 * Defines which layer will be displayed in the legend and the settings
		 * that will be used for the image to be displayed. 
		 * 
		 * https://docs.geoserver.org/stable/en/user/services/wms/get_legend_graphic/index.html
		 */
		this._setStaticLegends = function() {
			let baseurl = this._wmsUrl
			+ "?REQUEST=GetLegendGraphic&FORMAT=image/png&WIDTH=20&HEIGHT=20"
			+ ((ams.Auth.isAuthenticated())?("&access_token="+Authentication.getToken()):(""));
			if(ams.App._referenceLayerName.includes(ams.Config.defaultLayers.deter)){
				let cql=ams.App._appClassGroups.getCqlFilter(ams.App._suViewParams, ams.App._hasClassFilter);
				let deterurl = baseurl + "&LAYER=" + ams.App._referenceLayerName
				+ "&LEGEND_OPTIONS=hideEmptyRules:true;forceLabels:on;"
				+ "&CQL_FILTER=" + cql;
				this._wmsLegendControl.options.static.deter.url = deterurl;
				this._wmsLegendControl.options.static.af.url=null;
				this._wmsLegendControl.options.static.risk.url=null;
			}else if(ams.App._referenceLayerName.includes(ams.Config.defaultLayers.activeFire)){
				// here we force a different style to get the legend without 3 entries
				let afurl = baseurl + "&LAYER=" + ams.App._referenceLayerName
				+ "&STYLE=active_fires_legend"
				+ "&LEGEND_OPTIONS=forceLabels:on;";
				this._wmsLegendControl.options.static.af.url = afurl;
				this._wmsLegendControl.options.static.deter.url=null;
				this._wmsLegendControl.options.static.risk.url=null;
			}else{
				// Legend to risk raster layer from raw data
				this._wmsLegendControl.options.static.af.url=null;
				this._wmsLegendControl.options.static.deter.url=null;
				let riskurl = baseurl + "&LAYER=" + ams.App._referenceLayerName;
				this._wmsLegendControl.options.static.risk.url=riskurl;
			}
		}
	}
};
