var ams = ams || {};

ams.PeriodHandler = {
    _startdate: null,// used to display date information
    _enddate: null,// used to display date information
    _previousdate: null,// used to display date information
    _control: null,

    init: function(map){
        this._updatePeriodInfo();// gets start date from App configuration and injects here
        if(!this._control) {
            this._control = L.control.PeriodHandler({
                startDate:this._startdate
            });
        }
        
        this._control.addTo(map);
        this._control._setDatepicker();
    },

    remove: function(map) {
        if(this._control){
            map.removeControl(this._control);
            this._control=null;
        }
    },

    /**
     * Changes the period dates to be used to display
     * information in outputs to the user, in export files for example.
     */
    _updatePeriodInfo: function(){
        this._startdate=new Date(ams.App._dateControl.startdate + "T00:00:00");
        /**
         * Change the end date and previous date just to display the value
         * as the range in the compare filter uses "is greater than this date",
         * so it doesn't include that day's data
         */
        this._enddate=new Date(ams.App._dateControl.enddate + "T00:00:00");
        this._enddate.setUTCDate(this._enddate.getUTCDate()+1);
        this._previousdate=new Date(ams.App._dateControl.prevdate+'T00:00:00');
        this._previousdate.setUTCDate(this._previousdate.getUTCDate()+1);
    },

    changeDate: function(date){
        if(typeof date!='undefined')
            ams.App._dateControl.setPeriod(date, ams.App._currentTemporalAggregate);
        ams.App._suViewParams.updateDates(ams.App._dateControl);
        ams.App._priorViewParams.updateDates(ams.App._dateControl);
        ams.App._updateSpatialUnitLayer();
        ams.App._updateReferenceLayer();
        this._updatePeriodInfo();
        $('#datepicker-start').datepicker().val(this._startdate.toLocaleDateString("pt-BR"));
        $('#datepicker-end').datepicker().val(this._enddate.toLocaleDateString("pt-BR"));
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