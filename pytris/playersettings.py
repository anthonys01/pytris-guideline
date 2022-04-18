"""
    Manage player settings persistence
"""
import json
import os.path
from typing import Union


class PlayerSettings:
    """
        player settings management
    """

    SETTINGS_FILE_PATH = "data/player_settings.json"

    def __init__(self):
        self._das = 10
        self._arr = 2
        self._sdf = 3
        self._volume = 0.6
        if os.path.exists(self.SETTINGS_FILE_PATH):
            with open(self.SETTINGS_FILE_PATH, "r") as f:
                data = json.load(f)
                if "DAS" in data:
                    self._das = data["DAS"]
                if "ARR" in data:
                    self._arr = data["ARR"]
                if "SDF" in data:
                    self._sdf = data["SDF"]
                if "volume" in data:
                    self._volume = data["volume"]

    def _save_settings(self):
        with open(self.SETTINGS_FILE_PATH, "w") as f:
            json.dump({
                "DAS": self._das,
                "ARR": self._arr,
                "SDF": self._sdf,
                "volume": self._volume
            }, f)

    @property
    def das(self):
        return self._das

    @das.setter
    def das(self, new_das: int):
        self._das = new_das
        self._save_settings()

    @property
    def arr(self) -> Union[float, int]:
        return self._arr

    @arr.setter
    def arr(self, new_arr: Union[float, int]):
        if new_arr == 0.0:
            self._arr = 0
        elif new_arr > 1:
            self._arr = int(new_arr)
        else:
            self._arr = new_arr
        self._save_settings()

    @property
    def sdf(self) -> Union[float, int]:
        return self._sdf

    @sdf.setter
    def sdf(self, new_sdf: Union[float, int]):
        if new_sdf == 0.0:
            self._sdf = 0
        elif new_sdf > 1:
            self._sdf = int(new_sdf)
        else:
            self._sdf = new_sdf
        self._save_settings()

    @property
    def volume(self) -> float:
        return self._volume

    @volume.setter
    def volume(self, new_volume: float):
        if 0 <= new_volume <= 1:
            self._volume = new_volume
            self._save_settings()
