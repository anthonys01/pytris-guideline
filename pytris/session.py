"""
    Represents a game session, local or online
"""
import json
import os
import random
from base64 import b64encode

from PodSixNet.Connection import ConnectionListener, connection


class GameSession(ConnectionListener):
    """
        Game session, managing the session data state
    """

    GAME_SERVER_FILE_PATH = "data/game_server.json"

    def __init__(self, session_id: str = None):
        self.session_id = session_id

        self.randomizer = None
        self.seed = None
        self.current_piece = None
        self.hold_piece = None
        self.holt = False
        self.queue = []
        self.piece_count = 0
        self.timer = 0
        self.stats = {}
        self.grid = []

        self.session_ready = False
        self.error_msg = None

        self.server_addr = ("localhost", 4242)
        if os.path.exists(self.GAME_SERVER_FILE_PATH):
            address = "localhost"
            port = 4242
            with open(self.GAME_SERVER_FILE_PATH, "r") as f:
                data = json.load(f)
                if "address" in data:
                    address = data["address"]
                if "port" in data:
                    port = data["port"]
            self.server_addr = (address, port)

        self.load_from_server()

    def exit_session(self):
        if self.session_id is not None:
            connection.Close()

    def get_general_stats(self) -> dict:
        general_stats = {
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
            "Perfect Clears": 0
        }
        for stat in general_stats:
            general_stats[stat] = self.stats[stat]
        return general_stats

    @property
    def successive_pc(self):
        return self.stats["Successive PC"]

    @successive_pc.setter
    def successive_pc(self, new_successive):
        self.stats["Successive PC"] = new_successive

    @property
    def max_successive_pc(self):
        return self.stats["Max successive PC"]

    @max_successive_pc.setter
    def max_successive_pc(self, new_max):
        self.stats["Max successive PC"] = new_max

    @property
    def level(self):
        return self.stats["Level"]

    @level.setter
    def level(self, new_level):
        self.stats["Level"] = new_level

    @property
    def lines_cleared(self):
        return self.stats["Lines cleared"]

    @lines_cleared.setter
    def lines_cleared(self, new_cleared):
        self.stats["Lines cleared"] = new_cleared

    @property
    def pieces_since_pc(self):
        return self.stats["Pieces since PC"]

    @pieces_since_pc.setter
    def pieces_since_pc(self, pieces_nb):
        self.stats["Pieces since PC"] = pieces_nb

    @property
    def used_pieces(self):
        return self.piece_count \
                - (1 if self.hold_piece is not None else 0) \
                - (1 if self.current_piece is not None else 0)

    @property
    def score(self):
        return self.stats["Score"]

    @score.setter
    def score(self, new_score):
        self.stats["Score"] = new_score

    @property
    def combo(self):
        return self.stats["Combo"]

    @combo.setter
    def combo(self, new_combo):
        self.stats["Combo"] = new_combo

    @property
    def back_to_back(self):
        return self.stats["B2B"]

    @back_to_back.setter
    def back_to_back(self, new_b2b):
        self.stats["B2B"] = new_b2b

    def _init_local_session(self):
        self.current_piece = None
        self.hold_piece = None
        self.holt = False
        self.queue = []
        self.piece_count = 0
        self.timer = 0
        self.seed = b64encode(os.urandom(64)).decode('utf-8')
        self.randomizer = random.Random(self.seed)
        self.grid = [[0] * 10 for _ in range(22)]
        self.stats = {
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
        }

    def reset(self):
        if self.session_id is None:
            self._init_local_session()

    def update(self):
        if self.session_id:
            connection.Pump()
            self.Pump()

    def update_time(self, time_delta):
        self.timer += time_delta

    def load_from_server(self):
        if self.session_id is None:
            self._init_local_session()
            self.session_ready = True
        else:
            self.Connect(self.server_addr)
            if self.session_id == "NEW_ID":
                connection.Send({"action": "get_session_id"})
            else:
                connection.Send({"action": "join_session", "session_id": self.session_id})

    def send_to_server(self):
        if self.session_id:
            connection.Send({
                "action": "update_session",
                "session_id": self.session_id,
                "data": {
                    "current_piece": self.current_piece,
                    "hold_piece": self.hold_piece,
                    "holt": self.holt,
                    "piece_count": self.piece_count,
                    "timer": self.timer,
                    "stats": self.stats,
                    "grid": self.grid
                }
            })

    def _reload_queue_and_randomizer(self):
        self.randomizer = random.Random(self.seed)
        for _ in range(self.piece_count):
            while len(self.queue) < 11:
                self._add_next_bag_to_queue()
            self.queue.pop()

    def _add_next_bag_to_queue(self):
        next_pieces = list(range(7))
        self.randomizer.shuffle(next_pieces)
        self.queue = next_pieces + self.queue

    def set_next_in_queue(self, start: bool = False):
        if start and self.current_piece is not None:
            # already a starting piece, no need to take next piece
            return
        while len(self.queue) < 11:
            self._add_next_bag_to_queue()
        self.current_piece = self.queue.pop()
        self.piece_count += 1
        self.holt = False

    def get_preview(self):
        return reversed(self.queue[-5:])

    def topped_out(self):
        if self.session_id:
            connection.Send({"action": "top_out", "session_id": self.session_id})

    def Network(self, data):
        print(f"data received : {data}")

    def Network_session_join(self, data_recv):
        if "status" not in data_recv or data_recv["status"] != "OK":
            print("an error occurred while trying to connect to session")
            self.error_msg = data_recv["status"] if "status" in data_recv else "Unknown error"
            return

        connection.Send({"action": "get_session", "session_id": self.session_id})

    def Network_session_id(self, data):
        if "session_id" not in data:
            self.error_msg = data["status"] if "status" in data else "Unknown error"
        else:
            self.session_id = data["session_id"]
            connection.Send({"action": "get_session", "session_id": self.session_id})

    def Network_session_data(self, data_recv):
        if "status" not in data_recv or data_recv["status"] != "OK":
            print("an error occurred while trying to connect to session")
            self.error_msg = data_recv["status"] if "status" in data_recv else "Unknown error"
            return
        data = data_recv["data"]
        self.seed = data["seed"]
        self.current_piece = data["current_piece"]
        self.hold_piece = data["hold_piece"]
        self.holt = data["holt"]
        self.piece_count = data["piece_count"]
        self.timer = data["timer"]
        self.stats = data["stats"]
        self.grid = data["grid"]
        self._reload_queue_and_randomizer()
        self.session_ready = True
