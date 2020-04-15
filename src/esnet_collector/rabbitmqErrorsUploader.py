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

print("Creating connection")
credentials = pika.PlainCredentials(username, passwd)
params = pika.ConnectionParameters(host=rabbithost, virtual_host=vhost, credentials=credentials)
params.socket_timeout = 5
connection = pika.BlockingConnection(params) # Connect to CloudAMQP
channel = connection.channel() # start a channel

with open("interface.csv", "r") as csv_file:
    csv_reader = csv.reader(csv_file, delimiter=',')
    for lines in csv_reader:
      url1 = "https://esnet-netbeam.appspot.com/api/network/esnet/prod/"
      device = lines[1].strip()
      recordType = '/errors?{}'
      finalUrl = url1+device+recordType 
      #print(finalUrl)
      date1 = int(datetime.datetime(2020, 4, 10, 20, 00, 00).timestamp() * 1000)
      date2 = int(datetime.datetime(2020, 4, 11, 20, 00, 00).timestamp() * 1000)
      params = urllib.parse.urlencode({'begin': date1, 'end': date2})
     
      try:
          with urllib.request.urlopen(finalUrl.format(params)) as url:
              data = json.load(url)
              points = data['points']
              
              for point in points:
                  record = 'errors'
                  interfaceData = json.dumps({"name" : device, "recordType" : record, "timestamp" : point[0] , "in" : point[1] , "out" : point[2]})
                  channel.basic_publish(exchange=exchange, routing_key=key, body=interfaceData, properties=pika.BasicProperties(content_type='text/plain',
                                                          delivery_mode=1))
                  channel.confirm_delivery()
                  
                  print("[x] Errors data from begin date", date1 ,"to end date", date2 , "sent to RabbitMQ bus at exchange osg.esdata.raw")  

      except (HTTPError):
          print('No Record found')

connection.close()  
