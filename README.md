ESNET Collector
============

The ESNET Collector queries [Netbeam API](https://esnet-netbeam.appspot.com/) instances and sends the data onto a RabbitMQ message bus.

The collector is packaged in a docker container available on [DockerHub](https://hub.docker.com/r/sandci/esnet-collector)

## RabbitMQ Configuration

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

## MySQL Configuration

To keep track of the everyday changes in the esnet [Interfaces API](https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces) including additon/removal of interfaces we have decided to use a MySQL database with an interfaces table.

In order to start a mysql instance, we brought up a docker `mysql5.7` instance using a `docker-compose.yml` file in our production server. The specifications of the docker-compose file are provided below :

    [docker-compose.yml]
    
    version: '3'

    services:
      db:
        image: mysql:5.7
        container_name: esnet_db
        environment:
          MYSQL_ROOT_PASSWORD: 
          MYSQL_DATABASE: esnet
          MYSQL_USER: esnet_user
          MYSQL_PASSWORD:
        ports:
          - "3306"
        volumes:
          - dbdata:/var/lib/mysql
    networks:
      default:
        external:
          name: esnet-network
    volumes:
      dbdata:

Place the docker-compose file in a suitable accessible location in the production server. The database image we are using is mysql5.7 and the docker container name in this instance is `esnet_db`. The environment parameter values can be set to your choice. In our case we set the MYSQL_DATABASE value to be esnet which is the name of the database we will be using for the project. We also created a user named `esnet_user`. The password for the user and root can be any password of your choice. The mysql instance is running in port 3306 and the data will be stored in /var/lib/mysql directory. Since we are mounting it as a volume, the data will persist even if the mysql container is stopped/deleted and restarted. The Networking part of the container is explained in the Networking section of this documentation.

In order to start the container just run `docker-compose up` from the directory where your docker compose file is stored.   

To access the mysql docker command line instance , run

`docker exec -it esnet_db mysql -uesnet_user -p`

where esnet_db is the docker mysql container name and esnet_user is the username for the login. After running the above command you will be prompted for a password . Then we eneter the passwordd for the user provided in our docker-compose.yml file.

After logging into the mysql database instance we can do the following:

The database we use is named esnet. The table we use to store the interface data is esnet_interfaces. The esnet_interfaces table layout is provided below

| Field          | Type         | Null | Key | Default | Extra          |
+----------------+--------------+------+-----+---------+----------------+
| id             | int          | NO   | PRI | NULL    | auto_increment |
| name           | varchar(128) | NO   | PRI | NULL    |                |
| status         | varchar(2)   | NO   |     | NULL    |                |
| active_from    | varchar(13)  | NO   |     | NULL    |                |
| active_until   | varchar(13)  | YES  |     | NULL    |                |
| errors_until   | varchar(13)  | YES  |     | NULL    |                |
| discards_until | varchar(13)  | YES  |     | NULL    |                |
| traffic_until  | varchar(13)  | YES  |     | NULL    |                |
+----------------+--------------+------+-----+---------+----------------+

Now our interfaces table is ready to store data permanently.

## Container Networking

Since we are going to be running multiple docker containers, we need all the containers to be on the same network. If the containers are not in the smae network the python esnet collector script would not be able to see the mysql esnet database and perform select, insert, update operations on the interfaces table.

Until Docker version 2, the containers could be linked with a `--link` flag as described in this [documentation](https://docs.docker.com/network/links/).But from Docker version 3, which our containers use as seen above in our mysql container the --link flag has been deprecated and are not used. Thus, to link the containers together in docker version 3 we use the networking feature.
First we run the `docker network ls` command to list the current networks.

Then, we created a network named `esnet-network` using the command "docker network create esnet-network". We use this network in the mysql docker-compose file as shown in the section above. Once the docker container is started it automatically uses our user-defined network as indicated in the docker compose file.

To view the details about the network including which containers are using the particular network we use `docker network inspect <network_name>` command

## Collector

Before running the esnet collector python script we first package our script into a Dockerfile so that we can run it as a docker container. The Dockerfile has a python3 version and runs a requirements file which contains all packages needed for the collector script to run including pika, python-dotenv, requests and mysql-connector. The docker compose file for the esnet_collector contains environment variables with RabbitMQ parameters described in the RabbitMQ Configuration section.

Next step is to build the esnet collector. To do that we run 

`docker build -t esnet-collector .`

where esnet-colelctor is the folder where the Dockerfile , docker-compose.yml file, requirements.txt file and the collector python script reside.

Once the docker container image for the collector is built we can run the script successfully on the same network as the mysql database using the command below

`docker run -it --rm --network esnet-network esnet-collector`

where esnet-netowrk is the user-defined network that is used to connect the mysql container. We want the python script to run in the same network as the database else the esnet interface table operations will fail and the python script will fail due to that.
