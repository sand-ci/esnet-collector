from dotenv import load_dotenv
import pika
import os

# Shared RabbitMQ
rabbitmq_connect = None

def get_rabbitmq_connection():
    global rabbitmq_connect
    if rabbitmq_connect == None:
        rabbitmq_connect = RabbitMQConnect()
    return rabbitmq_connect


class RabbitMQConnect:
    def __init__(self):
        #Load the environment file
        load_dotenv()
        self.username = os.getenv('RMQ_USER')
        self.passwd = os.getenv('RMQ_PASS')
        self.rabbithost = os.getenv('RMQ_HOST')
        self.exchange = os.getenv('RMQ_EXCHANGE')
        self.key1 = os.getenv('RMQ_INTERFACE_KEY')
        self.key2 = os.getenv('RMQ_TRAFFICE_KEY')
        self.vhost = os.getenv('RMQ_VHOST')
        self.createConnection()

    def createConnection(self):
        #Connect to the bus
        credentials = pika.PlainCredentials(self.username, self.passwd)
        self.params = pika.ConnectionParameters(host=self.rabbithost, virtual_host=self.vhost, credentials=credentials)
        self.connection = pika.BlockingConnection(self.params) # Connect to CloudAMQP
    
    def createChannel(self):
        #Create a channel and return it
        if not self.connection.is_open:
            self.createConnection()
            print("Creating Connection")
        return self.connection.channel() # start a channel

    def closeConnection(self):
        return self.connection.close()

