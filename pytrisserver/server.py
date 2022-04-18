"""
    Server
"""
from PodSixNet.Server import Server

from pytrisserver.channel import ClientChannel
from pytrisserver.sessionmanager import SessionManager


class MyServer(Server):
    """
        Server
    """
    channelClass = ClientChannel

    def __init__(self, *args, **kwargs):
        self.id = 0
        Server.__init__(self, *args, **kwargs)
        self.session_manager = SessionManager()
        print('Server launched')

    def Connected(self, channel, addr):
        print(f'new connection at {channel.addr}')
