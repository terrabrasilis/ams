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
            this._popupReference=null;
        },

        'showFeatureInfo': function (latlng, jsonTxt) {
            if(jsonTxt.includes("no features were found")) return;
            let featureInfo = JSON.parse(jsonTxt);
            let htmlInfo="";
            if(featureInfo.numberReturned>=1){
                htmlInfo="<div><h5>"+this._overlay.wmsParams.layers+"</h5><br>";
                if (this._isSpatialUnitInfo()) {
                    htmlInfo=htmlInfo+this._formatSpatialUnitPopup(featureInfo, latlng);
                }else{
                    htmlInfo=htmlInfo+this._formatDeterPopup(featureInfo);
                }
                htmlInfo=htmlInfo+"</div>";

                if(this._popupReference && this._popupReference._popup){
                    htmlInfo=htmlInfo+this._popupReference._popup.getContent();
                    this._popupReference.closePopup();
                    delete this._popupReference;
                }
                this._popupReference=this._map.openPopup(htmlInfo, latlng);
            }
        },

        '_isSpatialUnitInfo': function () {
            let isDeter=this._overlay.wmsParams.layers.includes(ams.Config.defaultLayers.deterAmz);
            let isAF=this._overlay.wmsParams.layers.includes(ams.Config.defaultLayers.activeFireAmz);
            return !isDeter&&!isAF;
        },

        '_formatSpatialUnitPopup': function (featureInfo, latlng) {
            let result = {
                "name": "",
                "classname": "",
                "area": 0,
                "percentage": 0,
            };
            let viewConfig={};
            viewConfig.click = { when: new Date(), where: latlng };
            let value, fProperties;
            feature=featureInfo.features[0].properties;
            for (let i in fProperties) {
                let v=fProperties[i];
                value= isNaN(v) ? v : parseFloat(v);
                viewConfig.click[i] = isNaN(v) ?  value.replace(/ /g, "|"): value;
                if (i in result) {
                    result[i] = isNaN(value) ? value : ams.Utils.numberFormat(value);
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

        '_formatDeterPopup': function(featureInfo) {
            let value, fProperties, result={};
            feature=featureInfo.features[0].properties;

            for (let i in fProperties) {
                let v=fProperties[i];
                value= isNaN(v) ? v : parseFloat(v);
                if (i in result) {
                    result[i] = isNaN(value) ? value : ams.Utils.numberFormat(value);
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