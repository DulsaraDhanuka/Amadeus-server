import argparse
import json
import socket
import select
import time
import amadeus

parser = argparse.ArgumentParser(
                    prog='Amadeus server',
                    description='Start the amadeus server')

parser.add_argument('host', help='IP address of the server', default=socket.gethostbyname(socket.gethostname()))
parser.add_argument('port', help='Port of the server', default=9999)

args = parser.parse_args()

HEADER_LENGTH = 10
IP = args.host
PORT = args.port

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP, PORT))
server_socket.listen()

sockets_list = [server_socket]
clients = {}

class Device(object):
    def __init__(self, name, type):
        self._name = name
        self._type = type
    
    def getName(self):
        return self._name
    
    def getType(self):
        return self._type

def process_message(device, send, input_message):
    amadeus.process_input(input_message)

def receive_message(client_socket):
    try:
        messege_header = client_socket.recv(HEADER_LENGTH)
        if not len(messege_header):
            return False
        
        message_length = int(messege_header.decode("utf-8").strip())
        message = client_socket.recv(message_length).decode("utf-8")
        message = json.loads(message)
        return {"header": messege_header, "data": message}
    except:
        return False
    
def send_message(client_socket, message):
    message = json.dumps(message).encode("utf-8")
    header = f"{len(message):<{HEADER_LENGTH}}".encode("utf-8")
    client_socket.send(header + message)

def create_callable_send_message(client_socket):
    def callable_send_message(message):
        return send_message(client_socket, message)
    
    return callable_send_message

while True:
    read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)

    for notified_socket in read_sockets:
        if notified_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            init_data = receive_message(client_socket)
            if init_data is False:
                continue

            device = Device(init_data['data']['name'], init_data['data']['type'])

            sockets_list.append(client_socket)
            clients[client_socket] = device

            print(f"Accepted new connection from {client_address[0]}:{client_address[1]} Device: {device.getName()} Type: {device.getType()}")
        else:
            data = receive_message(notified_socket)

            if data is False:
                print(f"Closed connection from {clients[notified_socket].getName()}")
                sockets_list.remove(notified_socket)
                del clients[notified_socket]
                continue

            data = data['data']
            if data['type'] == 'text':
                process_message(clients[notified_socket], create_callable_send_message(notified_socket), data['data'])
                send_message(notified_socket, {'type': 'eof', 'data': True})
            else:
                print("Invalid message type received:", data)

    for notified_socket in exception_sockets:
        sockets_list.remove(notified_socket)
        del clients[notified_socket]
