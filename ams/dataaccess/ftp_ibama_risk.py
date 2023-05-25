from os import path
from psycopg2 import connect
from datetime import datetime
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

    def __init__(self, db_url:str, host:str, ftp_path:str, user:str, password:str, port:int=None, output_path:str=None, risk_file_name:str=None):
        """
        Settings for FTP connection and file download.

        Mandatory parameters:
        -------------------------------------------------
        :param str db_url: The connection string to write log into database log table (See model at scripts/startup.sql)
        :param str host: The host name or IP of FTP service
        :param str ftp_path: The path for directory where the file is
        :param str user: The username to login
        :param str password: The password to login

        Optional parameters:
        -------------------------------------------------
        :param int port: The port number for connection
        :param str output_path: The output directory to write the downloaded file
        :param str risk_file_name: The name of file on server
        
        """

        self._host = host
        self._port = port if port else 21
        self._ftp_path = ftp_path
        self._user = user
        self._pass = password

        self._conn = connect(db_url)

        self._input_file_name = risk_file_name if risk_file_name else 'Risk_areas_AMZL.tif'
        self._output_path = output_path if output_path and path.exists(output_path) else path.join(path.dirname(__file__), '../../data')
        self._output_file_name = f"""weekly_ibama_1km_{datetime.now().strftime("%d_%m_%Y")}.tif"""
        self._risk_input_table = 'risk.weekly_ibama_1km'
        self._log_table = 'risk.etl_log_ibama'

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
        file_destination=""
        status=0
        try:
            await client.connect(self._host, int(self._port))
            await client.login(self._user, self._pass)

            file_source=self._ftp_path + '/' + self._input_file_name

            if await client.exists(file_source):
                remote_file_metadata=await client.stat(file_source)
                remote_file_size=int(remote_file_metadata['size'])
                file_mdate=remote_file_metadata['modify']
                remote_file_date=datetime(year=int(file_mdate[0:4]), month=int(file_mdate[4:6]), day=int(file_mdate[6:8])).date()
                last_download_date=self.__get_last_download_date()
                if remote_file_date > last_download_date:
                    file_destination=f"""{self._output_path}/{self._output_file_name}"""
                    file_destination=path.abspath(file_destination)
                    await client.download(file_source, file_destination, write_into=True)
                    if path.isfile(file_destination) and path.getsize(file_destination) == remote_file_size:
                        log_msg="Success on download file."
                        status=1
                    else:
                        log_msg="The file is downloaded but is invalid file."
                        file_destination=""
                else:
                    log_msg="There is no new file."
                    file_destination=""

        except Exception as e:
            log_msg=f"Error on download file from FTP. exception_msg: {e.__str__()}"
            raise e
        
        finally:
            client.close()
            self.__write_log2db(log_msg, status, remote_file_date, file_destination)


    def __get_last_download_date(self):

        sql=f"SELECT last_file_date FROM {self._log_table} WHERE process_status = 1 ORDER BY last_file_date DESC LIMIT 1;"
        try:
            cur = self._conn.cursor()
            cur.execute(sql)
            results=cur.fetchall()
        except Exception as e:
            print('Error on read the last date from database')
            print(e.__str__())
            raise e
        
        if len(results)==0:
            dt=datetime(year=2023,month=1,day=1).date()
        else:
            dt=results[0][0]

        return dt


    def __write_log2db(self, msg:str, status:int, remote_file_date:datetime, output_file_name:str):

        dt=remote_file_date.strftime("%Y-%m-%d")
        sql=f"""INSERT INTO {self._log_table} (file_name, process_status, process_message, last_file_date)
                VALUES('{output_file_name}', {status}, '{msg}', '{dt}')"""
        try:
            cur = self._conn.cursor()
            cur.execute(sql)
            self._conn.commit()
        except Exception as e:
            self._conn.rollback()
            print('Error on write log into database')
            print(e.__str__())
            raise e

    def execute(self):
        asyncio.run(self.__get_file())

# local test
# db='postgresql://postgres:postgres@150.163.17.103:5444/AMS2'
# ftp = FtpIBAMARisk(db, host="ftp.gov.br", ftp_path="/somedir", user="user", password="pass")
# ftp.execute()