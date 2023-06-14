var ams = ams || {};

ams.RiskThresholdHandler = {
    _sliderRange: [0, 0.35, 0.85, 1],
    _control: null,

    init: function(map){
        if(this._control) return;
        
        this._control = L.control.RiskThresholdHandler({
            range:this._sliderRange
        }).addTo(map);
        // restart to initial range value
        this._control._highlightSelectedLabel(this._sliderRange[0]);
    },

    remove: function(map) {
        if(this._control){
            map.removeControl(this._control);
            this._control=null;
        }
    },

    onChange: function(){
        this._control._onInputChange();
    }
};