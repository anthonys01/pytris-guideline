"""
    Server
"""
from PodSixNet.Server import Server

from pytrisserver.channel import ClientChannel


class MyServer(Server):
    """
        Server
    """
    channelClass = ClientChannel

    def Connected(self, channel, addr):
        print(f'new connection: {channel} at {addr}')
