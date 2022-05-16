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
    },

    changeDate: function(date){
        if(typeof date!='undefined')
            ams.App._dateControl.setPeriod(date, ams.App._currentTemporalAggregate);
        ams.App._suViewParams.updateDates(ams.App._dateControl);
        ams.App._priorViewParams.updateDates(ams.App._dateControl);
        ams.App._updateSpatialUnitLayer();
        ams.App._updateReferenceLayer();
        let startdate= new Date(ams.App._dateControl.startdate + "T00:00:00");
        $('#datepicker-start').datepicker().val(startdate.toLocaleDateString("pt-BR"));
        let enddate= new Date(ams.App._dateControl.enddate + "T00:00:00");
        /**
         * Change the end date just to display the value
         * as the range in the compare filter uses "is greater than this date",
         * so it doesn't include that day's data
         */
        enddate.setUTCDate(enddate.getUTCDate()+1);
        $('#datepicker-end').datepicker().val(enddate.toLocaleDateString("pt-BR"));
        // if no have more periods, disable the next button
        if(ams.App._dateControl.hasNext(ams.App._dateControl.getNext())){
            $('#next-period').css('visibility','unset');
        }else{
            $('#next-period').css('visibility','hidden');
        }
    },

    previousPeriod: function(){
        ams.App._dateControl.toPrevious();
        this.changeDate();
    },

    nextPeriod: function(){
        ams.App._dateControl.toNext();
        this.changeDate();
    }
};