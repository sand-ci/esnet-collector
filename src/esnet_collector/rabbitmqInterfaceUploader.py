from dotenv import load_dotenv
import urllib.request
import json
import pika, os

load_dotenv()
username = os.getenv('rmq-user')
passwd = os.getenv('rmq-pass')
rabbithost = os.getenv('rmq-host')
exchange = os.getenv('rmq-exchange')
key = os.getenv('rmq-interface-key')
vhost = os.getenv('rmq-vhost')

print("Creating connection")
credentials = pika.PlainCredentials(username, passwd)
params = pika.ConnectionParameters(host=rabbithost, virtual_host=vhost, credentials=credentials)
params.socket_timeout = 5
connection = pika.BlockingConnection(params) # Connect to CloudAMQP
channel = connection.channel() # start a channel

with urllib.request.urlopen("https://esnet-netbeam.appspot.com/api/network/esnet/prod/interfaces") as url:
    data = json.loads(url.read().decode())

interfaceData = json.dumps(data)

channel.basic_publish(exchange=exchange, routing_key=key, body=interfaceData, properties=pika.BasicProperties(content_type='text/plain',
                                                          delivery_mode=1))

channel.confirm_delivery()
        
print("[x] Interface Data sent to OSG RabbitMQ bus")
connection.close()
