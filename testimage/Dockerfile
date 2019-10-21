FROM python:3-alpine
MAINTAINER Quentin Loubiere <map@synidion.fr>

RUN apk update && apk add git
RUN  git clone https://github.com/Z-Map/async-rai.git /home/docker/async-rai

COPY asyncrai_test.sh /home/docker/script/asyncrai_test.sh
RUN chmod 744 /home/docker/script/asyncrai_test.sh

ENTRYPOINT /home/docker/script/asyncrai_test.sh
WORKDIR /home/docker/async-rai

