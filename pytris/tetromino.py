"""
Tetromino
"""
from typing import List

import pygame
from pygame.locals import *

from pytris.cell import Cell
from pytris.grid import Grid

HD_KEY = K_z
SD_KEY = K_s
LEFT_KEY = K_q
RIGHT_KEY = K_d
ROT_CW_KEY = K_KP4
ROT_CCW_KEY = K_KP5
ROT_180_KEY = K_KP6
HOLD_KEY = K_KP0


class Tetromino(pygame.sprite.Sprite):
    """
        Player controlled tetromino
    """
    I_PIECE = 0
    S_PIECE = 1
    Z_PIECE = 2
    L_PIECE = 3
    J_PIECE = 4
    O_PIECE = 5
    T_PIECE = 6

    CELL = [1, 2, 3, 4, 5, 6, 7]
    SPAWN_POS = {
        I_PIECE: [(1, 3), (1, 4), (1, 5), (1, 6)]
    }

    ALLOWED_WIGGLES = 5

    def __init__(self, grid: Grid, piece_type: int):
        super().__init__()
        self.piece_type = piece_type
        self.piece_nb = 0
        self.grid = grid
        self.cells: List[(int, int)] = []
        self.falling = True
        self.locked = False
        self.wiggles_left = self.ALLOWED_WIGGLES
        self.current_height = 1
        self.max_height = 1

    def spawn_piece(self) -> bool:
        """
        Try to spawn the tetromino piece in the spawn area. Succeed iif all needed cells are empty
        :return: True if succeeded, False otherwise
        """
        for pos in self.SPAWN_POS[self.piece_type]:
            self.grid.get_cell(pos).cell_type = self.CELL[self.piece_type]
        self.cells = self.SPAWN_POS[self.piece_type]
        self.piece_nb += 1
        self.falling = True
        self.locked = False
        self.current_height = 1
        self.max_height = 1
        return True

    def _is_on_top_of_something(self) -> bool:
        for cell_pos in self.cells:
            if cell_pos[0] == self.grid.height - 1 or \
                    self.grid.get_cell((cell_pos[0] + 1, cell_pos[1])).cell_type != Cell.EMPTY:
                return True
        return False

    @staticmethod
    def _get_max_height(*cells) -> int:
        return max(cell_pos[0] for cell_pos in cells)

    def update(self):
        """
            Update piece position following user input
        """
        if self.locked:
            return
        pressed_keys = pygame.key.get_pressed()
        top = 0
        left = 0
        if pressed_keys[SD_KEY]:
            top += 1
        if pressed_keys[LEFT_KEY]:
            left -= 1
        if pressed_keys[RIGHT_KEY]:
            left += 1
        # TODO take into account DAS, ARR and SD speed
        self.cells = self.grid.move(left, top, *self.cells)

        new_height = self._get_max_height(*self.cells)
        if new_height > self.max_height:
            self.max_height = new_height
            self.wiggles_left = self.ALLOWED_WIGGLES
        elif new_height < self.current_height:
            self.wiggles_left -= 1
        elif self._is_on_top_of_something() and self.wiggles_left == 0:
            self.locked = True

        self.current_height = new_height

    def go_down(self):
        """
            GODOWN with gravity
        """
        self.cells = self.grid.move(0, 1, *self.cells)
        new_height = self._get_max_height(*self.cells)
        if new_height == self.current_height:
            self.locked = True
        else:
            if new_height > self.max_height:
                self.max_height = new_height
                self.wiggles_left = self.ALLOWED_WIGGLES
            self.current_height = new_height
