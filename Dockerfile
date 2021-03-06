FROM python:3-alpine3.7

LABEL maintainer Soundar Rajendran <rajends@umich.edu>

RUN apk update && apk add ca-certificates && rm -rf /var/cache/apk/*

ADD . /esnet_collector
WORKDIR /esnet_collector
RUN pip install -r requirements.txt

EXPOSE 8000

CMD ["python", "esnet_collector/esnetStatsUploader.py"]
