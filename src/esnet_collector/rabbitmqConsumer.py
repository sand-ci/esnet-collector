import urllib.request
import json
import pika, os

print("Creating connection")
url = os.environ.get('CLOUDAMQP_URL', 'amqps://username:password@rmqhost:5671/vhost?socket_timeout=10&connection_attempts=5')
params = pika.URLParameters(url)
params.socket_timeout = 5
connection = pika.BlockingConnection(params) # Connect to CloudAMQP
channel = connection.channel() # start a channel
        
def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)

channel.basic_consume(queue='osg.esdata.raw', on_message_callback=callback)

channel.start_consuming()