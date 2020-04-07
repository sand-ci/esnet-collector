from dotenv import load_dotenv
import datetime
import urllib.request
import urllib.parse
import json
import csv
import pika, os
from urllib.error import HTTPError

load_dotenv()
username = os.getenv('rmq-user')
passwd = os.getenv('rmq-pass')
rabbithost = os.getenv('rmq-host')
exchange = os.getenv('rmq-exchange')
key = os.getenv('rmq-traffic-key')
vhost = os.getenv('rmq-vhost')

with open("interface1.csv", "r") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for lines in csv_reader:
      url1 = "https://esnet-netbeam.appspot.com/api/network/esnet/prod/"
      device = lines[1].strip()
      recordType = '/traffic?{}'
      finalUrl = url1+device+recordType 
      #print(finalUrl)
      date1 = int(datetime.datetime(2020, 4, 3, 20, 00, 00).timestamp() * 1000)
      date2 = int(datetime.datetime(2020, 4, 4, 20, 00, 00).timestamp() * 1000)
      params = urllib.parse.urlencode({'begin': date1, 'end': date2})

      try:
          with urllib.request.urlopen(finalUrl.format(params)) as url:
              data = json.loads(url.read().decode())
              data['recordType'] = 'traffic'
          interfaceData = json.dumps(data)
      except (HTTPError):
          print('No Record found')

print("Creating connection")
credentials = pika.PlainCredentials(username, passwd)
params = pika.ConnectionParameters(host=rabbithost, virtual_host=vhost, credentials=credentials)
params.socket_timeout = 5
connection = pika.BlockingConnection(params) # Connect to CloudAMQP
channel = connection.channel() # start a channel

channel.basic_publish(exchange=exchange, routing_key=key, body=interfaceData, properties=pika.BasicProperties(content_type='text/plain',
                                                          delivery_mode=1))

channel.confirm_delivery()

print("[x] Traffic data from begin date", date1 ,"to end date", date2 , "sent to RabbitMQ bus at exchange osg.esdata.raw") 
