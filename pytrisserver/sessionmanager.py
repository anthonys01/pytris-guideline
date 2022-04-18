"""
    Manage sessions lifecycle
"""
import json
import os
import string
import random
import time
from base64 import b64encode
from typing import Optional


class SessionManager:
    """
        Session manager
    """

    SESSIONS_FILE_PATH = "sessions.json"

    def __init__(self):
        self.sessions: dict = {}
        self.session_users = {}
        if os.path.exists(self.SESSIONS_FILE_PATH):
            with open(self.SESSIONS_FILE_PATH, 'r') as f:
                self.sessions: dict = json.load(f)

    def _save(self):
        with open(self.SESSIONS_FILE_PATH, 'w') as f:
            json.dump(self.sessions, f)

    def _generate_session_id(self):
        letters = string.ascii_lowercase
        res = ''.join(random.choice(letters) for _ in range(10))
        while res in self.sessions:
            res = ''.join(random.choice(letters) for _ in range(10))
        return res

    def _new_session(self, session_id):
        self.sessions[session_id] = {
            "metadata": {
                "last_update": time.time()
            },
            "data": {
                "seed": b64encode(os.urandom(64)).decode('utf-8'),
                "current_piece": None,
                "hold_piece": None,
                "holt": False,
                "piece_count": 0,
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
        }
        self._save()

    def get_session(self, session_id) -> dict:
        if session_id not in self.sessions:
            self._new_session(session_id)
        if session_id not in self.session_users:
            self.session_users[session_id] = None
        return self.sessions[session_id]["data"]

    def join_session(self, session_id, player) -> Optional[str]:
        self.get_session(session_id)
        if self.session_users[session_id] is not None:
            return "Session is already used"
        self.session_users[session_id] = player

    def leave_session(self, session_id, player):
        self.get_session(session_id)
        if self.session_users[session_id] == player:
            self.session_users[session_id] = None

    def get_new_session_id(self) -> str:
        session_id = self._generate_session_id()
        self._new_session(session_id)
        return session_id

    def delete_session(self, session_id, player) -> Optional[str]:
        if session_id not in self.sessions:
            return "Session does not exist"
        if self.session_users[session_id] != player:
            return "Player is not in session"
        self.sessions.pop(session_id)
        self.session_users.pop(session_id)
        self._save()

    def update_session(self, session_id, player, data) -> Optional[str]:
        """
            return None if everything is OK, an error message if update failed
        """
        if session_id not in self.sessions:
            return "Session does not exist"
        if self.session_users[session_id] != player:
            return "Player is not in session"

        self.sessions[session_id]["data"].update(data)
        self.sessions[session_id]["metadata"]["last_update"] = time.time()
        self._save()
