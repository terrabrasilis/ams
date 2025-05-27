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
    RISK_INPE = os.environ.get('RISK_INPE', "true") == "true"
    RISK_THRESHOLD = 0. if RISK_INPE else float(os.environ.get("RISK_THRESHOLD", "0.90"))
    RESET_LOCAL_STORAGE = (
        os.environ.get('RESET_LOCAL_STORAGE').lower() == "true" if os.environ.get('RESET_LOCAL_STORAGE') else False
    )
    INPE_RISK_SCALE_FACTOR = 1

    @staticmethod
    def get_params_to_frontend():
        """Return a dictionary with the parameters to be loaded in the frontend."""
        return {
            "risk_threshold": Config.RISK_THRESHOLD,
            "reset_local_storage": Config.RESET_LOCAL_STORAGE,
            "risk_inpe": Config.RISK_INPE,
            "risk_scale_factor": Config.INPE_RISK_SCALE_FACTOR,
        }
