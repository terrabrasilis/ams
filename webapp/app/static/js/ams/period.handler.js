var ams = ams || {};

ams.PeriodHandler = {
    _startdate: null,
    _enddate: null,
    _control: null,

    init: function(map, startDate){
        this._startdate=startDate;
        this._control = L.control.PeriodHandler({
            startDate:startDate
        }).addTo(map);
        this._control._setDatepicker();
    }
};