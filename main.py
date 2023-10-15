import logging
import os
import openai
from dotenv import load_dotenv
from server import AmadeusServer

load_dotenv(override=True)
openai.api_key = os.getenv('OPENAI_API_KEY')

server = AmadeusServer(server_key=b"KJEodzwQhl7NfZjWcqw4HEgeKV7DrMz-o8xWy4vaW-c=")
server.listen()
