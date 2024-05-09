/*
 * L.Control.WMSLegend is used to add a WMS Legend to the map
 */

L.Control.WMSLegend = L.Control.extend({
    options: {
        position: 'middleright',
        uri: '',
        static:{
            deter:{
                url:''
            },
            af:{
                url:''
            },
            risk:{
                url:''
            }
        }
    },

    onAdd: function () {
        let controlClassName = 'leaflet-control-wms-legend',
            legendClassName = 'wms-legend';
        this.fcontainer = L.DomUtil.create('div', 'leaflet-control-legend');
        this.ll = L.DomUtil.create('span', 'label-legend', this.fcontainer);
        this.ll.innerText='LEGENDA';
        let container = L.DomUtil.create('div', controlClassName, this.fcontainer);
        // static deter legend
        if(this.options.static.deter.url){
            let ldl = L.DomUtil.create('span', 'wms-label-legend', container);
            ldl.innerText='DETER';
            let dl = L.DomUtil.create('img', legendClassName, container);
            dl.src = this.options.static.deter.url;
            dl.alt = 'DETER Legend';
        }
        // static active fires legend
        if(this.options.static.af.url){
            let lafl = L.DomUtil.create('span', 'wms-label-legend', container);
            lafl.innerText='Focos de Queimadas';
            let afl = L.DomUtil.create('img', legendClassName, container);
            afl.src = this.options.static.af.url;
            afl.alt = 'Active Fires Legend';
        }
        // static risk legend
        if(this.options.static.risk.url){
            let lafl = L.DomUtil.create('span', 'wms-label-legend', container);
            lafl.innerText='Risco de desmatamento (IBAMA)';
            let afl = L.DomUtil.create('img', legendClassName, container);
            afl.src = this.options.static.risk.url;
            afl.alt = 'IBAMA Risk Legend';
        }
        // dinamic spatial unit legend
        let limg = L.DomUtil.create('span', 'wms-label-legend', container);
        limg.innerText=ams.Map.PopupControl._prefix+ams.Map.PopupControl._text;
        this.img = L.DomUtil.create('img', legendClassName, container);
        this.img.src = this.options.uri;
        this.img.alt = 'Spatial Unit Legend';

        let stop = L.DomEvent.stopPropagation;
        L.DomEvent
            .on(this.fcontainer, 'click', this._click, this)
            .on(this.ll, 'click', this._click, this)
            .on(this.img, 'click', this._click, this)
            .on(container, 'click', this._click, this)
            .on(this.img, 'mousedown', stop)
            .on(this.img, 'dblclick', stop)
            .on(this.img, 'click', L.DomEvent.preventDefault)
            .on(this.img, 'click', stop);
        this.height = null;
        this.width = null;
        this.container=container;
        return this.fcontainer;
    },
    _click: function (e) {
        L.DomEvent.stopPropagation(e);
        L.DomEvent.preventDefault(e);
        // toggle legend visibility
        var style = window.getComputedStyle(this.container);
        if (style.display === 'none') {
            this.fcontainer.style.height = this.height + 'px';
            this.fcontainer.style.width = this.width + 'px';
            this.container.style.display = this.displayStyle;
            this.ll.style.display = 'none';
        }
        else {
            if (this.width === null && this.height === null) {
                // Only do inside the above check to prevent the container
                // growing on successive uses
                this.height = this.fcontainer.offsetHeight;
                this.width = this.fcontainer.offsetWidth;
            }
            this.displayStyle = this.container.style.display;
            this.container.style.display = 'none';
            this.ll.style.display = 'inline';
            this.fcontainer.style.height = 'fit-content';
            this.fcontainer.style.width = '20px';
        }
    },
});

L.wmsLegend = function (uri) {
    var wmsLegendControl = new L.Control.WMSLegend;
    wmsLegendControl.options.uri = uri;
    map.addControl(wmsLegendControl);
    return wmsLegendControl;
};
