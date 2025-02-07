# -*- coding: utf-8 -*-
import json
from pathlib import Path

from flask_caching import Cache

cache = Cache()


def init_cache(app):
    print("init cache")

    Path('./cache').mkdir(exist_ok=True)

    app.config['CACHE_TYPE'] = 'filesystem'
    app.config['CACHE_DIR'] = './cache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 60  # 86400  # a day

    cache.init_app(app)


@cache.cached()
def get_globals():
    return {"key1": "name1"}
