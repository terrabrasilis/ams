# Used as entry point to debug the ftp_ibama_risk.py in localhost during development.
#
# Read data file from INPE FTP service
# local test (see environment vars into launch startup definition)
import os
ftp = FtpIBAMARisk(db_url=os.environ.get('DB_AMAZON_URL'),
                   ftp_host=os.environ.get('FTP_HOST'),
                   ftp_path=os.environ.get('FTP_PATH'),
                   ftp_user=os.environ.get('FTP_USER'),
                   ftp_password=os.environ.get('FTP_PASS'))
ftp.execute()