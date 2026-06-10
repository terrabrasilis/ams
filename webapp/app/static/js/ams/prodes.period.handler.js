var ams = ams || {};

ams.ProdesPeriodHandler = {
    _control: null,
    _map: null,
    _selection: null,
    _startYear: null,
    _endYear: null,
    _minYear: null,
    _maxYear: null,
    _mode: null,
    _enabled: false,

    init: function (map, minYear, maxYear, startYear, endYear, indicator) {
        this._map = map;
        this._minYear = minYear;
        this._maxYear = maxYear;
        this._startYear = startYear;
        this._endYear = endYear;
        this._mode = indicator == 'AI'? 'range' : 'single';
        this._selection = null;

        // force to recreate the control so option changes are always reflected in the UI.
        if (this._control) {
            map.removeControl(this._control);
            this._control = null;
        }

        let controlOptions = this._buildControlOptions();

        this._control = L.control.ProdesPeriodHandlerControl(controlOptions);
        this._control.addTo(map);

        this._syncFromSelection(this._control.getSelection());

        this._enabled = true;
    },

    remove: function (map) {
        if (this._control) {
            map.removeControl(this._control);
            this._control = null;
        }
        this._map = null;
        this._enabled = false;
        this._selection = null;
        this._startYear = null;
        this._endYear = null;
    },

    isEnabled: function () {
        return this._enabled;
    },

    changeDate: function(selection) {
        this._syncFromSelection(selection);
        
        const startDate = this._startYear-1 + '-12-31';
        const endDate = this._endYear + '-12-31';

        ams.App._dateControl.setCustomPeriod(endDate, startDate);
        ams.App._suViewParams.updateDates(ams.App._dateControl);
        ams.App._priorViewParams.updateDates(ams.App._dateControl);

        if (!ams.App.hasSpatialUnitLayer()) {
            ams.App.addSpatialUnitLayer();
        } else {        
            ams.App._updateSpatialUnitLayer();
        }

        ams.App._updateReferenceLayer();
    },

    update: function () {
        this.changeDate(this._selection);
    },

    _buildControlOptions: function () {
        let selection = this.getSelection();

        return {
            minYear: this._minYear,
            maxYear: this._maxYear,
            startYear: selection.startYear,
            endYear: selection.endYear,
            mode: this._mode,
        };
    },

    _normalizeSelection: function () {
        if (this._startYear === null || isNaN(this._startYear)) {
            if (this._mode === 'single') {
                this._startYear = this._maxYear;
            } else {
                this._startYear = this._minYear;
            }
        }

        if (this._endYear === null || isNaN(this._endYear)) {
            this._endYear = this._maxYear;
        }

        this._selection = this._buildSelection(this._startYear, this._endYear, this._mode);
    },

    _buildSelection: function (startYear, endYear, mode) {
        return {
            mode: mode,
            startYear: startYear,
            endYear: endYear,
        };
    },

    _syncFromSelection: function (selection) {
        let nextSelection = this._buildSelection(selection.startYear, selection.endYear, selection.mode);

        this._mode = nextSelection.mode;
        this._startYear = nextSelection.startYear;
        this._endYear = nextSelection.endYear;
    },

    setRange: function (startYear, endYear) {
        this._mode = 'range';
        this._startYear = parseInt(startYear, 10);
        this._endYear = parseInt(endYear, 10);
        this._normalizeSelection();

        if (this._control) {
            this._control.setRange(this._startYear, this._endYear);
        }
    },

    setSingleYear: function (year) {
        this._mode = 'single';
        this._startYear = parseInt(year, 10);
        this._endYear = this._startYear;
        this._normalizeSelection();

        if (this._control) {
            this._control.setSingleYear(this._startYear);
        }
    },

    setSelection: function (selection) {
        if (!selection) {
            return;
        }

        if (selection.mode === 'single') {
            this.setSingleYear(selection.startYear);
            return;
        }

        this.setRange(selection.startYear, selection.endYear);
    },

    getSelection: function () {
        if (!this._selection) {
            this._normalizeSelection();
        }

        return {
            mode: this._selection.mode,
            startYear: this._selection.startYear,
            endYear: this._selection.endYear,
        };
    },

    onAdd: function (map) {
        this.init(map);
    },

    getMode: function (indicator) {
        if (indicator == 'AI') {
            return 'range';
        }
        return 'single';
    }

};
