"""
    Manage key presses and key binding
"""
from enum import auto, Enum
from typing import Dict

import pygame
from pygame.locals import *


class Key(Enum):
    """
        Relevant keys for the game
    """
    HD_KEY = auto()
    SD_KEY = auto()
    LEFT_KEY = auto()
    RIGHT_KEY = auto()
    ROT_CW_KEY = auto()
    ROT_CCW_KEY = auto()
    ROT_180_KEY = auto()
    HOLD_KEY = auto()
    RESET_KEY = auto()


class KeyManager:
    """
        Manage key presses and binding
    """
    def __init__(self):
        self._pressing_keys: Dict[Key, bool] = {}
        self._just_pressed_keys: Dict[Key, bool] = {}
        self._enum_to_key_mapping: Dict[Key, int] = {}
        self._init_mapping()

    def _init_mapping(self):
        self._enum_to_key_mapping = {
            Key.HD_KEY: K_z,
            Key.SD_KEY: K_s,
            Key.LEFT_KEY: K_q,
            Key.RIGHT_KEY: K_d,
            Key.ROT_CW_KEY: K_k,
            Key.ROT_CCW_KEY: K_l,
            Key.ROT_180_KEY: K_m,
            Key.HOLD_KEY: K_SPACE,
            Key.RESET_KEY: K_BACKSPACE
        }

    @property
    def pressed(self) -> Dict[Key, bool]:
        return dict(self._just_pressed_keys)

    @property
    def pressing(self) -> Dict[Key, bool]:
        return dict(self._pressing_keys)

    def update(self):
        pressed_keys = pygame.key.get_pressed()
        for enum, key in self._enum_to_key_mapping.items():
            self._just_pressed_keys[enum] = pressed_keys[key] and not self._pressing_keys[enum]
            self._pressing_keys[enum] = pressed_keys[self._enum_to_key_mapping[enum]]
