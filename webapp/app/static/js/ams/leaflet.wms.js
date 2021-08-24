var ams = ams || {};

ams.LeafletWms = {
	floatDecimals: 2,// change this number to change the number of decimals to float numbers
	DETERMetadataURL: "http://terrabrasilis.dpi.inpe.br/geonetwork/srv/eng/catalog.search#/metadata/f9b7e1d3-0d4e-4cb1-b3cf-c2b8906126be",
	Source: L.WMS.Source.extend({
	    'initialize': function(url, options, deterClassGroups) {
	        //L.WMS.Source.prototype.initialize(url, options); # TODO: call base class initialize instead
	        L.setOptions(this, options);
	        if (this.options.tiled) {
	            this.options.untiled = false;
	        }
	        this._url = url;
	        this._subLayers = {};
	        this._overlay = this.createOverlay(this.options.untiled);	        
	        this._deterClassGroups = deterClassGroups;
	    },   

		'showFeatureInfo': function(latlng, info) {
			if(this._isSpatialUnitInfo(info)) {
				this._map.openPopup(this._formatSpatialUnitPopup(info), latlng);
			}
			else if(this._isDeterInfo(info)) {
				this._map.openPopup(this._formatDeterPopup(info), latlng);
			}
		},

		'_isSpatialUnitInfo': function(info) {
			return info.includes("area") && info.includes("percentage") && info.includes("name"); 
		},

		'_isDeterInfo': function(info) {
			return info.includes("origin_gid") && info.includes("date_audit"); 
		},		

		'_formatSpatialUnitPopup': function(str) {
			let tokens = str.split("\n");
			let result = {
				"name": "",
				"classname": "",
				"area": 0,
				"percentage": 0,
			};

			for(let i = 0; i < tokens.length; i++)
			{
				let pair = tokens[i].split(" = ");
				if(pair.length > 1) {
					if(pair[0] in result) {
						result[pair[0]] = isNaN(pair[1]) ? pair[1] : parseFloat(pair[1]).toFixed(ams.LeafletWms.floatDecimals);
					}
				}
			}

			return this._createSpatialUnitInfoTable(result);
		},

		'_formatClassName': function(acronym) {
			return acronym != "null" ? this._deterClassGroups.getGroupName(acronym) : " ";
		},

		'_createSpatialUnitInfoTable': function(result) {
			return '<table class="popup-spatial-unit-table" style="width:100%">'
						+ "<tr>"
							+ "<th></th>"
							+ "<th></th>"
							+ "</tr>"
						+ "<tr>"
							+ "<td>Unidade Espacial   </td>"
							+ "<td>" + result["name"] + "</td>"
						+ "</tr>"
						+ "<tr>"
							+ "<td>Classe   </td>"
							+ "<td>" + this._formatClassName(result["classname"]) + "</td>"
						+ "</tr>"
						+ "<tr>"
							+ "<td>&#193;rea (km&#178;)   </td>"
							+ "<td>" + result["area"] + "</td>"
						+ "</tr>"
						+ "<tr>"
							+ "<td>Porcentagem   </td>"
							+ "<td>" + result["percentage"] + "%</td>"
						+ "</tr>"																		
					+ "</table>"			
		},
		'_formatDeterPopup': function(str) {
			let tokens = str.split("\n");
			let result = {};
			let numberFormat = function(n){
				let sp=n.split('.');// determine if number is float by exists point
				return ( (sp.length==2)?(parseFloat(n).toFixed(ams.LeafletWms.floatDecimals)):(parseInt(n)) );
			};
			for(let i = 0; i < tokens.length; i++)
			{
				let pair = tokens[i].split(" = ");
				if(pair.length > 1) {
					result[pair[0]] = isNaN(pair[1]) ? pair[1] : numberFormat(pair[1]);
				}
			}
			delete result["geom"];
			delete result["month_year"];
			delete result["quadrant"];
			delete result["lot"];
			return this._createDeterInfoTable(result);
		},
		'_createDeterInfoTable': function(result) {
			let table = '<table class="popup-deter-table" style="width:100%">'
						+ "<tr>"
							+ "<th></th>"
							+ "<th></th>"
							+ "</tr>";
			for(let k in result) {
				let v = result[k];
				if(k.includes("date")) {
					v = this._formatDate(v);
				}
				if(k.includes("car_imovel") && (v.split(";")).length>=1 ) {
					table += "<tr>"
								+ "<td colspan='2'>"
								+ k
								+ (v != "null" ? this._formatListCAR(v) : " ")
								+ "</td>"
								+ "</tr>";
				}else{
					table += "<tr>"
								+ "<td>" + k + "  </td>"
								+ "<td>" + (v != "null" ? v : " ") + "</td>"
								+ "</tr>";
				}
			}
			table += "<tr><td colspan='2'><a target='_blank' href='"+ams.LeafletWms.DETERMetadataURL+"'>Ver detalhes dos atributos</a></td></tr>";
			table += "</table>"
			return table;
		},
		'_formatDate': function(str) {
			let res = str.replace("Z", "").split("-");
			return `${res[2]}/${res[1]}/${res[0]}`
		},
		'_formatListCAR': function(str) {
			let ids = str.replaceAll(";","\n");
			return "<div id='ids_car'>"+
			"<textarea name='listcars' rows='2' cols='50' readonly "+
			"style='resize: none;max-width: fit-content;border:0;font-size:xx-small;'>"+
			ids+"</textarea></div>";
		}

	})
};