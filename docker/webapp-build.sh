#!/bin/bash

NO_CACHE=""

# pass "silent" as first parameter when calling this script to skip questions
if [[ ! "$1" = "silent" ]]; then
    echo "Do you want to build using docker cache from previous build? Type yes to use cache." ; read BUILD_CACHE
    if [[ ! "$BUILD_CACHE" = "yes" ]]; then
        echo "Using --no-cache to build the image."
        echo "It will be slower than use docker cache."
        NO_CACHE="--no-cache"
    else
        echo "Using cache to build the image."
        echo "Nice, it will be faster than use no-cache option."
    fi
fi

VERSION=$(git describe --tags --abbrev=0)

echo 
echo "/######################################################################/"
echo " Build new image terrabrasilis/ams-webapp:$VERSION "
echo "/######################################################################/"
echo
docker build $NO_CACHE -t "terrabrasilis/ams-webapp:$VERSION" --build-arg APP_BUILD_VERSION=$VERSION -f webapp/Dockerfile ../

# pass "silent" as first parameter when calling this script to skip questions
if [[ ! "$1" = "silent" ]]; then
    # send to dockerhub
    echo 
    echo "The building was finished! Do you want sending the new image to Docker HUB? Type yes to continue." ; read SEND_TO_HUB
    if [[ ! "$SEND_TO_HUB" = "yes" ]]; then
        echo "Ok, not send the images."
    else
        echo "Nice, sending the image!"
        docker push "terrabrasilis/ams-webapp:$VERSION"
    fi
fi