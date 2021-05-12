[![Build Status](https://travis-ci.com/AmazonSR/ams.svg?branch=master)](https://travis-ci.com/AmazonSR/ams)
[![codecov](https://codecov.io/gh/AmazonSR/ams/branch/master/graph/badge.svg?token=RM6BDOL70Y)](https://codecov.io/gh/AmazonSR/ams)

# AMS - Amazon Situation Room

## Environment
* **Ubuntu** >= 20.04
* **Python** >= 3.8.5
* **PostgreSQL** >= 13 & **PostGIS** >= 3
* **GeoServer** >= 2.19

## To Install
### Ubuntu
```bash
sudo apt -y install vim bash-completion wget
wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | sudo apt-key add -
echo "deb [arch=amd64] http://apt.postgresql.org/pub/repos/apt/ `lsb_release -cs`-pgdg main" | sudo tee /etc/apt/sources.list.d/pgdg.list
sudo apt update
sudo apt install postgresql-13-postgis-3
sudo passwd postgres
[[postgres]]
su postgres
psql -c "ALTER USER postgres WITH PASSWORD 'postgres'" -d postgres
exit
sudo -u postgres createuser --superuser $USER
sudo -u postgres psql
\password $USER #note: $USER here needs to be written# 
``` 
### Development
#### Core 
```bash
cd ~
mkdir ams
mkdir git
git clone https://github.com/$GitHub_User/ams.git git/ams #note: it must be your fork for development
sudo apt-get install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r git/ams/requirements.txt
createdb -h localhost -p 5432 -U postgres DETER-B
pg_restore --host "localhost" --port "5432" --username "postgres" --no-password --dbname "DETER-B" --verbose  git/ams/data/deter-b-2019-2021.backup
cd git/ams/tests
export PYTHONPATH=../../ams
pytest -v --cov
flake8 ..
```
#### GeoServer
```bash
cd ~
wget http://sourceforge.net/projects/geoserver/files/GeoServer/2.19.0/geoserver-2.19.0-bin.zip
sudo apt install unzip
unzip geoserver-2.19.0-bin.zip -d geoserver
sudo apt install openjdk-11-jre-headless
echo "export GEOSERVER_HOME=/home/$USER*/geoserver" >> ~/.profile #note: $USER here needs to be written#
source ~/.profile
~/geoserver/bin/startup.sh &
```
##### GeoServer Views [TODO]

#### Web App
Create a file `.env` whith folling content:
```
export FLASK_APP=../webapp/main.py 
export FLASK_DEBUG=1
export PYTHONPATH=../../ams
source ams/venv/bin/activate
```
Then
```bash
cd git/ams/tests
source .venv
flask run
```
