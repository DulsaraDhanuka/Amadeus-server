from typing import List


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
