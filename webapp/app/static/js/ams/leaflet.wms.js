var ams = ams || {};

ams.LeafletWms = {
    Source: L.WMS.Source.extend({
        'initialize': function (url, options, deterClassGroups) {
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

        'showFeatureInfo': function (latlng, info) {
            if(info.includes("no features were found")) return;
            if (this._isSpatialUnitInfo()) {
                this._map.openPopup(this._formatSpatialUnitPopup(info, this.viewConfig, latlng) , latlng); //-- mgd T6 this.config
            }else{
                this._map.openPopup(this._formatDeterPopup(info), latlng);
            }
        },

        '_isSpatialUnitInfo': function () {
            return !this._overlay.wmsParams.layers.includes(ams.Config.defaultLayers.deterAmz);
        },

        '_formatSpatialUnitPopup': function (str, viewConfig, latlng) {  //-- mgd T6
            let tokens = str.split("\n");
            let result = {
                "name": "",
                "classname": "",
                "area": 0,
                "percentage": 0,
            };
            //-- mgd T6 v
            viewConfig.click = { when: new Date(), where: latlng };
            let value;
            //-- mgd T6 ^
            for (let i = 0; i < tokens.length; i++) {
                let pair = tokens[i].split(" = ");
                if (pair.length > 1) {
                    value= isNaN(pair[1]) ? pair[1] : parseFloat(pair[1]);
                    viewConfig.click[pair[0]] = isNaN(pair[1]) ?  value.replace(/ /g, "|"): value;  //-- mgd T6 HTML render error (space brakes quotes), check why
                    if (pair[0] in result) {
                        result[pair[0]] = isNaN(value) ? value : ams.Utils.numberFormat(value);
                    }
                }
            }
            let sButton = "";
            // -- mlra
            if (viewConfig.click.classname == 'null')
                viewConfig.click.classname = "DS";
            if ((viewConfig.click.classname != 'null') && (viewConfig.click.area != 0)) {
                sButton = this._createGraphicButton(viewConfig);
            }
            return this._createSpatialUnitInfoTable(result) + sButton;
        },

        '_formatClassName': function (acronym) {
            return acronym != "null" ? this._deterClassGroups.getGroupName(acronym) : " ";
        },
        //!--  mgd T6 v-->
        '_createGraphicButton': function (viewConfig) {
            let sButton=
                  '<div style="width: 100%;">'
                + '<button class="btn btn-primary-p btn-success" onclick=ams.App.displayGraph('  // see app.js
                + JSON.stringify(viewConfig)
                + ')>Perfil</button>'
                + '</div>';
            return sButton;
        },
        '_createSpatialUnitInfoTable': function (result) {
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
            +"</table>";
        },

        '_formatDeterPopup': function(str) {
			let tokens = str.split("\n");
			let result = {};
			for(let i = 0; i < tokens.length; i++)
			{
				let pair = tokens[i].split(" = ");
				if(pair.length > 1) {
					result[pair[0]] = isNaN(pair[1]) ? pair[1] : ams.Utils.numberFormat(pair[1]);
				}
			}
			delete result["geom"];
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
				if(k.includes("view_date")) {
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
			table += "<tr><td colspan='2'><a target='_blank' href='"+ams.Config.DETERMetadataURL+"'>Ver detalhes dos atributos</a></td></tr>";
			table += "</table>"
			return table;
		},

        '_formatDate': function (str) {
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