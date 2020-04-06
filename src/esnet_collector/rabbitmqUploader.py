import urllib.request
import json
import pika, os

print("Creating connection")
url = os.environ.get('CLOUDAMQP_URL', 'amqps://username:password@rmqhost:5671/vhost?socket_timeout=10&connection_attempts=5')
params = pika.URLParameters(url)
params.socket_timeout = 5
connection = pika.BlockingConnection(params) # Connect to CloudAMQP
channel = connection.channel() # start a channel

with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
    data = json.loads(url.read().decode())

interfaceData = json.dumps(data)
       
channel.basic_publish(exchange='osg.esdata.raw', routing_key='esnetdata', body=interfaceData, properties=pika.BasicProperties(content_type='text/plain',
                                                          delivery_mode=1))
channel.confirm_delivery()
        
print("[x] Data sent to OSG RabbitMQ bus")
connection.close()