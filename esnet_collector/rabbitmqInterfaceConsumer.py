from dotenv import load_dotenv
import urllib.request
import json
import pika, os

load_dotenv()
username = os.getenv('rmq-user')
passwd = os.getenv('rmq-pass')
rabbithost = os.getenv('rmq-host')
vhost = os.getenv('rmq-vhost')
key = os.getenv('rmq-interface-key')
exchange = os.getenv('rmq-exchange')

print("Creating connection")
credentials = pika.PlainCredentials(username, passwd)
params = pika.ConnectionParameters(host=rabbithost, virtual_host=vhost, credentials=credentials)
params.socket_timeout = 5
connection = pika.BlockingConnection(params) # Connect to CloudAMQP
channel = connection.channel() # start a channel
        
def callback(ch, method, properties, body):
    data = json.loads(body)
    print(" [x] Message Received")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue=exchange, on_message_callback=callback)

channel.start_consuming()