"""
    Server-client channel
"""
import os
import string
import random
from base64 import b64encode
from typing import Dict

from PodSixNet.Channel import Channel

from pytrisserver.sessionmanager import SessionManager


class ClientChannel(Channel):
    """
        Client channel
    """
    def __init__(self, *args, **kwargs):
        Channel.__init__(self, *args, **kwargs)
        self.session_manager: SessionManager = self._server.session_manager
        self.session_id = None

    def Network(self, data):
        print(f"data received : {data}")

    def Network_join_session(self, data):
        to_send = {"action": "session_join", "status": "OK"}
        if "session_id" not in data:
            to_send["status"] = "Session ID was not given"
        else:
            session_id = data["session_id"]
            res = self.session_manager.join_session(session_id, self.addr)
            if res is None:
                self.session_id = session_id
            else:
                to_send["status"] = res
        self.Send(to_send)

    def Network_top_out(self, data):
        to_send = {"action": "top_out_ack", "status": "OK"}
        if "session_id" in data:
            session_id = data["session_id"]
            res = self.session_manager.delete_session(session_id, self.addr)
            if res is None:
                self.session_id = None
            else:
                to_send["status"] = res
        self.Send(to_send)

    def Network_get_session_id(self, data):
        self.Send({"action": "session_id", "session_id": self.session_manager.get_new_session_id()})

    def Network_get_session(self, data):
        send_back = {"action": "session_data", "status": "OK"}
        if "session_id" not in data:
            send_back["status"] = "Session ID was not given"
        else:
            session_id = data["session_id"]
            send_back["data"] = self.session_manager.get_session(session_id)
        self.Send(send_back)

    def Network_update_session(self, data):
        send_back = {"action": "update_session_ack", "status": "OK"}
        if "session_id" not in data:
            send_back["status"] = "Session ID was not given"
        else:
            session_id = data["session_id"]
            res = self.session_manager.update_session(session_id, self.addr, data["data"])
            if res:
                send_back["status"] = res
        self.Send(send_back)

    def Close(self):
        print(f"{self.addr} connection closed")
        if self.session_id:
            self.session_manager.leave_session(self.session_id, self.addr)
