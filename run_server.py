"""
    Main script for pytris server
"""
from time import sleep

from pytrisserver.server import MyServer

if __name__ == "__main__":
    myserver = MyServer(localaddr=("localhost", 4242))
    while True:
        myserver.Pump()
        sleep(0.0001)
