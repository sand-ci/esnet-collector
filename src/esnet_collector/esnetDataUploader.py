from esnet_collector.rabbitmqconnect import RabbitMQConnect
from datetime import date, datetime, timedelta
from urllib.error import HTTPError 
import esnet_collector
import urllib.request
import urllib.parse
import datetime
import time
import json
import csv
import pika
import os

class EsnetDataUploader():

    def __init__(self):       
        
        self.channel = esnet_collector.get_rabbitmq_connection().createChannel()
        self.exchange = esnet_collector.get_rabbitmq_connection().exchange
        self.key1 = esnet_collector.get_rabbitmq_connection().key1
        self.key2 = esnet_collector.get_rabbitmq_connection().key2

    def SendInterfacetoRMQ(self):
        
        with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
            data = json.load(url)

            for datum in data:
                seconds = datetime.utcnow().timestamp()
                timestamp_in_millis = round(seconds * 1000)
                datum['timestamp'] = timestamp_in_millis
                self.channel.basic_publish(exchange=self.exchange, routing_key=self.key1, body=json.dumps(datum), properties=pika.BasicProperties(content_type='text/plain',
                                                          delivery_mode=1))
                self.channel.confirm_delivery()
                print("[x] Interface data sent to OSG RabbitMQ bus")  


    def SendStatsToRMQ(self, stats):

        datetimePattern = '%Y-%m-%d %H:%M:%S'
        yesterday = (date.today() - timedelta(1)).strftime('%Y-%m-%d %H:%M:%S')
        startDate = int(time.mktime(time.strptime(yesterday,datetimePattern)))*1000
        today = date.today().strftime('%Y-%m-%d %H:%M:%S')
        endDate = int(time.mktime(time.strptime(today,datetimePattern)))*1000

        with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
            data = json.load(url)

            for datum in data:
                url1 = "https://esnet-netbeam.appspot.com/api/network/esnet/prod/"
                device = datum['resource']
                recordType = stats
                finalUrl = url1+device+'/'+recordType+'?{}'
                print(finalUrl)
                params = urllib.parse.urlencode({'begin': startDate, 'end': endDate})
                try:
                    with urllib.request.urlopen(finalUrl.format(params)) as url:
                        data = json.load(url)
                        points = data['points']
              
                        for point in points:
                            self.channel.basic_publish(exchange=self.exchange, routing_key=self.key2, body=json.dumps({"name" : device, "recordType" : recordType, 
                              "timestamp" : point[0] , "in" : point[1] , "out" : point[2]}), properties=pika.BasicProperties(content_type='text/plain', delivery_mode=1))
                            self.channel.confirm_delivery()
                   
                except (HTTPError):
                    print('No Record found')

stats = EsnetDataUploader()
stats.SendInterfacetoRMQ()
stats.SendStatsToRMQ('errors')
stats.SendStatsToRMQ('discards')
stats.SendStatsToRMQ('traffic')

esnet_collector.get_rabbitmq_connection().closeConnection()  
