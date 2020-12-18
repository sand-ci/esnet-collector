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

    def SendInterfacetoRMQ(self):

        with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
            f = open("int0930.txt", 'w')
            data = json.load(url)
            timestamp = datetime.utcnow()

            for datum in data:
                seconds = datetime.utcnow().timestamp()
                timestamp_in_millis = round(seconds * 1000)
                #datum['timestamp'] = timestamp_in_millis
                body = json.dumps(datum)
                print(body, file = f)
                                                                                                 
stats = EsnetInterfaceUploader()
stats.SendInterfacetoRMQ()

