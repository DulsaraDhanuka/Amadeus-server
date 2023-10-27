import copy
import json
import socket
import openai
from client import AmadeusClient
from simplesocks.server import SimpleServer

class AmadeusServer(SimpleServer):
    amadeus_clients = {}
    
    messages = [{"role": "system", "content": "You're the personal AI assistant of Dulsara Dhanuka (Male). You're name is Amadeus. "}]

    def __init__(self, host: str = None, port: int = 9999, header_length: int = 10, server_key: bytes = None) -> None:
        super().__init__(host, port, header_length, server_key)
        ip_address, port = self._socket.getsockname()

    def accept_client_connection(self, client_socket: socket.socket, client_address: tuple, initialization_data: object) -> None:
        super().accept_client_connection(client_socket, client_address, initialization_data)

        client_id = json.loads(initialization_data.decode("utf-8"))['id']
        print(f"Client {client_address[0]}:{client_address[1]} connected as {client_id}")

    def handle_incoming_data(self, client_id: str, client_socket: socket.socket, data: bytes) -> None:
        super().handle_incoming_data(client_id, client_socket, data)

        ip, port = client_socket.getpeername()
        data = json.loads(data.decode('utf-8'))
        if data['type'] == "register_client":
            if client_id not in self.amadeus_clients:
                self.amadeus_clients[client_id] = AmadeusClient(ip, port, client_id, data['client_type'], data['function_specs'])
            else:
                print(f"Client {client_id} already registered")
                self.close_client_connection(client_id, client_socket, server_request=True)
        elif data['type'] == "prompt":
            prompt = data['prompt']
            self.handle_prompt(prompt, client_id, client_socket)
        elif data['type'] == "terminate_server":
            self.terminate_server()

    def close_client_connection(self, client_id: str, client_socket: socket.socket, server_request: bool=False) -> None:
        super().close_client_connection(client_id, client_socket)
        if client_id in self.amadeus_clients:
            del self.amadeus_clients[client_id]

        if not server_request:
            print(f"Client {client_id} disconnected")

    def get_function_response(self, client_socket: socket.socket) -> str:
        data = self._receive_data(client_socket).decode('utf-8')
        data = json.loads(data)
        if data['type'] == 'function_response':
            return data['response']
        return None

    def handle_prompt(self, prompt: str, client_id: str, client_socket: socket.socket):
        function_specs = []
        for _, client in self.amadeus_clients.items():
            function_specs.extend(client.function_specs)

        self.messages.append({"role": "user", "content": prompt})
        
        local_messages = copy.deepcopy(self.messages)
        response = False
        while response is False or 'function_call' in response:
            if len(function_specs) > 0:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=local_messages,
                    functions=function_specs,
                    function_call="auto",  # auto is default, but we'll be explicit
                )
            else:
                completion = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=local_messages,
                )
            response = completion['choices'][0]['message']
            local_messages.append(response)

            if 'function_call' in response:
                func_name = self.amadeus_clients[client_id].get_local_function_name(response['function_call']['name'])
                func_arguments = json.loads(response['function_call']['arguments'])
                self.send_client_data(client_socket, json.dumps({'type': 'function_call', 'name': func_name, 'arguments': func_arguments}).encode('utf-8'))
                
                func_resp = self.get_function_response(client_socket)
                local_messages.append({"role": "function", "name": response['function_call']['name'], "content": func_resp})
        self.messages.append(response)
        self.send_client_data(client_socket, json.dumps({'type': 'response', 'response': response['content']}).encode('utf-8'))
        self.send_client_data(client_socket, json.dumps({'type': 'eol'}).encode('utf-8'))
