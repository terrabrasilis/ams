# Docker-based deploy

A complete stack to deploy the dependency services required by the AMS application.

**Missing notes about required server configuration before starting the stack.**

## Docker for app

A self-contained environment to run the webapp and sync task based on Python 3.8.10 and Alpine Linux images.

## S.O. settings

The image of the docker container depends on the Docker environment. To prepare the system for operation, make changes based on the official documentation.

Mandatory:
 - https://docs.docker.com/engine/install/
 - https://docs.docker.com/engine/install/linux-postinstall/

Optional:
 - https://docs.docker.com/compose/install/


## Building the webapp image and sync image

The preconditions is:
 - Review and/or change the version number using git tags before building the image, because successive builds will overwrite the previous image that has the same version number;

The build script uses the latest repository tag to tag the docker image by running the following command.
```sh
# example to get more recent repository tag
git describe --tags --abbrev=0
```

### Build webapp image

Using a shell command line terminal, go to the docker directory and run the webapp-build.sh script.

```sh
cd docker/
./webapp-build.sh
```

### Build sync task image

Using a shell command line terminal, go to the docker directory and run the backend-sync-build.sh script.

```sh
cd docker/
./backend-sync-build.sh
```

## Container stack startup (docker compose)

The preconditions is:
 - Change the **docker/webapp-secrets.env** with the necessary database parameters so that the application back-end reaches the target database;
 - Change the SCRIPT_NAME and GEOSERVER_URL environment variables in the docker-compose.yaml file to their compatible runtime values;
 - Define a directory to be used to mount as a volume by the synchronization service container instance by looking in docker-compose.yaml to adjust this setting;
 - Change the INPUT_GEOTIFF_FUNDIARY_STRUCTURE environment variable in the docker-compose.yaml file to name of the GeoTiff compatible with the fundiary structure (this file is defined and prepared externally and copied to the directory mounted as volume by the instance of the synchronization service container);

Using the docker-compose command and the **docker/docker-compose.yaml** file to activate the webapp and the backend sync task services.

To up the stack in detached mode:
```sh
cd docker/
docker-compose -f docker-compose.yaml up -d
```

To down the stack:
```sh
cd docker/
docker-compose -f docker-compose.yaml down
```

## Container startup (without docker compose)

The preconditions is:
 - Change the **docker/webapp-secrets.env** with the necessary database parameters so that the application back-end reaches the target database;
 - Change the SCRIPT_NAME and GEOSERVER_URL environment variables in the command below to their compatible runtime values;
 - Define a directory to be used to mount as a volume by the synchronization service container instance by looking in the command line example below to adjust this setting;
 - Change the INPUT_GEOTIFF_FUNDIARY_STRUCTURE environment variable in the command line example below to name of the GeoTiff compatible with the fundiary structure (this file is defined and prepared externally and copied to the directory mounted as volume by the instance of the synchronization service container);

Use the docker command line. Change the <x.y.z> to the desired version.

```sh
# webapp launch command line example
docker run --env SCRIPT_NAME="/ams" \
--env GEOSERVER_URL="http://terrabrasilis.dpi.inpe.br/geoserver/" \
--env-file docker/webapp-secrets.env \
-d --rm --name ams-webapp terrabrasilis/ams-webapp:v<x.y.z>

# sync service launch command line example
docker run --env INPUT_GEOTIFF_FUNDIARY_STRUCTURE="estrutura_fundiaria_cst_lzw_4326.tif" \
--env-file docker/webapp-secrets.env \
-v "/some/local/dir/data:/usr/local/data" \
-d --rm --name ams-sync terrabrasilis/ams-sync:v<x.y.z>
```

## References

About env vars for runtime app.
https://dlukes.github.io/flask-wsgi-url-prefix.html