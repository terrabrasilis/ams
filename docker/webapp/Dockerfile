# To build image for this dockerfile use this command on root directory of project:
#   docker build -t terrabrasilis/ams-webapp:<version> -f docker/webapp/Dockerfile .
#
#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.8.10-alpine

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis"
LABEL br.inpe.dpi.terrabrasilis="ams-webapp"
LABEL author="Andre Carvalho"
LABEL author.email="andre.carvalho@inpe.br"
LABEL description="AMS - Amazon Situation Room"

ENV PYTHONUNBUFFERED 1
#-------------Application Specific Stuff ----------------------------------------------------

RUN apk update \
  && apk add --no-cache --update \
    build-base \
    postgresql \
    postgresql-dev \
    libpq \
    tzdata \
    proj \
    proj-dev \
    proj-util \
    gdal-dev \
    geos \
    geos-dev \
    && rm -rf /var/cache/apk/*

# define the timezone to run cron
ENV TZ=America/Sao_Paulo

# define the install path env var
ENV INSTALL_PATH /usr/local

# INSTALL REQUIREMENTS AND CODE
# ------------------------------------------------------
RUN mkdir $INSTALL_PATH/ams && mkdir $INSTALL_PATH/webapp
ADD ams/requirements.txt $INSTALL_PATH/ams/requirements.txt
ADD webapp/requirements.txt $INSTALL_PATH/webapp/requirements.txt
# Install Python requirements
RUN pip install -r $INSTALL_PATH/ams/requirements.txt \
    && pip install -r $INSTALL_PATH/webapp/requirements.txt
# END REQUIREMENTS INSTALATION
# ------------------------------------------------------

# INSTALL APP
# ------------------------------------------------------
COPY ams/ $INSTALL_PATH/ams/
COPY webapp/ $INSTALL_PATH/webapp/
# END INSTALL APP
# ------------------------------------------------------

## THE ENV VARS
ARG APP_BUILD_VERSION="1.0.0"
RUN echo "export PYTHONPATH=\"${INSTALL_PATH}\"" >> "${INSTALL_PATH}/webapp/.env" \
    && echo "export TZ=America/Sao_Paulo" >> "${INSTALL_PATH}/webapp/.env" \
    && echo "var appVersion='${APP_BUILD_VERSION';" > "${INSTALL_PATH}/webapp/app/static/js/ams/app.version.js"

# Script to run on start server
ADD docker/webapp/docker-entrypoint.sh $INSTALL_PATH/bin/docker-entrypoint.sh
RUN chmod +x $INSTALL_PATH/bin/docker-entrypoint.sh \
    && ln -s usr/local/bin/docker-entrypoint.sh / # backwards compat

EXPOSE 7000

WORKDIR $INSTALL_PATH/webapp

ENTRYPOINT [ "/docker-entrypoint.sh" ]
