# To build image for this dockerfile use this command on root directory of project:
#   docker build -t terrabrasilis/ams-sync:<version> -f docker/backend-sync/Dockerfile .
#
#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.9.18-alpine

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis"
LABEL br.inpe.dpi.terrabrasilis="ams-sync"
LABEL author="Andre Carvalho"
LABEL author.email="andre.carvalho@inpe.br"
LABEL description="Update task for AMS database"

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

# INSTALL REQUIREMENTS AND BACKEND CODE
# ------------------------------------------------------
RUN mkdir ${INSTALL_PATH}/ams && mkdir ${INSTALL_PATH}/scripts && mkdir ${INSTALL_PATH}/data
ADD ams/requirements.txt ${INSTALL_PATH}/ams/requirements.txt
# Install Python requirements
RUN pip install -r ${INSTALL_PATH}/ams/requirements.txt
# ------------------------------------------------------
COPY ams/ ${INSTALL_PATH}/ams/
COPY scripts/ ${INSTALL_PATH}/scripts/
# ------------------------------------------------------

## THE ENV VARS
RUN echo "export PYTHONPATH=\"${INSTALL_PATH}\"" >> "${INSTALL_PATH}/scripts/.env" \
    && echo "export TZ=America/Sao_Paulo" >> "${INSTALL_PATH}/scripts/.env"

# install and enable cron job scripts
ADD docker/backend-sync/cron_exec.sh ${INSTALL_PATH}/
ADD docker/backend-sync/schedule.cron /etc/crontabs/root
RUN chmod +x ${INSTALL_PATH}/cron_exec.sh \
    && chmod +x /etc/crontabs/root

WORKDIR ${INSTALL_PATH}

VOLUME ["${INSTALL_PATH}/data/"]

CMD crond -l 2 -f
