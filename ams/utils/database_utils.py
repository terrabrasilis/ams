from psycopg2 import OperationalError, connect

class DatabaseUtils:
    """
    Some common functions used to control database access.
    """

    def __init__(self, db_url:str):
        """
        Mandatory parameters:
        -------------------------------------------------
        :param str db_url: The connection string to write log into database log table (See model at scripts/startup.sql)
        """
        # database string connection
        self._db_url = db_url
        self._conn = None

    def get_db_cursor(self):
        """
        Gets the database cursor to run queries.
        
        Make a connection if you are not connected or if the connection is broken.
        """
        try:
            if self._conn is None or self._conn.closed>0:
                self._conn = connect(self._db_url)

            return self._conn.cursor()
        
        except OperationalError as e:
            print('Error on database connection')
            print(e.__str__())
            raise e

    def close(self):
        if self._conn:
            self._conn.close()

    def commit(self):
         if self._conn:
            self._conn.commit()

    def rollback(self):
         if self._conn:
            self._conn.rollback()