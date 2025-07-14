# To build image for this dockerfile use this command on root directory of project:
#   docker build -t terrabrasilis/ams-webapp:<version> -f docker/webapp/Dockerfile .

#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.9.18-slim

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis"
LABEL br.inpe.dpi.terrabrasilis="ams-webapp"
LABEL author="Andre Carvalho"
LABEL author.email="andre.carvalho@inpe.br"
LABEL description="AMS - Amazon Situation Room"

ENV PYTHONUNBUFFERED 1

#-------------Application Specific Stuff ----------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libpq-dev \
    libproj-dev \
    proj-data \
    proj-bin \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    tzdata \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# define a timezone
ENV TZ=America/Sao_Paulo

# define install path
ENV INSTALL_PATH=/usr/local

# define PROJ config
ENV PROJ_DIR=/usr
ENV PROJ_LIB=/usr/share/proj

# define PYTHONPATH para acesso ao código ams/
ENV PYTHONPATH=${INSTALL_PATH}

# INSTALL REQUIREMENTS AND CODE
# ------------------------------------------------------
RUN mkdir -p $INSTALL_PATH/ams $INSTALL_PATH/webapp

ADD ams/requirements.txt $INSTALL_PATH/ams/requirements.txt
ADD webapp/requirements.txt $INSTALL_PATH/webapp/requirements.txt

RUN pip install --upgrade pip
RUN pip install -r $INSTALL_PATH/ams/requirements.txt
RUN pip install -r $INSTALL_PATH/webapp/requirements.txt

# INSTALL APP
# ------------------------------------------------------
COPY ams/ $INSTALL_PATH/ams/
COPY webapp/ $INSTALL_PATH/webapp/

# ENV VARS extras
ARG APP_BUILD_VERSION="1.0.0"
RUN echo "export TZ=America/Sao_Paulo" >> "${INSTALL_PATH}/webapp/.env" \
    && echo "var appVersion='${APP_BUILD_VERSION}';" > "${INSTALL_PATH}/webapp/app/static/js/ams/app.version.js"

# ENTRYPOINT
ADD docker/webapp/docker-entrypoint.sh $INSTALL_PATH/bin/docker-entrypoint.sh
RUN chmod +x $INSTALL_PATH/bin/docker-entrypoint.sh \
    && ln -s $INSTALL_PATH/bin/docker-entrypoint.sh /docker-entrypoint.sh

EXPOSE 7000

WORKDIR $INSTALL_PATH/webapp

ENTRYPOINT ["/docker-entrypoint.sh"]
