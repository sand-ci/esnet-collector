from rabbitmqconnect import RabbitMQConnect, get_rabbitmq_connection
from datetime import date, datetime, timedelta
from socket import error as SocketError
from multiprocessing import Process
from urllib.error import HTTPError
import mysql.connector
import urllib.request
import urllib.parse
import urllib3.util
import threading
import requests
import errno
import time
import json
import pika
import csv
import sys
import os
import re


class EsnetStatsUploader():

    def __init__(self, sleep=30, low_water=30000, high_water=50000):

        self.url = get_rabbitmq_connection().rabbithost
        self.exchange = get_rabbitmq_connection().exchange
        self.username = get_rabbitmq_connection().username
        self.passwd = get_rabbitmq_connection().passwd
        self.vhost = get_rabbitmq_connection().vhost
        self.key1 = get_rabbitmq_connection().key1
        self.key2 = get_rabbitmq_connection().key2
        self.sleep = sleep
        self.low_water = low_water
        self.high_water = high_water
        self.batchSize = 5760

        credentials = pika.PlainCredentials(self.username, self.passwd)
        self.params = pika.ConnectionParameters(
            host=self.url, virtual_host=self.vhost, credentials=credentials, heartbeat=0)
        self.connection = pika.BlockingConnection(self.params)  # Connect to CloudAMQP
        self.channel = get_rabbitmq_connection().createChannel()

        # Make RabbitMQ REST API URL from AMQP URL
        u_parse = urllib3.util.parse_url(self.url)
        self.api_url = urllib3.util.url.Url('http', '{}:{}'.format(self.username, self.passwd), u_parse.hostname, None, '/api/queues/' + self.vhost).url

        # Use a session for connection pooling
        self.session = requests.Session()

    def getMsgInQueue(self):
        '''Query RabbitMQ API and return total number of messages in queue. Retries as needed.'''
        while True:
            try:
                # Request stats from API
                resp = self.session.get(self.api_url)
                resp.raise_for_status()

                # Sum the waiting messages for all queues
                # API might return OK, but not have a 'messages' key
                msg_count = sum([c['messages'] for c in resp.json()])
                return msg_count
            except (requests.exceptions.RequestException, KeyError) as e:
                print('RabbitMQ API error. Waiting to recheck.')
                print(e)
                self.connection.sleep(60)
                continue

    def batchSleep(self):
        '''Sleep between message batches'''
        # Get the number of messages
        msg_count = self.getMsgInQueue()
        timestamp = datetime.utcnow()

        # We're above the HWM. Stop sending for an additional 2x sleep and then check again
        while msg_count > self.high_water:
            print("Time : {} , Message count of {} is above high-water mark of {}. Waiting to recheck msg count...".format(
                timestamp, msg_count, self.high_water))
            self.connection.sleep(self.sleep)
            timestamp = datetime.utcnow()
            msg_count = self.getMsgInQueue()

        if msg_count < self.low_water:
            print("Time : {} , Message count of {} is below low-water mark of {}. Continuing.".format(
                timestamp, msg_count, self.low_water))
            return

    def SendStatsToRMQ(self, stats):
        
        db_connect = mysql.connector.connect(host="localhost", user="root", password="", database="esnet" )
        my_cursor = db_connect.cursor(buffered=True)
        my_cursor1 = db_connect.cursor(buffered=True)
        sql_query = "select name, active_until, traffic_until, discards_until, traffic_until from int_test where status != 0"
        my_cursor.execute(sql_query)
        datum = my_cursor.fetchone()
        self.startTime = datum[2]

        now = datetime.now()
        print(now)
        twoMinutesAgo = now - \
            timedelta(minutes=30, seconds=now.second,
                      microseconds=now.microsecond)
        nowInMinutes = now - \
            timedelta(minutes=15, seconds=now.second, microseconds=now.microsecond)

        if self.startTime is None and self.endTime is None:
            self.startTime = round(twoMinutesAgo.timestamp()*1000)
            self.endTime = round(nowInMinutes.timestamp()*1000)

        f = open('timeCollector.txt', 'a')
        while (int(self.startTime) < int(self.endTime)):
            
            while datum is not None:
                url1 = "https://esnet-netbeam.appspot.com/api/network/esnet/prod/"
                device = datum[1]
                recordType = stats
                finalUrl = url1+device+'/'+recordType+'?{}'
                print(finalUrl, self.startTime, self.endTime )
                counter = 0

                params = urllib.parse.urlencode({'begin': self.startTime, 'end': self.endTime})
                update_query = "UPDATE int_test1 SET errors_until = %s WHERE name = %s AND id= %s"
                my_cursor1.execute(update_query, (self.checkpoint.endTime, datum[1], datum[0]))
                db_connect.commit()

                try:
                    with urllib.request.urlopen(finalUrl.format(params)) as url:
                        data = json.load(url)
                        points = data['points']

                        for point in points:
                            self.channel.basic_publish(exchange=self.exchange, routing_key=self.key2, body=json.dumps({"name": device, "recordType": recordType,
                                                                                                                           "timestamp": point[0], "in": point[1], "out": point[2]}), properties=pika.BasicProperties(content_type='text/plain', delivery_mode=1))

                            counter += 1
                            if (counter % self.batchSize) == 0:
                                self.batchSleep()

                except (HTTPError):
                        print('No Record found')
                except json.decoder.JSONDecodeError:
                        print('No Record found')
                except IndexError:
                        print('No Record found')
                except SocketError as e:
                    if e.errno != errno.ECONNRESET:
                        raise
                        pass

                datum = my_cursor.fetchone()

        else:
            print("Start time not less than end time .... exiitng loop")

    def RunInParallel(self):
        stats = EsnetStatsUploader()
        statType = ['traffic', 'errors', 'discards']
        for i in statType:
            p = Process(target=stats.SendStatsToRMQ, args=[i])
            p.start()
            p.join()


stats = EsnetStatsUploader()
stats.RunInParallel()

get_rabbitmq_connection().closeConnection()
