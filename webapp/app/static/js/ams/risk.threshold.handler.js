var ams = ams || {};

ams.RiskThresholdHandler = {
    _sliderRange: [],
    _control: null,
    _date: null,

    init: function(map){
        this._sliderRange=ams.Config.risk.range;
        this._date = ams.RiskThresholdHandler.getLastRiskDate(dateLabel);
        if(!this._control) {
            this._control = L.control.RiskThresholdHandler({
                range: this._sliderRange,
                date: this._date
            });
        }
        this._control.addTo(map);
        // restart to initial range value
        this._control._highlightSelectedLabel(this._sliderRange[0]);
        this._control._updateStatusAndDateLabel(this._date)
    },

    remove: function(map) {
        if(this._control){
            map.removeControl(this._control);
            this._control=null;
        }
    },

    getLastRiskDate: function(lastRiskDate){           
        dateLabel = lastRiskDate;
        return dateLabel;
    },

    onChange: function(){
        // to keep updated infos on UI and return the selected value
        ams.App._riskThreshold=this._control._onInputChange();
        ams.App._suViewParams.updateRiskThreshold(ams.App._riskThreshold);
        ams.App._updateSpatialUnitLayer();
    }
};