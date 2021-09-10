# To build image for this dockerfile use this command on root directory of project:
#   docker build -t terrabrasilis/ams-update-task:<version> -f docker/update-task/Dockerfile .
#
#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM python:3.8.10-alpine

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis"
LABEL br.inpe.dpi.terrabrasilis="ams-update-task"
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
    && rm -rf /var/cache/apk/*

# define the timezone to run cron
ENV TZ=America/Sao_Paulo

# define the install path env var
ENV INSTALL_PATH /usr/local

# INSTALL REQUIREMENTS AND BACKEND CODE
# ------------------------------------------------------
RUN mkdir $INSTALL_PATH/ams && mkdir $INSTALL_PATH/tasks
# ------------------------------------------------------
COPY ams/ $INSTALL_PATH/ams/
COPY scripts/ $INSTALL_PATH/tasks/
# Install Python requirements
RUN pip install -r $INSTALL_PATH/ams/requirements.txt
# END REQUIREMENTS INSTALATION
# ------------------------------------------------------

## THE ENV VARS
RUN echo "export PYTHONPATH=\"${INSTALL_PATH}\"" >> "${INSTALL_PATH}/tasks/.env" \
    && echo "export TZ=America/Sao_Paulo" >> "${INSTALL_PATH}/tasks/.env"

# install and enable cron job scripts
ADD docker/update-task/cron_exec.sh $INSTALL_PATH/
ADD docker/update-task/update-task-schedule.cron /etc/crontabs/root
RUN chmod +x /usr/local/cron_exec.sh \
    && chmod +x /etc/crontabs/root

WORKDIR $INSTALL_PATH

CMD crond -l 2 -f
