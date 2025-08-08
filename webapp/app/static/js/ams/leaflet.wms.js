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
            // Invoke createOverlay on leaflet.wms.js lib
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
                } else if (this._isIbamaRKInfo()) {
                    name = "Risco de Desmatamento";
                    type = "risk";
                    htmlInfo = this._formatIbamaRiskPopup(featureInfo);
                } else if (this._isInpeRKInfo()) {
                    name = "Risco de Desmatamento";
                    type = "risk";
                    htmlInfo = this._formatInpeRiskPopup(featureInfo);
                } else {
                    name="Unidade Espacial";
                    type="su";// used to controls
                    htmlInfo=this._formatSpatialUnitPopup(featureInfo);
                }

                if (type != "" && name != "" && htmlInfo != ""){
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
            }   }
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
        '_isIbamaRKInfo': function () {
            if (ams.Config.defaultRiskFilter.source === "inpe") {
                return false;
            }            
            var rkLayer = ams.Config.defaultLayers.ibamaRisk;
            return this._overlay.wmsParams.layers.includes(rkLayer);
        },
        '_isInpeRKInfo': function () {
            if (ams.Config.defaultRiskFilter.source !== "inpe") {
                return false;
            }
            var rkLayer = ams.Config.defaultLayers.inpeRisk;
            return this._overlay.wmsParams.layers.includes(rkLayer);
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

                    if (i=="score") {
                        v = v / ams.Config.defaultRiskFilter.scaleFactor;
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
                "area_unit": "km²",
                "suid": "",
                "score": 0
            };
            this._updateResults(result, featureInfo);

            let buttons = this._createButtons(result);

            return this._createSpatialUnitInfoTable(result) + buttons;
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

            if (conf["tempUnit"] === "custom") {
                conf["tempUnit"] = ams.App._dateControl.customDays + "d";
                conf["custom"] = true;
            }
            
            conf["suName"]=n;
            conf["landUse"]=ams.App._landUseList.join(',');
            conf["targetbiome"]=ams.Config.biome;
            conf["municipalitiesGroup"]=encodeURIComponent(ams.App._municipalitiesGroup);
            conf["geocodes"]=ams.App._geocodes.join(',');

            return conf;
        },

        '_createButtons': function (result) {
            let suName = result.name;
            let suId = result.suid;
            let area = result.area;
            let classname = result.classname;
            let viewConfig = this._getViewConfig(suName);

            let buttons = '<div class="button-container">';

            if (area!=0) {
                buttons +=
                    '<button class="btn btn-primary-p btn-success" style="margin:1px" onclick=ams.App.displayGraph('  // see app.js
                    + JSON.stringify(viewConfig)
                    + ')>Perfil</button>';

                if (["DS", "DG", "CS", "MN", "AF"].includes(classname)) {
                    let buttonName =  (classname === "AF") ? "Salvar focos" : "Salvar alertas";
                    buttons +=
                        '<button class="btn btn-primary-p btn-success" style="margin:1px" onclick=ams.App.saveIndicators('  // see app.js
                        + JSON.stringify(viewConfig)
                        + ')>'+ buttonName + '</button>';
                }
            }

            if (
                ams.App._currentSULayerName.includes("municipalities") &&
                ams.Utils.getServerConfigParam('municipality-panel') === undefined
            ) {
                buttons +=
                    '<button class="btn btn-primary-p btn-success" style="margin:1px" onclick=ams.App.startMunicipalityPanel('
                    + '"id",'
                    + suId
                    + ')>Sala de Situa&ccedil;&atilde;o Municipal</button>';
            }

            buttons += '</div>'

            return buttons;
        },

        '_createSpatialUnitInfoTable': function (result) {
            let risk=focus=deter="";
            if(result["classname"]=="AF"){
                focus=""
                + "<tr>"
                + "<td>Focos (unidades)   </td>"
                + "<td>" + result["counts"] + "</td>"
                + "</tr>";
            }
            else if(result["classname"]=="RK"){
                risk=""
                + "<tr>"
                + "<td>Riscos (unidades)   </td>"
                + "<td>" + result["counts"] + "</td>"
                + "</tr>";    
            }
            else if(result["classname"]=="RI"){
                risk=""
                + "<tr>"
                + "<td>Risco (intensidade) </td>"
                + "<td>" + result["score"] + "</td>"
                + "</tr>";    
            }
            else {
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
                + risk
                + focus
                + deter
            +"</table>";
        },

        '_formatIbamaRiskPopup': function(featureInfo) {
            let result = {
                "id": 0,
                "risk": 0,
                "risk_date": "",
            }
            this._updateResults(result, featureInfo);
            return this._createRiskInfoTable(result);
        },

        '_formatInpeRiskPopup': function(featureInfo) {
            let result = {
                "id": 0,
                "risk": 0,
                "risk_date": "",
                "score": 10,
            }
            this._updateResults(result, featureInfo);
            return this._createRiskInfoTable(result);
        },

        '_createRiskInfoTable': function(result) {
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
                table += "<tr>"
                + "<td>" + k + "  </td>"
                + "<td>" + (v != "null" ? v : " ") + "</td>"
                + "</tr>";
            }
            table += "</table>"
            return table;
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
                "uc": null,
                "uf": "",
                "biome": "",
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
