from ams.utils.database_utils import DatabaseUtils
from dateutil.relativedelta import relativedelta

class RiskUtils:
    """
    Some common functions used to provide the risk data file.
    """

    def __init__(self, db:DatabaseUtils):
        """
        Mandatory parameters:
        -------------------------------------------------
        :param str db: The instance 
        """
        self._db_schema = 'risk'
        self._log_table = 'etl_log_ibama'
        self._risk_expiration_table = 'risk_ibama_date'
        self._risk_input_table = 'weekly_data'
        self._db = db

    def get_last_file_info(self):
        """
        Get infos about the most recently downloaded file.
        return file name and date if exists one valid download registry on log table
        """
        fname=None
        dt=None

        sql=f"""
        SELECT file_name, last_file_date FROM {self._db_schema}.{self._log_table}
        WHERE process_status = 1 ORDER BY created_at DESC LIMIT 1;
        """
        try:
            cur = self._db.__get_db_cursor()
            cur.execute(sql)
            results=cur.fetchall()
        except Exception as e:
            print('Error on read the file name and last date from database')
            print(e.__str__())
            raise e
        
        if len(results)>0:
            fname=results[0][0]
            dt=results[0][1]

        return fname,dt

    def has_new_risk(self, file_date, expiration_risk:int=7):
        """
        Is there a new risk?

        Make sure it has the date ID that is not yet in use, filtered by expiration date.

        The expiration date is the date of the last downloaded file increased by 7 days,
        normally, or the number of days defined by the external configuration.

        Optional parameters:
        -------------------------------------------------
        :param int expiration_risk: The number of days to set the risk forecast due date. Default is seven (7)
        """
        has_new = False
        id = None
        expiration_date=(file_date + relativedelta(days = expiration_risk)).strftime("%Y-%m-%d")
        sql=f"""
        SELECT t1.id
        FROM {self._db_schema}.{self._risk_expiration_table} t1
        WHERE t1.expiration_date='{expiration_date}'::date
        AND NOT EXISTS
        (
            SELECT 1 FROM {self._db_schema}.{self._risk_input_table} t2
            WHERE t2.date_id=t1.id
        );
        """
        try:
            cur = self._db.__get_db_cursor()
            cur.execute(sql)
            results=cur.fetchall()
            if len(results)>0 and results[0][0]>0:
                has_new = True
                id = results[0][0]
        except Exception as e:
            print('Error on read id from expiration date')
            print(e.__str__())
            raise e
        
        return has_new, id