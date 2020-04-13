#!/usr/bin/env bash

#Uploading Interface data to RabbitMQ
echo " Writing Interfaces Data to the RabbitMQ bus"
python rabbitmqInterfaceUploader.py

#Uploading Error  data to RabbitMQ
echo " Writing Errors Data to the RabbitMQ bus"
python rabbitmqErrorsUploader.py

#Uploading Discards data to RabbitMQ
echo " Writing Discards Data to the RabbitMQ bus"
python rabbitmqDiscardsUploader.py

#Uploading Traffic data to RabbitMQ
echo " Writing Traffic Data to the RabbitMQ bus"
python rabbitmqTrafficUploader.py

