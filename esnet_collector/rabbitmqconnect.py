from dotenv import load_dotenv
import pika
import os

class RabbitMQConnect:
    def __init__(self):
        #Load the environment file
        load_dotenv()
        self.username = os.getenv('rmq-user')
        self.passwd = os.getenv('rmq-pass')
        self.rabbithost = os.getenv('rmq-host')
        self.exchange = os.getenv('rmq-exchange')
        self.key1 = os.getenv('rmq-interface-key')
        self.key2 = os.getenv('rmq-traffic-key')
        self.vhost = os.getenv('rmq-vhost')
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

