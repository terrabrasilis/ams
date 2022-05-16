var ams = ams || {};

ams.Date = {
	DateController: function() {
		this.startdate;
		this.enddate;
		this.prevdate;
		this.period;
		this.maxdate;// the max date to control the period navigation

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
			return numDays;
		}

		this.setPeriod = function(startdate, period) {
			this.period=period;
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
	}
};

if(typeof module !== 'undefined') {
	module.exports.ams = ams;
	module.exports.ams.Date.DateController = ams.Date.DateController;
}