var ams = ams || {};

ams.Date = {
    DateController: function() {
        this.startdate;
        this.enddate;
        this.prevdate;
        this.period;
        this.maxdate;  // the max date to control the period navigation
        this.customDays=0;  // number of days for custom period
        
        this.toNext = function() {
            let nextdate=this.getNext();
            if(this.hasNext(nextdate)){
                this.setPeriod(this.toUTCDate(nextdate), this.period);
            }
        }
        
        this.getNext = function() {
            let numDays=this.getNumberOfDays();
            let sdate = new Date(this.startdate + "T00:00:00");
            let nextdate = new Date(sdate);
            nextdate.setUTCDate(sdate.getUTCDate() + numDays);
            return nextdate;
        }

        this.hasNext = function(refdate) {
            return this.maxdate && refdate<=this.maxdate;
        }
        
        this.toPrevious = function() {
            if(!this.maxdate)
                this.maxdate=new Date(this.startdate + "T00:00:00");
            this.setPeriod(this.enddate, this.period);
        }

        this.toUTCDate = function(date) {
            let uday = date.getUTCDate();
            let day = uday < 10 ? "0" + uday : uday;
            let umonth = date.getUTCMonth() + 1;
            let month = umonth < 10 ? "0" + umonth : umonth;
            return `${date.getUTCFullYear()}-${month}-${day}`; 
        }

        this.getNumberOfDays = function(){
            let numDays=0;
            if(this.period == "7d") {
                numDays=7;
            }            
            else if(this.period == "15d") {
                numDays=15;
            }
            else if(this.period == "1m") {
                numDays=30;
            }
            else if(this.period == "3m") {
                numDays=90;
            }            
            else if(this.period == "1y") {
                numDays=365;
            }
            else if(this.period == "custom") {
                numDays=this.customDays;
            }
            return numDays;
        }
        
        this.getPeriodByDays = function(numdays){
            let period;

            if (this.period === "custom") {
                return this.period;
            }
            
            switch(numdays) {
            case 7:
                period='7d';
                break;
            case 15:
                period='15d';
                break;
            case 30:
                period='1m';
                break;
            case 90:
                period='3m';
                break;
            case 365:
                period='1y';
                break;
            default:
                period = '7d';
            }
            return period;
        }

        this.setPeriod = function(date, period, datetype) {
            this.period = period;

            if (period === "custom" && datetype !== undefined) {
                // In the custom period mode the end date is defined by user. So, isn't necessary to compute
                if (datetype == "start") {
                    this.setCustomPeriod(date, this.enddate, 1);
                } else {
                    this.setCustomPeriod(this.startdate, date, 1);
                }
                return;
            }
            
            startdate = date;
            
            this.startdate = startdate;
            let sdate = new Date(startdate + "T00:00:00");
            let enddate = new Date(sdate);
            let prevdate = new Date(sdate);
            
            let numDays=this.getNumberOfDays();
            enddate.setUTCDate(enddate.getUTCDate() - numDays);
            prevdate.setUTCDate(prevdate.getUTCDate() - 2*numDays);
            
            // set to display
            this.enddate = this.toUTCDate(enddate);
            this.prevdate = this.toUTCDate(prevdate);
        }

        this.setCustomPeriod = function(startdate, enddate, incDays=0) {
            ams.Utils.assert(typeof(startdate) === "string");
            ams.Utils.assert(typeof(enddate) === "string");

            startdate = ams.Date.fromString(startdate);
            enddate = ams.Date.fromString(enddate);
            
            this.period = "custom";
            this.customDays = ams.Date.differenceInDays(startdate, enddate) - incDays;

            this.startdate = this.toUTCDate(startdate);
            this.enddate = this.toUTCDate(enddate);

            let prevdate = enddate;
            prevdate.setUTCDate(prevdate.getUTCDate() - this.customDays);
            this.prevdate = this.toUTCDate(prevdate);
        }        

        this.disableCustomPeriod = function() {
            this.period = null;
            this.customDays = null;
        }

        this.getPeriod = function() {
            return this.period;
        }
    },

    /**
     * Convert a date string in the specified format to a Date object.
     */
    fromString: function(dateStr, format="yyyy-mm-dd") {
        ams.Utils.assert(["dd/mm/yyyy", "yyyy-mm-dd"].includes(format));
        if (format === "dd/mm/yyyy") {
            let parts = dateStr.split("/");
            return new Date(parts[2] + "-" + parts[1] + "-" + parts[0] + "T00:00:00");
        }
        return new Date(dateStr + "T00:00:00");
    },

    /**
     * Calculate the difference in days between the specified dates
     */
    differenceInDays: function(date1, date2) {
        return Math.round(Math.abs(date1 - date2) / (1000 * 3600 * 24)) + 1;
    },

    /**
     * Add days to the given date.
     */
    addDays: function(date, days) {
        ams.Utils.assert(date instanceof Date);
        date.setUTCDate(date.getUTCDate() + days);
        return ams.Date.DateController.toUTCDate(date);
    },

    getMin: function (dateStr1, dateStr2) {
        var date1 = new Date(dateStr1);
        var date2 = new Date(dateStr2);

        var minDate = date1 < date2 ? date1 : date2;

        return minDate.toISOString().slice(0, 10);
    }

};

if(typeof module !== 'undefined') {
    module.exports.ams = ams;
    module.exports.ams.Date.DateController = ams.Date.DateController;
}
