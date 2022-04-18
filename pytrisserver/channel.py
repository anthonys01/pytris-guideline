"""
    Server-client channel
"""
import os
import string
import random
from base64 import b64encode
from typing import Dict

from PodSixNet.Channel import Channel


class ClientChannel(Channel):
    """
        Client channel
    """
    def __init__(self, *args, **kwargs):
        self.sessions: Dict[str, dict] = {}
        if "sessions" in kwargs:
            self.sessions = kwargs["sessions"]
        Channel.__init__(self, *args, **kwargs)

    def _generate_session_id(self):
        letters = string.ascii_lowercase
        res = ''.join(random.choice(letters) for _ in range(10))
        while res in self.sessions:
            res = ''.join(random.choice(letters) for _ in range(10))
        return res

    def make_new_session(self, session_id):
        self.sessions[session_id] = {
            "seed": b64encode(os.urandom(64)).decode('utf-8'),
            "current_piece": None,
            "hold_piece": None,
            "holt": False,
            "piece_count": 0,
            "cells": [],
            "timer": 0,
            "stats": {
                "Level": 1,
                "Lines cleared": 0,
                "Score": 0,
                "B2B": -1,
                "Combo": -1,
                "T-spin": 0,
                "T-spin mini": 0,
                "T-spin Single": 0,
                "T-spin Double": 0,
                "T-spin Triple": 0,
                "T-spin mini Single": 0,
                "T-spin mini Double": 0,
                "Single": 0,
                "Double": 0,
                "Triple": 0,
                "Quad": 0,
                "Max combo": 0,
                "Max Back-to-Back": 0,
                "Perfect Clears": 0,
                "Successive PC": 0,
                "Max successive PC": 0,
                "Pieces since PC": 0
            },
            "grid": [[0] * 10 for _ in range(22)]
        }

    def Network(self, data):
        print(f"data received : {data}")

    def Network_get_session_id(self, data):
        print(f"data received : {data}")
        session_id = self._generate_session_id()
        self.make_new_session(session_id)
        self.Send({"action": "session_id", "session_id": session_id})

    def Network_get_session(self, data):
        print(f"data received : {data}")
        send_back = {"action": "session_data", "status": "OK"}
        if "session_id" not in data:
            send_back["status"] = "Session ID was not given"
        else:
            session_id = data["session_id"]
            if session_id not in self.sessions:
                self.make_new_session(session_id)
            send_back["data"] = self.sessions[session_id]
        self.Send(send_back)

    def Network_update_session(self, data):
        print(f"data received : {data}")
        send_back = {"action": "update_session_ack", "status": "OK"}
        if "session_id" not in data:
            send_back["status"] = "Session ID was not given"
        else:
            session_id = data["session_id"]
            if session_id not in self.sessions:
                send_back["status"] = "Session does not exist"
            else:
                self.sessions[session_id].update(data["data"])
        self.Send(send_back)
