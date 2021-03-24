import datetime
from ams.utils import DatetimeUtils


def previous_month_assert(startdate, isoformat):
	previous_month_date = DatetimeUtils.previous_month(startdate)
	assert previous_month_date.isoformat() == isoformat

def test_previous_month():
	previous_month_assert(datetime.date(2021, 3, 18), '2021-02-18')
	previous_month_assert(datetime.date(2021, 3, 31), '2021-02-28')
	previous_month_assert(datetime.date(2021, 2, 28), '2021-01-31')
	previous_month_assert(datetime.date(2021, 2, 1), '2021-01-01')
	previous_month_assert(datetime.date(2021, 1, 1), '2020-12-01')
