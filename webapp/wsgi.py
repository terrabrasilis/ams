import logging
from main import app

# We check if we are running directly or not
if __name__ == "__main__":
	# here is running from Flask directly
	app.run(host='0.0.0.0', port=7000, debug=True)
else:
	# if we are not running directly, we set the loggers for gunicorn
	gunicorn_logger = logging.getLogger('gunicorn.error')
	app.logger.handlers = gunicorn_logger.handlers
	app.logger.setLevel(gunicorn_logger.level)