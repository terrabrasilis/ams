import logging
from main import app

if __name__ == "__main__":
	app.run()
	# set the loggers for gunicorn
	gunicorn_logger = logging.getLogger('gunicorn.error')
	app.logger.handlers = gunicorn_logger.handlers
	app.logger.setLevel(gunicorn_logger.level)