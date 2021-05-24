[![Build Status](https://travis-ci.com/AmazonSR/ams.svg?branch=master)](https://travis-ci.com/AmazonSR/ams)
[![codecov](https://codecov.io/gh/AmazonSR/ams/branch/master/graph/badge.svg?token=RM6BDOL70Y)](https://codecov.io/gh/AmazonSR/ams)

# AMS - Amazon Situation Room
AMS is a Web Mapping GIS application, which integrates with REST and OGC web services that provide spatial data on deforestation of Brazil Amazon rainforest obtained by satellites. In this way, the application provides visualization of the areas that are being deforested in different spatial resolutions and periods. In addition, the application provides graphs and reports to help analyze the data.

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
 mkdir -p ~/ams/git
cd ams
git clone https://github.com/$GitHub_User/ams.git git/ams #note: it must be your fork for development
sudo apt-get install python3-venv
python3 -m venv venv
source venv/bin/activate
pip install -r git/ams/requirements.txt
createdb -h localhost -p 5432 -U postgres DETER-B
pg_restore --host "localhost" --port "5432" --username "postgres" --dbname "DETER-B" --verbose  git/ams/data/deter-b-2019-2021.backup
cd git/ams/tests
export PYTHONPATH=~/ams/git/ams
pytest -v --cov
flake8 ..
```
### GeoServer

#### Install and start

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
##### Config

###### Accessing GeoServer Context Path to create the objects:

http://**[geoserverip]**:8080/geoserver/web/?7 

###### Click Workspaces/Add new workspace

**Name:** ams

Click **Save**

###### Click Stores/Add 
**Note:** A store is a data repository, a Postgres database f.e.

**Workspace:** ams

**Data Source Name:** AMS

**host:** locallhost (or another valid Postgres server IP)

**port:** 5432

**database:** AMS

**schema:** public

**user:** postgres

**passwd:** postgres

Click **Save**

###### Click Layers/Add a new Layer

In **Add layer from** choose ams:AMS

Click in **Publish** to publish a table in the list that appears below.

Publish the following tables:
csAmz_150km, csAmz_300km, csAmz_150km_risk_indicators, csAmz_300km_risk_indicators, amz_municipalities, amz_municipalities_risk_indicators, amz_states, amz_states_risk_indicators.

###### Click Layers/Add a new Layer

**Note:** Before that, check if the functions that are shown in **~/git/ams/geoserver/sqlviews** folder exists in AMS database. If they don't, you should create it.

In **Add layer from** choose ams:AMS

Click **Configure a new SQL view...**

**View Name:** csAmz_150km_diff_view

**SQL statement:** get the corresponding (by name) SQL statement in **~/git/ams/geoserver/sqlviews** folder. 
**Note:** remove comments and any other text than the SQL itself.

Click **Guess parameters from SQL** link

Copy the values for **Default value** and **Validation regular expression** from the original SQL statement comments.
 
Check checkbox **Get geometry type and SRID**

In **Atributes**, click **Refresh** 

Click **Save**

In the next form:

In **Bounding Boxes\Native Bounding Box**, click **Compute from data**

In **Bounding Boxes\Lat/Lon Bounding Box**, click **Compute from native bounds**

Click **Save**

You must create the other views you find in **~/git/ams/geoserver/sqlviews** folder.

##### Web App
Create a file `.env` within `~/git/ams/tests` whith following content:
```
export FLASK_APP=~/ams/git/ams/webapp/main.py 
export FLASK_DEBUG=1
export PYTHONPATH=~/ams/git/ams
source ~/git/ams/venv/bin/activate
```
Then
```bash
cd ~/ams/git/ams/tests
source .env
flask run
```