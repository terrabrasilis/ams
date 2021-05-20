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
		this.getSpatialUnit = function getSpatialUnit(name) {
			for(var i = 0; i < this.spatialUnits.length; i++) {
				if(this.spatialUnits[i].dataname == name) {
					return this.spatialUnits[i];
				}
			}
			return null;				
		}			
		this.spatialUnits = spatialUnits;
		this.default = this.getSpatialUnit(suDefaultName);
		this.isSpatialUnit = function(name) {
			for(var i = 0; i < this.spatialUnits.length; i++) {
				if(this.spatialUnits[i].dataname == name) {
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
	},

	DeterClassGroups: function(groups) {
		this.groups = groups;
		this.length = function() {
			return this.groups.length;
		}
		this.at = function(pos) {
			return this.groups[pos];
		}		
	},

	WFS: function(url) {
		this.url = url;
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
	},

	TemporalUnits: function() {
		this.aggregates = {		
			0: {"key": "7d", "value": "Week"},
			1: {"key": "15d", "value": "15 Days"},
			2: {"key": "1m", "value": "Month"},
			3: {"key": "3m", "value": "3 Months"},
			4: {"key": "1y", "value": "Year"},
		};

		this.differeces = {
			0: {"key": "none", "value": "Current"},
			1: {"key": "1m", "value": "Previous"},
			// 2: {"key": "1y", "value": "Previous Year"}, TODO
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
						+ "REQUEST=GetLegendGraphic&FORMAT=image/png&WIDTH=20&HEIGHT=20"
						+ "&LAYER=" + layerName
						+ "&sld_body=" + layerStyle.getEncodeURI(); 			
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
