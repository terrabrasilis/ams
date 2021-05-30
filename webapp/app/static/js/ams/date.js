var ams = ams || {};

ams.Date = {
	DateController: function() {
		this.startdate;
		this.enddate;
		this.prevdate;

		this.toUTCDate = function(date) {
			let uday = date.getUTCDate();
			let day = uday < 10 ? "0" + uday : uday;
			let umonth = date.getUTCMonth() + 1;
			let month = umonth < 10 ? "0" + umonth : umonth;
			return `${date.getUTCFullYear()}-${month}-${day}`; 
		}

		this.isLastDay =function(date) {
			let last = new Date(date);
			let month = date.getMonth();
			last.setDate(last.getDate() + 1);
			return last.getMonth() != month;
		}

		this.setPeriod = function(startdate, period) {
			this.startdate = startdate;
			let sdate = new Date(startdate + "T00:00:00");
			let enddate = new Date(sdate);
			let prevdate = new Date(sdate);
			if(period == "7d") {
				enddate.setUTCDate(enddate.getUTCDate() - 7);
				prevdate.setUTCDate(prevdate.getUTCDate() - 14);
			}			
			else if(period == "15d") {
				enddate.setUTCDate(enddate.getUTCDate() - 15);
				prevdate.setUTCDate(prevdate.getUTCDate() - 30);
			}
			else if(period == "1m") {
				enddate.setUTCDate(0);
				prevdate.setUTCDate(0);
				prevdate.setUTCDate(0);				
				if(!this.isLastDay(sdate)) {
					let day = sdate.getUTCDate();
					prevdate.setUTCDate(day);
					enddate.setUTCDate(day);
				}
			}
			else if(period == "3m") {
				if(this.isLastDay(sdate)) {
					enddate.setUTCDate(enddate.getUTCDate() - 2*32);
					enddate.setUTCDate(0);
					prevdate.setUTCDate(prevdate.getUTCDate() - 5*32);
					prevdate.setUTCDate(0);
				}
				else {
					let day = enddate.getUTCDate();
					enddate.setUTCDate(enddate.getUTCDate() - 2*32);
					prevdate.setUTCDate(prevdate.getUTCDate() - 5*32);
					enddate.setUTCDate(day);
					prevdate.setUTCDate(day);
				}
			}			
			else if(period == "1y") {
				enddate.setUTCFullYear(enddate.getUTCFullYear() - 1);
				prevdate.setUTCFullYear(prevdate.getUTCFullYear() - 2);					
				if(this.isLastDay(sdate) && (sdate.getUTCMonth() == 1)) {
					let month = sdate.getUTCMonth() + 1;
					enddate.setUTCMonth(month);
					prevdate.setUTCMonth(month);					
					enddate.setUTCDate(0);
					prevdate.setUTCDate(0);			
				}
			}						
			this.enddate = this.toUTCDate(enddate);
			this.prevdate = this.toUTCDate(prevdate);
		}
	}
};

if(typeof module !== 'undefined') {
	module.exports.ams = ams;
	module.exports.ams.Date.DateController = ams.Date.DateController;
}