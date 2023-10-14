import os
import copy
import json
import socket
import openai
from typing import List
from dotenv import load_dotenv
from simplesocks.server import SimpleServer

load_dotenv(override=True)

openai.api_key = os.getenv('OPENAI_API_KEY')

class AmadeusClient():
    def __init__(self, ip: str, port: int, client_name: str, client_type: str, function_specs: List[dict]) -> None:
        self.ip = ip
        self.port = port
        self.client_name = client_name
        self.client_type = client_type
        
        self.function_specs = function_specs
        for function_spec in self.function_specs:
            function_spec['name'] = self.get_server_function_name(function_spec['name'])

    def get_server_function_name(self, function_name: str) -> str:
        return f"{self.client_name}_{function_name}"

    def get_local_function_name(self, function_name: str) -> str:
        return function_name.replace(f"{self.client_name}_", "")

class AmadeusServer(SimpleServer):
    amadeus_clients = {}
    amadeus_function_specs = []
    
    messages = [{"role": "system", "content": "You're the personal AI assistant of Dulsara Dhanuka (Male). You're name is Amadeus. "}]

    def accept_client_connection(self, client_socket: socket.socket, client_address: tuple, initialization_data: object) -> None:
        super().accept_client_connection(client_socket, client_address, initialization_data)

        initialization_data = json.loads(initialization_data)['id']
        print(f"Client {client_address[0]}:{client_address[1]} connected as {initialization_data}")

    def handle_incoming_data(self, client_id: str, client_socket: socket.socket, data: bytes) -> None:
        super().handle_incoming_data(client_id, client_socket, data)

        data = json.loads(data.decode('utf-8'))
        if data['type'] == "register_client":
            ip, port = client_socket.getsockname()
            if client_id not in self.amadeus_clients:
                self.amadeus_clients[client_id] = AmadeusClient(ip, port, client_id, data['client_type'], data['function_specs'])
                self.amadeus_function_specs.extend(self.amadeus_clients[client_id].function_specs)
            else:
                print(f"Client {client_id} already registered")
        elif data['type'] == "prompt":
            prompt = data['prompt']
            self.handle_prompt(prompt, client_id, client_socket)
        elif data['type'] == "terminate_server":
            self.terminate_server()

    def close_client_connection(self, client_id: str, client_socket: socket.socket) -> None:
        super().close_client_connection(client_id, client_socket)
        print(f"Client {client_id} disconnected")

    def get_function_response(self, client_socket: socket.socket) -> str:
        data = self._receive_data(client_socket).decode('utf-8')
        data = json.loads(data)
        if data['type'] == 'function_response':
            return data['response']
        return None

    def handle_prompt(self, prompt: str, client_id: str, client_socket: socket.socket):
        self.messages.append({"role": "user", "content": prompt})
        
        local_messages = copy.deepcopy(self.messages)
        response = False
        while response is False or 'function_call' in response:
            completion = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=local_messages,
                functions=self.amadeus_function_specs,
                function_call="auto",  # auto is default, but we'll be explicit
            )
            response = completion['choices'][0]['message']
            local_messages.append(response)

            if 'function_call' in response:
                func_name = self.amadeus_clients[client_id].get_local_function_name(response['function_call']['name'])
                self.send_client_data(client_socket, json.dumps({'type': 'function_call', 'name': func_name}).encode('utf-8'))
                
                func_resp = self.get_function_response(client_socket)
                local_messages.append({"role": "function", "name": response['function_call']['name'], "content": func_resp})
        self.messages.append(response)
        self.send_client_data(client_socket, json.dumps({'type': 'response', 'response': response['content']}).encode('utf-8'))
        self.send_client_data(client_socket, json.dumps({'type': 'eol'}).encode('utf-8'))

server = AmadeusServer(server_key=b"KJEodzwQhl7NfZjWcqw4HEgeKV7DrMz-o8xWy4vaW-c=")
server.listen()