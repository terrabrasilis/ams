# To build image for this dockerfile use this command on root directory of project:
#   docker build -t terrabrasilis/ams-sync:<version> -f docker/backend-sync/Dockerfile .
#
#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.8.10-alpine

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis"
LABEL br.inpe.dpi.terrabrasilis="ams-sync"
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
    && rm -rf /var/cache/apk/*

# define the timezone to run cron
ENV TZ=America/Sao_Paulo

# define the install path env var
ENV INSTALL_PATH /usr/local

# INSTALL REQUIREMENTS
# ------------------------------------------------------
RUN mkdir $INSTALL_PATH/ams && mkdir $INSTALL_PATH/webapp
ADD ams/requirements.txt $INSTALL_PATH/ams/requirements.txt
# Install Python requirements
RUN pip install -r $INSTALL_PATH/ams/requirements.txt
# END REQUIREMENTS INSTALATION
# ------------------------------------------------------

# INSTALL APP
# ------------------------------------------------------
COPY ams/ $INSTALL_PATH/ams/
COPY webapp/ $INSTALL_PATH/webapp/
# END INSTALL APP
# ------------------------------------------------------

## THE ENV VARS
RUN echo "export PYTHONPATH=\"${INSTALL_PATH}\"" >> "${INSTALL_PATH}/webapp/.env" \
    && echo "export TZ=America/Sao_Paulo" >> "${INSTALL_PATH}/webapp/.env"

# install and enable cron job scripts
ADD docker/backend-sync/cron_exec.sh ${INSTALL_PATH}/
ADD docker/backend-sync/daily.cron /etc/crontabs/root
RUN chmod +x ${INSTALL_PATH}/cron_exec.sh \
    && chmod +x /etc/crontabs/root

WORKDIR ${INSTALL_PATH}/

CMD crond -l 2 -f
