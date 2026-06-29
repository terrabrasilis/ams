/* global L */

// A period control dedicated to PRODES year selection.
// It can work in single-year mode or in year-range mode.
L.Control.ProdesPeriodHandlerControl = L.Control.extend({

    options: {
        position: 'bottomcenter',
        autoZIndex: true,
        minYear: null,
        maxYear: null,
        startYear: null,
        endYear: null,
        mode: 'range', // 'range' or 'single'
    },

    _container: null,
    _map: null,
    _startSelect: null,
    _endSelect: null,

    initialize: function (options) {
        L.Util.setOptions(this, options);
        this._normalizeOptions();

        if (this.options.mode == 'single') {
            this._setSingleYear(this.options.startYear);
            return;
        }

        this._setRange(this.options.startYear, this.options.endYear);
    },

    _normalizeOptions: function () {
        let minYear = parseInt(this.options.minYear, 10);
        let maxYear = parseInt(this.options.maxYear, 10);
        let startYear = parseInt(this.options.startYear, 10);
        let endYear = parseInt(this.options.endYear, 10);

        ams.Utils.assert(maxYear > minYear, 'maxYear > minYear is mandatory.');

        if (isNaN(startYear)) {
            startYear = minYear;
        }

        if (isNaN(endYear)) {
            endYear = maxYear;
        }

        startYear = Math.max(minYear, Math.min(startYear, maxYear));
        endYear = Math.max(minYear, Math.min(endYear, maxYear));

        if (this.options.mode === 'single') {
            endYear = startYear;
        } else if (startYear > endYear) {
            endYear = startYear;
        }

        this.options.minYear = minYear;
        this.options.maxYear = maxYear;
        this.options.startYear = startYear;
        this.options.endYear = endYear;
    },

    _buildYearSelect: function (className, selectedYear) {
        let select = L.DomUtil.create('select', className);

        for (let year = this.options.minYear; year <= this.options.maxYear; year++) {
            let option = document.createElement('option');
            option.value = year;
            option.text = year;
            option.selected = (year === selectedYear);
            select.appendChild(option);
        }

        return select;
    },

    _initLayout: function (map) {
        this._map = map;

        let className = 'leaflet-prodes-period-control';
        let container = L.DomUtil.create('div', className);
        let info = L.DomUtil.create('div',
            'leaflet-period-control-form leaflet-period-control-info',
            container
        )
        info.innerHTML = ' Controle da unidade temporal ';
     
        let form = L.DomUtil.create('div', 'leaflet-period-control-form', container);

        let label = L.DomUtil.create('span', 'period-control', form);
        label.innerText = 'PRODES: ';

        this._startSelect = this._buildYearSelect(
            className + '-year-select ' + className + '-start-year',
            this.options.startYear
        );
        form.appendChild(this._startSelect);

        if (this.options.mode === 'range') {
            let separator = L.DomUtil.create('span', 'period-control', form);
            separator.innerText = ' até ';

            this._endSelect = this._buildYearSelect(
                className + '-year-select ' + className + '-end-year',
                this.options.endYear
            );
            form.appendChild(this._endSelect);
        } else {
            this._endSelect = null;
        }

        $(container).mouseenter(function () {
            map.dragging.disable();
            map.scrollWheelZoom.disable();
            map.doubleClickZoom.disable();
        });

        $(container).mouseleave(function () {
            map.dragging.enable();
            map.scrollWheelZoom.enable();
            map.doubleClickZoom.enable();
        });

        if (L.Browser.touch) {
            L.DomEvent.on(container, 'click', L.DomEvent.stopPropagation);
        } else {
            L.DomEvent.disableClickPropagation(container);
            L.DomEvent.on(container, 'wheel', L.DomEvent.stopPropagation);
        }

        L.DomEvent.on(this._startSelect, 'change', this._onStartYearChange, this);
        if (this._endSelect) {
            L.DomEvent.on(this._endSelect, 'change', this._onEndYearChange, this);
        }

        this._container = container;
    },

    _readSelectedYear: function (select) {
        return parseInt(select.value, 10);
    },

    _emitChange: function () {
        ams.ProdesPeriodHandler.changeDate(this.getSelection());
    },

    _onStartYearChange: function () {
        let startYear = this._readSelectedYear(this._startSelect);

        if (this.options.mode === 'range' && this._endSelect) {
            let endYear = this._readSelectedYear(this._endSelect);

            if (startYear > endYear) {
                endYear = startYear;
                this._endSelect.value = String(endYear);
            }

            this.options.startYear = startYear;
            this.options.endYear = endYear;
        } else {
            this.options.startYear = startYear;
            this.options.endYear = startYear;
        }

        this._emitChange();
    },

    _onEndYearChange: function () {
        if (!this._endSelect) {
            return;
        }

        let endYear = this._readSelectedYear(this._endSelect);
        let startYear = this._readSelectedYear(this._startSelect);

        if (endYear < startYear) {
            startYear = endYear;
            this._startSelect.value = String(startYear);
        }

        this.options.startYear = startYear;
        this.options.endYear = endYear;

        this._emitChange();
    },

    getSelection: function () {
        return {
            mode: this.options.mode,
            startYear: this.options.startYear,
            endYear: this.options.endYear
        };
    },

    _setRange: function (startYear, endYear) {
        this.options.mode = 'range';
        this.options.startYear = parseInt(startYear, 10);
        this.options.endYear = parseInt(endYear, 10);

        if (this._startSelect) {
            this._startSelect.value = String(this.options.startYear);
        }
        if (this._endSelect) {
            this._endSelect.value = String(this.options.endYear);
        }
    },

    _setSingleYear: function (year) {
        this.options.mode = 'single';
        this.options.startYear = parseInt(year, 10);
        this.options.endYear = this.options.startYear;

        if (this._startSelect) {
            this._startSelect.value = String(this.options.startYear);
        }
    },

    onAdd: function (map) {
        this._initLayout(map);
        return this._container;
    },

    onRemove: function () {
        if (this._startSelect) {
            L.DomEvent.off(this._startSelect, 'change', this._onStartYearChange, this);
        }
        if (this._endSelect) {
            L.DomEvent.off(this._endSelect, 'change', this._onEndYearChange, this);
        }

        this._startSelect = null;
        this._endSelect = null;
        delete this._container;
        this._container = null;
    }
});

L.control.ProdesPeriodHandlerControl = function (options) {
    return new L.Control.ProdesPeriodHandlerControl(options);
};
