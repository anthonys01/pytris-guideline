"""
    Manage key presses and key binding
"""
import json
import os.path
from enum import Enum
from typing import Dict

import pygame
from pygame.locals import *


class Key(str, Enum):
    """
        Relevant keys for the game
    """
    HD_KEY = "hard_drop"
    SD_KEY = "soft_drop"
    LEFT_KEY = "left"
    RIGHT_KEY = "right"
    ROT_CW_KEY = "rotate_cw"
    ROT_CCW_KEY = "rotate_ccw"
    ROT_180_KEY = "rotate_180"
    HOLD_KEY = "hold"
    RESET_KEY = "reset"
    EXIT_KEY = "exit"


class KeyManager:
    """
        Manage key presses and binding
    """
    KEYBIND_FILE_PATH = "data/key_binding.json"

    def __init__(self):
        self._pressing_keys: Dict[Key, bool] = {}
        self._just_pressed_keys: Dict[Key, bool] = {}
        self._enum_to_key_mapping: Dict[Key, int] = {}
        self._init_mapping()

    def _init_mapping(self):
        json_data = {}
        if os.path.exists(self.KEYBIND_FILE_PATH):
            with open(self.KEYBIND_FILE_PATH, "r") as f:
                json_data = json.load(f)
        if not json_data:
            self._enum_to_key_mapping = {
                Key.HD_KEY: K_z,
                Key.SD_KEY: K_s,
                Key.LEFT_KEY: K_q,
                Key.RIGHT_KEY: K_d,
                Key.ROT_CW_KEY: K_k,
                Key.ROT_CCW_KEY: K_l,
                Key.ROT_180_KEY: K_m,
                Key.HOLD_KEY: K_SPACE,
                Key.RESET_KEY: K_BACKSPACE,
                Key.EXIT_KEY: K_ESCAPE
            }
            print("No binding data was found, setting default values")
        else:
            for key, value in json_data.items():
                self._enum_to_key_mapping[Key(key)] = value

    def key_for(self, enum: Key) -> int:
        """
            return current key binding
        """
        return self._enum_to_key_mapping[enum]

    def update_binding(self, enum: Key, key: int) -> bool:
        self._enum_to_key_mapping[enum] = key
        return self.save_settings(self._enum_to_key_mapping)

    def save_settings(self, bindings: Dict[Key, int]) -> bool:
        """
            Save given bindings and apply it
        """
        if os.path.exists(self.KEYBIND_FILE_PATH):
            with open(self.KEYBIND_FILE_PATH, "w") as f:
                json.dump(bindings, f)
                self._enum_to_key_mapping = dict(bindings)
            return True
        return False

    @property
    def pressed(self) -> Dict[Key, bool]:
        """
            Keys that were just pressed this frame
        """
        return dict(self._just_pressed_keys)

    @property
    def pressing(self) -> Dict[Key, bool]:
        """
            Keys currently pressed
        """
        return dict(self._pressing_keys)

    def update(self):
        """
            Update pressed keys
        """
        pressed_keys = pygame.key.get_pressed()
        for enum, key in self._enum_to_key_mapping.items():
            self._just_pressed_keys[enum] = pressed_keys[key] and not self._pressing_keys[enum]
            self._pressing_keys[enum] = pressed_keys[self._enum_to_key_mapping[enum]]
