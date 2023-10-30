from os import path
from psycopg2 import OperationalError, connect
from datetime import datetime
from dateutil.relativedelta import relativedelta
import aioftp
import asyncio

class FtpIBAMARisk:
    """
    Used to obtain the FTP raster data file provided by IBAMA.

    The geotiff file represents the risk of deforestation in the matrix 1km X 1km in the Legal Amazon for one week.

    
    Using async library to access FTP server.
    
    Implementation references:
    --------------------------------------------------
     - https://aioftp.readthedocs.io/client_tutorial.html
     - https://docs.python.org/3/library/asyncio-task.html

    """

    def __init__(self, db_url:str, ftp_host:str, ftp_path:str, ftp_user:str, ftp_password:str, ftp_port:int=None, output_path:str=None):
        """
        Settings for FTP connection and file download.

        Mandatory parameters:
        -------------------------------------------------
        :param str db_url: The connection string to write log into database log table (See model at scripts/startup.sql)
        :param str ftp_host: The host name or IP of FTP service
        :param str ftp_path: The path for directory where the file is
        :param str ftp_user: The username to login
        :param str ftp_password: The password to login

        Optional parameters:
        -------------------------------------------------
        :param int ftp_port: The port number for connection
        :param str output_path: The output directory to write the downloaded file
        
        """

        # FTP connection parameters
        self._host = ftp_host
        self._port = ftp_port if ftp_port else 21
        self._ftp_path = ftp_path
        self._user = ftp_user
        self._pass = ftp_password
        # database string connection
        self._db_url = db_url
        self._conn = None

        self._output_path = output_path if output_path and path.exists(output_path) else path.join(path.dirname(__file__), '../../data')
        self._output_file_name = f"""weekly_ibama_1km_{datetime.now().strftime("%d_%m_%Y")}.tif"""
        self._risk_expiration_table = 'risk.risk_ibama_date'
        self._log_table = 'risk.etl_log_ibama'

    def set_expiration_days(self, ndays:int=7):
        """
        Configure the number of days to define the risk forecast due date.
        Default is seven (7)
        """
        # number of days to set the risk forecast due date
        self._ndays_of_expiration = ndays

    def __get_db_cursor(self):
        """
        Gets the database cursor to run queries.
        
        Make a connection if you are not connected or if the connection is broken.
        """
        if self._conn is None or self._conn.closed>0:
            self._conn = connect(self._db_url)

        return self._conn.cursor()

    async def __get_file(self):
        """
        Gets the matricial file from FTP and write on local diretory.

        Prerequisites:
         - The FTP access parameters (from global config file);
         - The existence of geotiff file on FTP;
        See the README.md file for instructions.
        """
        client = aioftp.Client()
        log_msg=""
        remote_file_date=None
        file_destination=""
        status=0
        try:
            await client.connect(self._host, int(self._port))
            await client.login(self._user, self._pass)

            file_source=""
            latest_file_date=None

            # list files and sort by modified date
            for file_path, file_info in (await client.list(path=self._ftp_path, recursive=False)):
                remote_file_size=int(file_info['size'])
                file_mdate=file_info['modify']
                remote_file_date=datetime(year=int(file_mdate[0:4]), month=int(file_mdate[4:6]), day=int(file_mdate[6:8])).date()
                # get the latest file using metadata information
                if latest_file_date is None or latest_file_date < remote_file_date:
                    latest_file_date=remote_file_date
                    file_source=file_path

            last_download_date=self.__get_last_download_date()
            if last_download_date is None or latest_file_date > last_download_date:
                file_destination=f"""{self._output_path}/{self._output_file_name}"""
                file_destination=path.abspath(file_destination)
                await client.download(file_source, file_destination, write_into=True)
                if path.isfile(file_destination) and path.getsize(file_destination) == remote_file_size:
                    log_msg="Success on download file."
                    status=1
                else:
                    log_msg="The file is downloaded but is invalid."
                    file_destination=""
            else:
                log_msg="There is no new file."
                file_destination=""

        except OperationalError as e:
            log_msg=f"Error on database connection. exception_msg: {e.__str__()}"
            raise e
        
        except Exception as e:
            log_msg=f"Error on download file from FTP. exception_msg: {e.__str__()}"
            raise e
        
        finally:
            # close the ftp connection
            client.close()
            self.__write_log2db(log_msg, status, remote_file_date, file_destination)
            self.__write_expiration_date(status, remote_file_date)

            # clase the database connection if exists
            if self._conn:
                self._conn.close()


    def __get_last_download_date(self):
        dt=None
        sql=f"SELECT last_file_date FROM {self._log_table} WHERE process_status = 1 ORDER BY last_file_date DESC LIMIT 1;"
        try:
            cur = self.__get_db_cursor()
            cur.execute(sql)
            results=cur.fetchall()
        except Exception as e:
            print('Error on read the last date from database')
            print(e.__str__())
            raise e
        
        if len(results)>0:
            dt=results[0][0]

        return dt


    def __write_log2db(self, msg:str, status:int, remote_file_date:datetime, output_file_name:str):

        dt=remote_file_date.strftime("%Y-%m-%d") if remote_file_date is not None else ""
        sql=f"""
        INSERT INTO {self._log_table} (file_name, process_status, process_message, last_file_date)
        VALUES('{output_file_name}', {status}, '{msg}', '{dt}');
        """
        try:
            cur = self.__get_db_cursor()
            cur.execute(sql)
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on write log into database')
            print(e.__str__())
            raise e

    def __write_expiration_date(self, status:int, remote_file_date:datetime):

        if status==1:
            dt=(remote_file_date + relativedelta(days = self._ndays_of_expiration)).strftime("%Y-%m-%d")
            sql=f"""INSERT INTO {self._risk_expiration_table} (expiration_date) VALUES('{dt}')"""
            try:
                cur = self.__get_db_cursor()
                cur.execute(sql)
                self._conn.commit()
            except Exception as e:
                self._conn.rollback()
                print('Error on write log into database')
                print(e.__str__())
                raise e

    def execute(self):
        asyncio.run(self.__get_file())
