import os
import threading

os.makedirs("logs", exist_ok=True)

BUFFERSIZE: int = 1024
PROTOCOL_VERSION = 1.0
SERVER_PORT = 40000

rooms = []
active_clients = {}
lock = threading.Lock()
