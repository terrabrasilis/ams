from contextlib import contextmanager
from flask import template_rendered
from webapp.app.config import Config


class TestConfig(Config):
	TESTING = True
	DATABASE_URL = 'postgresql://postgres:postgres@localhost:5432/ams_webapp'	


# https://stackoverflow.com/questions/39822265/flask-testing-how-to-retrieve-variables-that-were-passed-to-jinja
@contextmanager
def get_context_variables(app):
    recorded = []
    
    def record(sender, template, context, **extra):
        recorded.append(context)
    template_rendered.connect(record, app)
    try:
        yield iter(recorded)
    finally:
        template_rendered.disconnect(record, app)   
