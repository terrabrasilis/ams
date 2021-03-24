import datetime
import calendar
# from pandas import Period


class DatetimeUtils:
	"""DatetimeUtils"""
	
	@staticmethod
	def previous_month(currentdate: datetime.date) -> datetime.date:
		day = currentdate.day
		prevmonth_last_day = currentdate.replace(day=1) - datetime.timedelta(days=1) 
		if DatetimeUtils.is_last_day(currentdate):
			return prevmonth_last_day
		prevmonth = prevmonth_last_day.replace(day=day)
		return prevmonth

	@staticmethod	
	def is_last_day(date: datetime.date) -> bool:
		last_day_of_month = calendar.monthrange(date.year, date.month)[1]
		return last_day_of_month == date.day
