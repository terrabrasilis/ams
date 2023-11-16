var ams = ams || {};

ams.RiskThresholdHandler = {
    _sliderRange: [],
    _control: null,
    _date: null,

    init: function(map){
        this._sliderRange=ams.Config.risk.range;           
        if(!this._control) {
            this._control = L.control.RiskThresholdHandler({
                range: this._sliderRange,
                date: this._date
            });
        }
        this._control.addTo(map);
        // restart to initial range value
        this._control._highlightSelectedLabel(this._sliderRange[0]);        
    },

    remove: function(map) {
        if(this._control){
            map.removeControl(this._control);
            this._control=null;
        }
    },

    setLastRiskDate: function(lastRiskDate){ 
        this._date = lastRiskDate;  
    },

    onChange: function(){
        // to keep updated infos on UI and return the selected value
        ams.App._riskThreshold=this._control._onInputChange();
        ams.App._suViewParams.updateRiskThreshold(ams.App._riskThreshold);
        ams.App._priorViewParams.updateRiskThreshold(ams.App._riskThreshold);
        ams.App._updateSpatialUnitLayer();
    }
};