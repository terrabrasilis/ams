import os


class Config:
    # used for frontend App
    GEOSERVER_URL = os.environ.get(
        'GEOSERVER_URL') or 'http://terrabrasilis.dpi.inpe.br/geoserver'
    SERVER_NAME = os.environ.get('SERVER_NAME') or '127.0.0.1:5000'
    APPLICATION_ROOT = os.environ.get('APPLICATION_ROOT') or ''
    DB_URL = os.environ.get(
        'DB_URL') or 'postgresql://postgres:postgres@150.163.17.75:5444/AMS4'
    if os.path.exists(DB_URL):
        DB_URL = open(DB_URL, 'r').read()
    RISK_THRESHOLD = (
        float(os.environ.get("RISK_THRESHOLD")) if os.environ.get("RISK_THRESHOLD") else 0.9
    )
    RESET_LOCAL_STORAGE = (
        os.environ.get('RESET_LOCAL_STORAGE').lower() == "true" if os.environ.get('RESET_LOCAL_STORAGE') else False
    )

    @staticmethod
    def get_params_to_frontend():
        """Return a dictionary with the parameters to be loaded in the frontend."""
        return {
            "risk_threshold": Config.RISK_THRESHOLD,
            "reset_local_storage": Config.RESET_LOCAL_STORAGE
        }
