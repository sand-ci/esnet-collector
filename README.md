ESNET Collector
============

The ESNET Collector queries [Netbeam API](https://esnet-netbeam.appspot.com/) instances and sends the data onto a RabbitMQ message bus.

The collector is packaged in a docker container available on [DockerHub](https://hub.docker.com/r/sandci/esnet-collector)

## Configuration

The default configuration is in `.env` file 

An example RabbitMQ environment file is:

    [rabbitmq]

    rmq-user = username
    rmq-pass = password
    rmq-host = example.com
    rmq-vhost = vhost
    rmq-exchange = osg.psdata.raw
    rmq-interface-key = esnet_interfaces
    rmq-traffic-key = esnet_traffic

Place this in a file the root directory of the project

