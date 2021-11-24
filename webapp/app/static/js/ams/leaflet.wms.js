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
            if (this._isSpatialUnitInfo(info)) {
                this._map.openPopup(this._formatSpatialUnitPopup(info, this.viewConfig, latlng) , latlng); //-- mgd T6 this.config
            } else if (this._isDeterInfo(info)) {
                this._map.openPopup(this._formatDeterPopup(info), latlng);
            }
        },

        '_isSpatialUnitInfo': function (info) {
            return info.includes("area") && info.includes("percentage") && info.includes("name");
        },

        '_isDeterInfo': function (info) {
            return info.includes("origin_gid") && info.includes("date_audit");
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
                        result[pair[0]] = isNaN(value) ? value : value.toFixed(5);//isNaN(pair[1]) ? pair[1] : parseFloat(pair[1]).toFixed(5);
                    }
                }
            }
            let sButton = "";
            // -- mlra
            if (viewConfig.click.classname == 'null')
                viewConfig.click.classname = "DS";
            if (viewConfig.click.classname != 'null') {
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
                + '<button onclick= displayGraph('  // see index.html
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
        '_formatDeterPopup': function (str) {
            let tokens = str.split("\n");
            let result = {};
            for (let i = 0; i < tokens.length; i++) {
                let pair = tokens[i].split(" = ");
                if (pair.length > 1) {
                    result[pair[0]] = isNaN(pair[1]) ? pair[1] : parseFloat(pair[1]).toFixed(5);
                }
            }
            delete result["geom"];
            delete result["month_year"];
            delete result["quadrant"];
            return this._createDeterInfoTable(result);
        },
        '_createDeterInfoTable': function (result) {
            let table = '<table class="popup-deter-table" style="width:100%">'
                + "<tr>"
                + "<th></th>"
                + "<th></th>"
                + "</tr>";
            for (let k in result) {
                let v = result[k];
                if (k.includes("date")) {
                    v = this._formatDate(v);
                }
                table += "<tr>"
                    + "<td>" + k + "  </td>"
                    + "<td>" + (v != "null" ? v : " ") + "</td>"
                    + "</tr>"
            }
            table += "</table>"
            return table;
        },
        '_formatDate': function (str) {
            let res = str.replace("Z", "").split("-");
            return `${res[2]}/${res[1]}/${res[0]}`
        }

    })
};