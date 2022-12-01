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

        'showFeatureInfo': function (latlng, jsonTxt) {
            if(jsonTxt.includes("no features were found")) {
                $('.toast').toast('show');
			    $('.toast-body').html("Sem informações para este local.");
                return;
            }
            let featureInfo = JSON.parse(jsonTxt);
            let htmlInfo="",name="",type="";
            if(featureInfo.numberReturned>=1){
                if (this._isDeterInfo()) {
                    name="DETER";
                    type="deter";// used to controls
                    htmlInfo=this._formatDeterPopup(featureInfo);
                }else if (this._isAFInfo()) {
                    name="Queimadas";
                    type="af";// used to controls
                    htmlInfo=this._formatAFPopup(featureInfo);
                }else{
                    name="Unidade Espacial";
                    type="su";// used to controls
                    htmlInfo=this._formatSpatialUnitPopup(featureInfo);
                }

                ams.Map.PopupControl._infoBody.push({type:type,name:name,htmlInfo:htmlInfo});
                let htmlPopup=this._accordionFormat();

                if(ams.Map.PopupControl._popupReference && ams.Map.PopupControl._popupReference._popup){
                    ams.Map.PopupControl._popupReference._popup.setContent(htmlPopup);
                }else{
                    ams.Map.PopupControl._popupReference=this._map.openPopup(htmlPopup, latlng);
                    ams.Map.PopupControl._popupReference.on('popupclose', ()=>{
                        ams.Map.PopupControl._infoBody=[];
                    });
                }
            }
        },

        '_accordionFormat': function(){

            let ac='<div id="accordion">';
            for (let id in ams.Map.PopupControl._infoBody){
                let body=ams.Map.PopupControl._infoBody[id];
                ac=ac+
                '<div class="card">'+
                '    <div class="card-header">'+
                '    <a class="'+( body.type=='su'?'':'collapsed ' )+'card-link" data-toggle="collapse" href="#collapse'+id+'">'+
                '        '+body.name+
                '    </a>'+
                '    </div>'+
                '    <div id="collapse'+id+'" class="collapse'+( body.type=='su'?' show':'' )+'" data-parent="#accordion">'+
                '    <div class="card-body">'+
                '        '+body.htmlInfo+
                '    </div>'+
                '    </div>'+
                '</div>';
            }
            ac=ac+'</div>';
            return ac;
        },

        '_isDeterInfo': function () {
            return this._overlay.wmsParams.layers.includes(ams.Config.defaultLayers.deter);
        },

        '_isAFInfo': function () {
            return this._overlay.wmsParams.layers.includes(ams.Config.defaultLayers.activeFire);
        },

        '_updateResults': function(result, featureInfo) {
            let fProperties=featureInfo.features[0].properties;
            for (let i in fProperties) {
                let v = ((fProperties[i]==null || fProperties[i]=="")?("-"):(fProperties[i]));
                if (i in result){
                    // swap area unit from km² to ha
                    if (i=="area" && ams.Map.PopupControl._unit=='ha') {
                        v=v*100;
                        result["area_unit"]=ams.Map.PopupControl._unit;
                    }
                    result[i] = isNaN(v) ? v : ams.Utils.numberFormat(v);
                }
            }
        },

        '_formatSpatialUnitPopup': function (featureInfo) {
            let result = {
                "name": "",
                "classname": "",
                "area": 0,
                "counts": 0,
                "percentage": 0,
                "area_unit": "km²"
            };
            this._updateResults(result, featureInfo);
            let sButton = "";
            if(result.area!=0){
                sButton = this._createGraphicButton(result.name);
            }
            return this._createSpatialUnitInfoTable(result) + sButton;
        },

        '_formatClassName': function (acronym) {
            return acronym != "null" ? this._deterClassGroups.getGroupName(acronym) : " ";
        },

        '_getViewConfig': function (suName) {
            // if it is a Municipality name then it can have spaces between the parts of the name.
            // In this case, we replaced the spaces with pipe to ensure server-side correctness.
            let n=suName.replace(/ /g, "|");
            let conf={};
            conf["className"]=ams.App._suViewParams.classname;
            conf["spatialUnit"]=ams.App._currentSULayerName.split(":")[1];
            conf["startDate"]=ams.App._dateControl.startdate;
            conf["tempUnit"]=ams.App._currentTemporalAggregate;
            conf["suName"]=n;
            return conf;
        },

        '_createGraphicButton': function (suName) {
            let viewConfig=this._getViewConfig(suName);
            let sButton=
                  '<div style="width:100%;display:flex;justify-content:space-between;">'
                + '<button class="btn btn-primary-p btn-success" onclick=ams.App.displayGraph('  // see app.js
                + JSON.stringify(viewConfig)
                + ')>Perfil</button>'
                + '</div>';
            return sButton;
        },
        '_createSpatialUnitInfoTable': function (result) {
            let focus=deter="";
            if(result["classname"]=="AF"){
                focus=""
                + "<tr>"
                + "<td>Focos (unidades)   </td>"
                + "<td>" + result["counts"] + "</td>"
                + "</tr>";
            }else{
                deter=""
                + "<tr>"
                + "<td>&#193;rea ("+result["area_unit"]+")</td>"
                + "<td>" + result["area"] + "</td>"
                + "</tr>"
                + "<tr>"
                + "<td>Porcentagem   </td>"
                + "<td>" + result["percentage"] + "%</td>"
                + "</tr>";
            }
            return '<table class="popup-spatial-unit-table">'
                + "<tr>"
                + "<th>Nome</th>"
                + "<th>Valor</th>"
                + "</tr>"
                + "<tr>"
                + "<td>Unidade Espacial   </td>"
                + "<td style='text-align-last: center;'>" + result["name"] + "</td>"
                + "</tr>"
                + "<tr>"
                + "<td>Classe   </td>"
                + "<td>" + this._formatClassName(result["classname"]) + "</td>"
                + "</tr>"
                + focus
                + deter
            +"</table>";
        },

        '_formatAFPopup': function(featureInfo) {
            let result = {
                "diasemchuva": 0,
                "estado": "",
                "municipio": "",
                "precipitacao": 0,
                "riscofogo": 0,
                "satelite": "",
                "view_date": ""
            };
            this._updateResults(result, featureInfo);
			return this._createAFInfoTable(result);
		},

        '_createAFInfoTable': function(result) {
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
                table += "<tr>"
                + "<td>" + k + "  </td>"
                + "<td>" + (v != "null" ? v : " ") + "</td>"
                + "</tr>";
			}
			table += "<tr><td colspan='2'><a target='_blank' href='"+ams.Config.AFMetadataURL+"'>Ver detalhes dos atributos</a></td></tr>";
			table += "</table>"
			return table;
		},

        '_formatDeterPopup': function(featureInfo) {
            let result = {
                "classname": "",
                "view_date": "",
                "areamunkm": 0,
                "areatotalkm": 0,
                "areauckm": 0,
                "municipality": "",
                "ncar_ids": null,
                "uc": null,
                "uf": "",
                "car_imovel": null,
                "continuo": "",
                "deltad": 0,
                "dominio": "",
                "est_fund": "",
                "ncar_ids": null,
                "tp_dominio": "",
                "velocidade": 0
            };
            this._updateResults(result, featureInfo);
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
			"<textarea name='listcars' rows='2' cols='40' readonly "+
			"style='resize: none;max-width: fit-content;border:0;font-size:xx-small;'>"+
			ids+"</textarea></div>";
		}
    })
};