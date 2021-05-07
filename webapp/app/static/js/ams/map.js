var ams = ams || {};

ams.Map = {
	update: function(source, layerName, viewParams, layerStyle) {
		source._subLayers = {};
		source._subLayers[currSuLayerName] = true;		
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
			0: {"key": "15d", "value": "15 Days"},
			1: {"key": "1m", "value": "Month"},
			2: {"key": "3m", "value": "3 Months"},
			3: {"key": "1y", "value": "Year"},
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

	DateController: function() {
		this.startdate;
		this.enddate;
		this.prevdate;

		this.toUTCDate = function(date) {
			let uday = date.getUTCDate();
			let day = uday < 10 ? "0" + uday : uday;
			let umonth = date.getUTCMonth() + 1;
			let month = umonth < 10 ? "0" + umonth : umonth;
			return `${date.getUTCFullYear()}-${month}-${day}`; 
		}

		this.isLastDay =function(date) {
			let last = new Date(date);
			let month = date.getMonth();
			last.setDate(last.getDate() + 1);
			return last.getMonth() != month; 
		}

		this.setPeriod = function(startdate, period) {
			this.startdate = startdate;
			let enddate = new Date(startdate + "T00:00:00");
			let prevdate = new Date(startdate + "T00:00:00");
			if(period == "15d") {
				enddate.setUTCDate(enddate.getUTCDate() - 15);
				prevdate.setUTCDate(prevdate.getUTCDate() - 30);
			}
			else if(period == "1m") {
				if(this.isLastDay(enddate)) {
					enddate.setUTCDate(0);
					prevdate.setUTCDate(0);
					prevdate.setUTCDate(0);
				}
				else {
					let day = enddate.getUTCDate();
					enddate.setUTCDate(enddate.getUTCDate() - 32);
					prevdate.setUTCDate(prevdate.getUTCDate() - 2*32);
					prevdate.setUTCDate(day);
					enddate.setUTCDate(day);
				}
			}
			else if(period == "3m") {
				if(this.isLastDay(enddate)) {
					enddate.setUTCDate(enddate.getUTCDate() - 2*32);
					enddate.setUTCDate(0);
					prevdate.setUTCDate(prevdate.getUTCDate() - 5*32);
					prevdate.setUTCDate(0);
				}
				else {
					let day = enddate.getUTCDate();
					enddate.setUTCDate(enddate.getUTCDate() - 2*32);
					prevdate.setUTCDate(prevdate.getUTCDate() - 5*32);
					enddate.setUTCDate(day);
					prevdate.setUTCDate(day);
				}
			}			
			else if(period == "1y") {
				enddate.setUTCFullYear(enddate.getUTCFullYear() - 1);
				prevdate.setUTCFullYear(prevdate.getUTCFullYear() - 2);
			}						
			this.enddate = this.toUTCDate(enddate);
			this.prevdate = this.toUTCDate(prevdate);
		}
	}
};
