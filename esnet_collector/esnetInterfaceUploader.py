from rabbitmqconnect import RabbitMQConnect, get_rabbitmq_connection
from datetime import date, datetime, timedelta
import urllib.request
import urllib.parse
import urllib3.util
import requests
import time
import json
import pika
import csv
import sys
import os

class EsnetInterfaceUploader():

    def __init__(self):

        self.url = get_rabbitmq_connection().rabbithost
        self.exchange = get_rabbitmq_connection().exchange
        self.username = get_rabbitmq_connection().username
        self.passwd = get_rabbitmq_connection().passwd
        self.vhost = get_rabbitmq_connection().vhost
        self.key1 = get_rabbitmq_connection().key1
        self.key2 = get_rabbitmq_connection().key2

        credentials = pika.PlainCredentials(self.username, self.passwd)
        self.params = pika.ConnectionParameters(
            host=self.url, virtual_host=self.vhost, credentials=credentials, heartbeat=0)
        self.connection = pika.BlockingConnection(
            self.params)  # Connect to CloudAMQP
        self.channel = get_rabbitmq_connection().createChannel()


    def SendInterfacetoRMQ(self):

        with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
            data = json.load(url)
            counter = 0
            timestamp = datetime.utcnow()

            for datum in data:
                seconds = datetime.utcnow().timestamp()
                timestamp_in_millis = round(seconds * 1000)
                datum['timestamp'] = timestamp_in_millis
                self.channel.basic_publish(exchange=self.exchange, routing_key=self.key1, body=json.dumps(datum), properties=pika.BasicProperties(content_type='text/plain',
                                                                                                                                                  delivery_mode=1))
                counter += 1
                
        print("{} total Interfaces sent to OSG RabbitMQ bus at Time : {}".format(counter, timestamp))


stats = EsnetInterfaceUploader()
stats.SendInterfacetoRMQ()

get_rabbitmq_connection().closeConnection()
