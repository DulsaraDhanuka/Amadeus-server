import json
import AppOpener
from typing import List
from datetime import datetime
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
                    function_name = data['name']
                    arguments = data['arguments']
                    can_execute_functions = input(f"Execute function {function_name}? (Y/n) -> ")
                    if can_execute_functions.lower() == "y":
                        self.send_data(json.dumps({'type': 'function_response', 'response': self.callables[function_name](**arguments)}).encode('utf-8'))
                    else:
                        self.send_data(json.dumps({'type': 'function_response', 'response': "Permission denied"}).encode('utf-8'))
            elif data['type'] == 'response':
                response = data['response']

        return response

def get_current_time():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    return current_time

def open_desktop_app(app_name):
    AppOpener.open(app_name)

    return "Done."

functions = [
    {
        "name": "get_current_time",
        "description": "Gets the current time",
        "parameters": {
            "type": "object",
            "properties": {},
            "required": [],
        }
    },
    {
        "name": "open_desktop_app",
        "description": "Opens a application in dekstop pc",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "The name of the application to open"
                }
            },
            "required": ["app_name"],
        }
    }
]

callables = {
    "get_current_time": get_current_time,
    "open_desktop_app": open_desktop_app,
}

client = AmadeusClient('192.168.1.200', 9998, 'project_server', "Windows 10", functions, callables)#, server_key=b"KJEodzwQhl7NfZjWcqw4HEgeKV7DrMz-o8xWy4vaW-c=")
while True:
    prompt = input("(Dulsara) > ")
    if prompt == "TERMINATE":
        client.send_data(json.dumps({'type': 'terminate_server'}).encode('utf-8'))
        break
    
    print(f"(Amadeus) > {client.execute_prompt(prompt)}")
