"""
    Main script for pytris server
"""
import json
import os.path
from time import sleep

from pytrisserver.server import MyServer

if __name__ == "__main__":
    server_param_path = "server_param.json"
    addr = ("localhost", 4242)
    if os.path.exists(server_param_path):
        address = "localhost"
        port = 4242
        with open(server_param_path, "r") as f:
            data = json.load(f)
            if "address" in data:
                address = data["address"]
            if "port" in data:
                port = data["port"]
        addr = (address, port)

    myserver = MyServer(localaddr=addr)
    while True:
        myserver.Pump()
        sleep(0.0001)
