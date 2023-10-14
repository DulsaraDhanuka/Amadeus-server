import json
import socket
from typing import List
from simplesocks.client import SimpleClient

class AmadeusClient(SimpleClient):
    def __init__(self, ip, port, client_name: str, client_type: str, functions: List[dict], callables: dict, server_key=None):
        super().__init__(ip, port, server_key=server_key, connection_id=client_name)
        self.callables = callables

        self.send_data(json.dumps({'type': 'register_client', 'client_type': client_type, 'function_specs': functions}).encode('utf-8'))

    def execute_prompt(self, prompt: str):
        response: str = ""
        self.send_data(json.dumps({'type': 'prompt', 'prompt': prompt}).encode('utf-8'))
        while True:
            data = json.loads(self.receive_data(timeout=30).decode('utf-8'))
            if data['type'] == 'eol':
                break
            elif data['type'] == 'function_call':
                if data['name'] in self.callables:
                    self.send_data(json.dumps({'type': 'function_response', 'response': self.callables[data['name']]()}).encode('utf-8'))
            elif data['type'] == 'response':
                response = data['response']

        return response

def get_current_time():
    from datetime import datetime
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    return current_time

functions = [
    {
        "name": "get_current_time",
        "description": "Gets the current time",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        }
    }
]

callables = {
    "get_current_time": get_current_time
}
client = AmadeusClient('192.168.1.200', 4444, 'project_server', "windows_10", functions, callables, server_key=b"KJEodzwQhl7NfZjWcqw4HEgeKV7DrMz-o8xWy4vaW-c=")
#print(client.execute_prompt("Hi"))
print(client.execute_prompt("What is the current time"))
client.send_data(json.dumps({'type': 'terminate_server'}).encode('utf-8'))