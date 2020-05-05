import rabbitmqconnect

# Shared RabbitMQ
rabbitmq_connect = None

def get_rabbitmq_connection():
    global rabbitmq_connect
    if rabbitmq_connect == None:
        rabbitmq_connect = rabbitmqconnect.RabbitMQConnect()
    return rabbitmq_connect