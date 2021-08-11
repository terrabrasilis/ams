var ams = ams || {};

ams.Map = {
	update: function(source, layerName, viewParams, layerStyle) {
		source._subLayers = {};
		source._subLayers[layerName] = true;		
		source.options["viewparams"] = viewParams.toWmsFormat();
		source._overlay.wmsParams.layers = layerName;
		if(layerStyle) {
			source.options["sld_body"] = layerStyle.getSLD();
			source._overlay.setParams({
				"viewparams": viewParams.toWmsFormat(),
				"sld_body": layerStyle.getSLD(),
			});				
		}
		else {
			source._overlay.setParams({
				"viewparams": viewParams.toWmsFormat(),
			});	
		}	
	},

	ViewParams: function(classname, dateControll, limit) {
		this.classname = classname;
		this.startdate = dateControll.startdate;
		this.enddate = dateControll.enddate;
		this.prevdate = dateControll.prevdate;
		this.limit = limit;
		this.toWmsFormat = function() {
			return "classname:" + this.classname
					+ ";startdate:" + this.startdate
					+ ";enddate:" + this.enddate
					+ ";prevdate:" + this.prevdate
					+ ";limit:" + this.limit;
		}

		this.updateDates = function(dateControll) {
			this.startdate = dateControll.startdate;
			this.enddate = dateControll.enddate;
			this.prevdate = dateControll.prevdate;
		}
	},

	SpatialUnits: function(spatialUnits, suDefaultName) {
		this._suNamesMap = {
			"csAmz_150km": "C&#233;lulas 150x150 Km&#178;",
			"csAmz_300km": "C&#233;lulas 300x300 Km&#178;",
			"amz_states": "Estados",
			"amz_municipalities": "Munic&#237;pios",
		};

		this._suDataNamesMap = {};

		this.getName = function(dataname) {
			return this._suNamesMap[dataname];
		}

		this.getSpatialUnit = function getSpatialUnit(name) {
			for(var i = 0; i < this.spatialUnits.length; i++) {
				if(this.spatialUnits[i].dataname == name) {
					return this.spatialUnits[i];
				}
			}
			return null;				
		}	

		this._setNames = function(sus) {
			for(var i = 0; i < sus.length; i++) {
				sus[i].name = this._suNamesMap[sus[i].dataname];
				this._suDataNamesMap[sus[i].name] = sus[i].dataname;
			}
			this.spatialUnits = sus;
		}
		
		this._setNames(spatialUnits);

		this.default = this.getSpatialUnit(suDefaultName);

		this.isSpatialUnit = function(name) {
			for(var i = 0; i < this.spatialUnits.length; i++) {
				if(this.spatialUnits[i].name == name) {
					return true;
				}
			}
			return false;			
		}

		this.length = function() {
			return this.spatialUnits.length;
		}

		this.at = function(pos) {
			return this.spatialUnits[pos];
		}	

		this.getDataName = function(name) {
			return this._suDataNamesMap[name];
		}
	},

	DeterClassGroups: function(groups) {
		this._groupNamesMap = {
			"DS": "DETER Desmatamento",
			"DG": "DETER Degrada&#231;&#227;o",
			"CS": "DETER Corte-Seletivo",
			"MN": "DETER Minera&#231;&#227;o",
		}

		this._setNames = function(groups) {
			for(var i = 0; i < groups.length; i++) {
				groups[i].acronym = groups[i].name;
				groups[i].name = this._groupNamesMap[groups[i].name];
			}
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

		this.getCqlFilter = function(viewParams) {
			return "(date > " + viewParams.enddate
					+ ") AND (date <= "
					+ viewParams.startdate
					+ ") AND ("
					+ this._filterClasses(viewParams.classname)
					+ ")";
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
					res = data["features"][0]["properties"][propertyName];
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

		this.getLastDate = function(layerName) {
			let propertyName="last_date";
			let wfsUrl = this.url 
						+ "&typeName=" + layerName
						+ "&propertyName=" + propertyName
						+ "&outputFormat=json";
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
					res = data["features"][0]["properties"][propertyName];
				}
			});		
			return res;	
		}

		this.getFile = function(layerName, viewParams, 
								outputFormat, extension,
								propertyName){

			let _viewToResolution = {
				"csAmz_150km": "CELL_150Km",
				"csAmz_300km": "CELL_300Km",
				"amz_states": "ESTADO",
				"amz_municipalities": "MUNIC",
			};
			let baseName = layerName.substring(layerName.indexOf(':') + 1).replace("_view", "");
			let diff = '';
			const _diff = "diff";
			if (baseName.indexOf(_diff) > 0) {
				diff = "_" + viewParams.prevdate;
				baseName = baseName.replace(_diff, "");
			}
			let resolution = _viewToResolution[baseName];
			if (typeof resolution == 'undefined') {
				resolution = baseName;
			}

			let filename = "AMS_"
						+ resolution
						+ "_"
						+ viewParams.classname
						+ "_"
						+ viewParams.startdate
						+ "_"
						+ viewParams.enddate
						+ diff
						+ "."
						+ extension;

			let wfsUrl = this.url 
						+ "&typeName=" + layerName
						+ "&outputFormat=" + outputFormat
						+ "&format_options=filename:" + filename
						+ "&version=1.0.0"
						+ "&propertyName=" + (propertyName ? propertyName : "")
						+ "&viewparams=classname:" + viewParams.classname
										+ ";startdate:" + viewParams.startdate
										+ ";enddate:" + viewParams.enddate
										+ ";prevdate:" + viewParams.prevdate
										+ ";limit:" + viewParams.limit;

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
					fail: function (jqXHR, textStatus) {
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
			let propertyName = "name,area,percentage,geometry";
			this.getFile(layerName, viewParams, "shape-zip", "zip", propertyName);
		} 

		this.getCsv = function(layerName, viewParams) {
			let propertyName = "name,area,percentage";
			this.getFile(layerName, viewParams, "csv", "csv", propertyName);
		} 
	},

	TemporalUnits: function() {
		this.aggregates = {		
			0: {"key": "7d", "value": "Agregado Semanal"},
			1: {"key": "15d", "value": "Agregado 15 Dias"},
			2: {"key": "1m", "value": "Agregado Mensal"},
			3: {"key": "3m", "value": "Agregado 3 Meses"},
			4: {"key": "1y", "value": "Agregado Anual"},
		};

		this.differeces = {
			0: {"key": "none", "value": "No Per&#237;odo"},
			1: {"key": "1m", "value": "Diferen&#231;a Per&#237;odo Anterior"},
			// 2: {"key": "1y", "value": "Previous Year"}, TODO
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
			this._setWMSControl(layerName, layerStyle);
			this._map.addControl(this._wmsLegendControl);
		}

		this.update = function(layerName, layerStyle) {
			this._setWMSControl(layerName, layerStyle);
			this._map.removeControl(this._wmsLegendControl);
			this._map.addControl(this._wmsLegendControl);
		}	

		this._setWMSControl = function(layerName, layerStyle) {
			this.setUrl(layerName, layerStyle);
			this._wmsLegendControl.options.uri = this._url;
			this._wmsLegendControl.options.position = "bottomright";
		}
	}
};
