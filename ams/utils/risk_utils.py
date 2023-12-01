from ams.utils.database_utils import DatabaseUtils

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
        # The public.last_risk_data is an SQLView in public schema to join some tables from risk schema
        self._risk_table = 'public.last_risk_data'
        # one of the land use tables used to verify that the second phase of risk data processing has been completed
        self._final_land_use_table = 'public.amz_states_land_use'
        self._db = db

        # The class name is fixed to "RK" as is all code that checks the risk class name.
        self._risk_classname = "RK"

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
            cur = self._db.get_db_cursor()
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

    def first_phase_already(self, risk_date):
        """
        Is the first phase already completed?

        The first phase is where the risk data is inserted on the database risk model.
            - Inserted from the raster risk file on weekly_ibama_tmp table;
            - Populate the points matrix crossing the points from the temp table and the biome border;
            - Copy the risk data into the weekly table using the pre-extracted dot matrix and filtered by values greater than zero;

        Mandatory parameters:
        -------------------------------------------------
        :param datetime risk_date: The date of the last valid risk file.

        """
        has_new = False
        id = None
        sql=f"""
        SELECT t1.id
        FROM {self._db_schema}.{self._risk_expiration_table} t1
        WHERE t1.risk_date='{risk_date}'::date
        AND NOT EXISTS
        (
            SELECT 1 FROM {self._db_schema}.{self._risk_input_table} t2
            WHERE t2.date_id=t1.id
        );
        """
        try:
            cur = self._db.get_db_cursor()
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

    def second_phase_already(self, risk_date):
        """
        Is the second phase already completed?

        The second phase is where the risk data is entered into the AMS database model.
            - Cross the dot matrix of risk data with raster land use data, producing data from the risk land structure table;
            - Group data from the land structure table by spatial units;
        
        Mandatory parameters:
        -------------------------------------------------
        :param datetime risk_date: The date of the last valid risk file.
        """
        phase_two = False

        sql=f"""
        SELECT COUNT(*)::integer
        FROM {self._risk_table} rk, 
        {self._final_land_use_table} rk_final
        WHERE rk_final.classname='{self._risk_classname}'
        AND rk_final.date='{risk_date}'::date
        AND rk_final.date=rk.view_date;
        """
        try:
            cur = self._db.get_db_cursor()
            cur.execute(sql)
            results=cur.fetchall()
            if len(results)>0 and results[0][0]>0:
                phase_two = True
        except Exception as e:
            print('Error on verify that the second phase of risk data processing has been completed')
            print(e.__str__())
            raise e
        
        return phase_two