# AMS - Amazon Situation Room

AMS is a Web Mapping GIS application, which integrates with REST and OGC web services that provide spatial data on deforestation of Brazil Amazon rainforest obtained by satellites. In this way, the application provides visualization of the areas that are being deforested in different spatial resolutions and periods. In addition, the application provides graphs and reports to help analyze the data.

## Backend

The backend consists of some tasks initiated by a cronjob and aims to synchronize DETER and Active Fires data from external databases and pre-process the statistics for the layers of spatial units.

After the IBAMA risk file is downloaded, it is copied to the datadir geoserver to replace the old risk file. To do this, we need the shared directory between the geoserver's datadir and the backend service's workdir to achieve this.

### Database requirements

Database requirements to support backend tasks are:

    - Existence of SQL Views in the database for DETER and Active Fires;

    - Existence of DETER and Active Fires Schemas and tables in database;
    - Existence of "spatial_units" table with related data;
    - Existence of "deter_class" and "deter_class_group" tables with related data;

To start the new database, use the scripts/startup.sql file and the data/shapefiles* files

The startup.sql file has SQL scripts to prepare resources to provide input data for topics of interest.

Shapefiles represent the spatial units needed to perform statistical processing. Import these shapefiles into the public schema in the database before starting backend tasks.

By default, the tables will be expected before import shapes (on public schema):
 - csAmz_25km
 - csAmz_150km
 - csAmz_300km
 - amz_states
 - amz_municipalities

 > if it's not the real scenario, you have to tweak the names and other details in the init scripts and so on.

The "spatial_units" table is used to record each spatial unit layer imported into the database, using the external shapefiles. The name of each table and the unique identifier column must be registered in this table. If you use the default names described above, the insert script was provided in the startup.sql file.

The "deter_class" and "deter_class_group" tables are used to record each class name and an acronym of a class group.

The steps are (follow the sessions in startup.sql script):
    1) Create the database (below);
    2) Create the database model with SQL Views and tables;
    3) Insert the starter metadata;
    4) Create some functions helper used into SQL View inside GeoServer configuration layers;
    
```sql
-- -------------------------------------------------------------------------
-- To create the database, run it in the separate SQL Query window
-- -------------------------------------------------------------------------

-- Database: AMS

-- DROP DATABASE IF EXISTS "AMS";

CREATE DATABASE "AMS"
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.utf8'
    LC_CTYPE = 'en_US.utf8'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

COMMENT ON DATABASE "AMS" IS 'The new AMS database';
```

### Dockerize backend

See the [README.md](./docker/README.md)

## Frontend

### Development

I use VSCode for development environment. The steps are:

   - install all python dependencies using pip install -r requirements.txt;
   - create or edit launch.json and add configuration entry as below to provide an easy way to debug frontend application;
   - prepare the backend services to use behind the application, database and Geoserver as needed (see the dockerize backend for easy startup of this software tier);
   - run the new entry to debug the application;
   - Minify* JS and CSS codes to improve page loading;

configuration example to help with the debugging process.
```json
{
    // Use o IntelliSense para saber mais sobre os atributos possíveis.
    // Focalizar para exibir as descrições dos atributos existentes.
    // Para obter mais informações, acesse: https://go.microsoft.com/fwlink/?linkid=830387
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Flask",
            "type": "python",
            "request": "launch",
            "module": "flask",
            "env": {
                "GEOSERVER_URL": "http://localhost/geoserver",
                "DB_CERRADO_URL": "postgresql://postgres:postgres@150.163.17.103:5444/CES",
                "DB_AMAZON_URL": "postgresql://postgres:postgres@150.163.17.103:5444/AMS2",
                "FLASK_APP": "webapp/main.py",
                "FLASK_ENV": "development",
                "PYTHONPATH": "."
            },
            "args": [
                "run",
                "--no-debugger"
            ],
            "jinja": true
        }
    ]
}
```

*Through the Minify plugin in VSCode.
