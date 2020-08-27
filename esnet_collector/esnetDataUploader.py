from rabbitmqconnect import RabbitMQConnect, get_rabbitmq_connection
from datetime import date, datetime, timedelta
from multiprocessing import Process
from urllib.error import HTTPError
from timeCheck import TimeCheck
import urllib.request
import urllib.parse
import urllib3.util
import threading
import requests
import time
import json
import pika
import csv
import sys
import os


class EsnetDataUploader():

    checkpoint = os.path.join(os.getcwd(), "checktime")

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
            host=self.url, virtual_host=self.vhost, credentials=credentials, heartbeat=10)
        self.connection = pika.BlockingConnection(
            self.params)  # Connect to CloudAMQP
        self.channel = get_rabbitmq_connection().createChannel()

        # Make RabbitMQ REST API URL from AMQP URL
        u_parse = urllib3.util.parse_url(self.url)
        self.api_url = urllib3.util.url.Url('https', '{}:{}'.format(
            self.username, self.passwd), u_parse.hostname, None, '/api/queues/' + self.vhost).url
        # Use a session for connection pooling
        self.session = requests.Session()

        if self.checkpoint:
            checkpoint_file = os.path.join(os.getcwd(), "checktime")
        else:
            checkpoint_file = None

        self.checkpoint = TimeCheck(checkpoint_file)

        now = datetime.utcnow()
        twoMinutesAgo = now - \
            timedelta(minutes=2, seconds=now.second,
                      microseconds=now.microsecond)
        nowInMinutes = now - \
            timedelta(seconds=now.second, microseconds=now.microsecond)

        if self.checkpoint.startTime is None and self.checkpoint.endTime is None:
            self.checkpoint.startTime = round(twoMinutesAgo.timestamp()*1000)
            self.checkpoint.endTime = round(nowInMinutes.timestamp()*1000)

        print(self.checkpoint.startTime, self.checkpoint.endTime)

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
            print("Time : {} , Message count of {} is above high-water mark of {}. Waiting to recheck.".format(
                timestamp, msg_count, self.high_water))
            self.connection.sleep(self.sleep)
            self.channel = get_rabbitmq_connection().createChannel()
            msg_count = self.getMsgInQueue()

        if msg_count < self.low_water:
            print("Time : {} , Message count of {} is below low-water mark of {}. Continuing.".format(
                timestamp, msg_count, self.low_water))
            return

    def SendInterfacetoRMQ(self):

        with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
            data = json.load(url)
            counter = 0

            for datum in data:
                seconds = datetime.utcnow().timestamp()
                timestamp_in_millis = round(seconds * 1000)
                datum['timestamp'] = timestamp_in_millis
                self.channel.basic_publish(exchange=self.exchange, routing_key=self.key1, body=json.dumps(datum), properties=pika.BasicProperties(content_type='text/plain',
                                                                                                                                                  delivery_mode=1))
                counter += 1
                print("[x] Interface data sent to OSG RabbitMQ bus")

    def SendStatsToRMQ(self, stats):

        f = open('timeCollector.txt', 'a')
        while (int(self.checkpoint.startTime) < int(self.checkpoint.endTime)):
            tmp_endTime = int(self.checkpoint.startTime) + 48*3600*1000
            print(self.checkpoint.startTime, tmp_endTime,
                  self.checkpoint.endTime, file=f)

            with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
                data = json.load(url)
                counter = 0

                for datum in data:
                    url1 = "https://esnet-netbeam.appspot.com/api/network/esnet/prod/"
                    device = datum['resource']
                    recordType = stats
                    finalUrl = url1+device+'/'+recordType+'?{}'
                    print(finalUrl)

                    params = urllib.parse.urlencode(
                        {'begin': self.checkpoint.startTime, 'end': tmp_endTime})
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

            self.checkpoint.startTime = tmp_endTime

        else:
            print("Start time not less than end time .... exiitng loop")

    def RunInParallel(self):
        stats = EsnetDataUploader()
        statType = ['traffic', 'discards', 'errors']
        for i in statType:
            p = Process(target=stats.SendStatsToRMQ, args=[i])
            p.start()
            p.join()

            while p.is_alive():
                print('Heart Beating ...')
                self.connection.process_data_events()
                self.connection.sleep(5)


stats=EsnetDataUploader()
stats.SendInterfacetoRMQ()
stats.RunInParallel()

get_rabbitmq_connection().closeConnection()
