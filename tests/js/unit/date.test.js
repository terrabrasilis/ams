const date = require("../../../webapp/app/static/js/ams/date");

test('Fifteen days period (day 1)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-01-01";
	controll.setPeriod(startdate, "15d");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2020-12-17");
	expect(controll.prevdate).toBe("2020-12-02");
});

test('One month period (day 1)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-01-01";
	controll.setPeriod(startdate, "1m");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2020-12-01");
	expect(controll.prevdate).toBe("2020-11-01");
});

test('One month period (Feb. last day)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-02-28";
	controll.setPeriod(startdate, "1m");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2021-01-31");
	expect(controll.prevdate).toBe("2020-12-31");
});

test('One month period (any given day)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-02-15";
	controll.setPeriod(startdate, "1m");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2021-01-15");
	expect(controll.prevdate).toBe("2020-12-15");
});

test('One year period (day 1)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-01-01";
	controll.setPeriod(startdate, "1y");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2020-01-01");
	expect(controll.prevdate).toBe("2019-01-01");
});

test('One year period (Feb. last day)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-02-28";
	controll.setPeriod(startdate, "1y");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2020-02-29");
	expect(controll.prevdate).toBe("2019-02-28");
});

test('One year period (Feb. 29 days)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2020-02-29";
	controll.setPeriod(startdate, "1y");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2019-02-28");
	expect(controll.prevdate).toBe("2018-02-28");
});

test('One year period (Feb. previous 29 days)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2022-02-28";
	controll.setPeriod(startdate, "1y");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2021-02-28");
	expect(controll.prevdate).toBe("2020-02-29");
});

test('One year period (Jan. last day)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-01-31";
	controll.setPeriod(startdate, "1y");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2020-01-31");
	expect(controll.prevdate).toBe("2019-01-31");
});

test('One year period (any given day)', () => {
	let controll = new date.ams.Date.DateController();
	let startdate = "2021-02-15";
	controll.setPeriod(startdate, "1y");
	expect(controll.startdate).toBe(startdate);
	expect(controll.enddate).toBe("2020-02-15");
	expect(controll.prevdate).toBe("2019-02-15");
});
