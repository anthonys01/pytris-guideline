"""
Tetromino
"""
import random
from typing import List

import pygame
from pygame.locals import *

from pytris.cell import Cell
from pytris.grid import Grid

HD_KEY = K_z
SD_KEY = K_s
LEFT_KEY = K_q
RIGHT_KEY = K_d
ROT_CW_KEY = K_k
ROT_CCW_KEY = K_l
ROT_180_KEY = K_KP6
HOLD_KEY = K_SPACE


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
        I_PIECE: [(1, 3), (1, 4), (1, 5), (1, 6)],
        J_PIECE: [(0, 3), (1, 3), (1, 4), (1, 5)],
        L_PIECE: [(1, 3), (1, 4), (1, 5), (0, 5)],
        O_PIECE: [(0, 4), (1, 4), (0, 5), (1, 5)],
        S_PIECE: [(1, 3), (1, 4), (0, 4), (0, 5)],
        Z_PIECE: [(0, 3), (0, 4), (1, 4), (1, 5)],
        T_PIECE: [(1, 3), (1, 4), (0, 4), (1, 5)]
    }

    PIECES_ROT = {
        I_PIECE: [
            [(0, 0), (0, 1), (0, 2), (0, 3)],
            [(-1, 2), (0, 2), (1, 2), (2, 2)],
            [(1, 3), (1, 2), (1, 1), (1, 0)],
            [(2, 1), (1, 1), (0, 1), (-1, 1)],
        ],
        J_PIECE: [
            [(0, 0), (1, 0), (1, 1), (1, 2)],
            [(0, 2), (0, 1), (1, 1), (2, 1)],
            [(2, 2), (1, 2), (1, 1), (1, 0)],
            [(2, 0), (2, 1), (1, 1), (0, 1)],
        ],
        L_PIECE: [
            [(1, 0), (1, 1), (1, 2), (0, 2)],
            [(0, 1), (1, 1), (2, 1), (2, 2)],
            [(1, 2), (1, 1), (1, 0), (2, 0)],
            [(2, 1), (1, 1), (0, 1), (0, 0)],
        ],
        S_PIECE: [
            [(1, 0), (1, 1), (0, 1), (0, 2)],
            [(0, 1), (1, 1), (1, 2), (2, 2)],
            [(1, 2), (1, 1), (2, 1), (2, 0)],
            [(2, 1), (1, 1), (1, 0), (0, 0)],
        ],
        Z_PIECE: [
            [(0, 0), (0, 1), (1, 1), (1, 2)],
            [(0, 2), (1, 2), (1, 1), (2, 1)],
            [(2, 2), (2, 1), (1, 1), (1, 0)],
            [(2, 0), (1, 0), (1, 1), (0, 1)],
        ],
        T_PIECE: [
            [(1, 0), (1, 1), (0, 1), (1, 2)],
            [(0, 1), (1, 1), (1, 2), (2, 1)],
            [(1, 2), (1, 1), (2, 1), (1, 0)],
            [(2, 1), (1, 1), (1, 0), (0, 1)],
        ],
    }

    MOVE_ROT = "rotation"
    MOVE_TRANS = "translation"

    ALLOWED_WIGGLES = 5
    DAS_TRIGGER = 7

    def __init__(self, grid: Grid, seed: str = None):
        super().__init__()
        self.randomizer = random.Random()
        if seed:
            self.randomizer = random.Random(seed)
        self.piece_type = None
        self.piece_nb = 0
        self.grid = grid
        self.cells: List[(int, int)] = []
        self.locked = False
        self.wiggles_left = self.ALLOWED_WIGGLES
        self.current_height = 1
        self.max_height = 1
        self.rotation = 0
        self.queue = []
        self.hold_piece = None
        self.key_pressed = []
        self.das_load = 0
        self.last_move = None
        self.gravity_lock = False
        self.holt = False
        self.last_dir = 0

    def _add_next_bag_to_queue(self):
        next_pieces = list(range(7))
        self.randomizer.shuffle(next_pieces)
        self.queue = next_pieces + self.queue

    def _get_preview(self):
        return reversed(self.queue[-5:])

    def set_next_from_queue(self):
        """
        set piece type to next in queue. If queue is small enough, add a new bag to the queue
        """
        if len(self.queue) < 8:
            self._add_next_bag_to_queue()
        self.piece_type = self.queue.pop()
        self.piece_nb += 1
        self.holt = False

    def spawn_piece(self) -> bool:
        """
        Try to spawn the tetromino piece in the spawn area. Succeed iif all needed cells are empty
        :return: True if succeeded, False otherwise
        """
        for pos in self.SPAWN_POS[self.piece_type]:
            if self.grid.get_cell(pos).cell_type != Cell.EMPTY:
                return False
        for pos in self.SPAWN_POS[self.piece_type]:
            self.grid.get_cell(pos).cell_type = self.CELL[self.piece_type]
        self.cells = self.SPAWN_POS[self.piece_type]
        self.locked = False
        self.current_height = 1
        self.max_height = 1
        self.rotation = 0
        self.last_move = None
        self.gravity_lock = False
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

    def _rotate(self, rotation: int):
        if self.piece_type == self.O_PIECE:
            return

        old_base = self.PIECES_ROT[self.piece_type][self.rotation]
        new_rotation = (self.rotation + rotation) % 4
        new_base = self.PIECES_ROT[self.piece_type][new_rotation]
        new_cells = []
        for i in range(4):
            new_cells.append((self.cells[i][0] - old_base[i][0] + new_base[i][0],
                              self.cells[i][1] - old_base[i][1] + new_base[i][1]))
        for cell_pos in set(new_cells).difference(self.cells):
            cell = self.grid.get_cell(cell_pos)
            if cell is None or cell.cell_type != Cell.EMPTY:
                # TODO SRS kicks
                return
        for cell in self.cells:
            self.grid.get_cell(cell).cell_type = Cell.EMPTY
        for cell in new_cells:
            self.grid.get_cell(cell).cell_type = self.CELL[self.piece_type]
        self.cells = new_cells
        self.rotation = new_rotation
        self.last_move = self.MOVE_ROT

    def is_tspin(self) -> bool:
        """
        test if we have a tspin
        """
        if self.piece_type != self.T_PIECE or self.last_move != self.MOVE_ROT:
            return False
        center = self.cells[1]
        corners = [
            (center[0] - 1, center[1] - 1),
            (center[0] - 1, center[1] + 1),
            (center[0] + 1, center[1] - 1),
            (center[0] + 1, center[1] + 1)
        ]

        def _is_used(cell_pos):
            cell = self.grid.get_cell(cell_pos)
            return cell is None or cell.cell_type != Cell.EMPTY

        used = sum(_is_used(corner) for corner in corners)
        if used < 3:
            return False

        if self.rotation == 0 and _is_used(corners[0]) and _is_used(corners[1]):
            return True
        if self.rotation == 1 and _is_used(corners[1]) and _is_used(corners[3]):
            return True
        if self.rotation == 2 and _is_used(corners[2]) and _is_used(corners[3]):
            return True
        if self.rotation == 3 and _is_used(corners[0]) and _is_used(corners[2]):
            return True

        return False

    def _translate(self, pressed_keys):
        top = 0
        left = 0
        if pressed_keys[SD_KEY]:
            top += 1
        if pressed_keys[LEFT_KEY]:
            left -= 1
        if pressed_keys[RIGHT_KEY]:
            left += 1

        if left != 0:
            if left * self.last_dir < 0:
                self.das_load = 1
            elif self.das_load == 0:
                self.das_load += 1
            elif self.das_load < self.DAS_TRIGGER:
                self.das_load += 1
                left = 0
        else:
            self.das_load = 0
        self.last_dir = left
        # TODO take into account ARR and SD speed
        new_cells = self.grid.move(left, top, self.cells)
        if new_cells != self.cells:
            self.cells = new_cells
            self.last_move = self.MOVE_TRANS

    def update(self):
        """
            Update piece position following user input
        """
        if self.locked:
            return
        pressed_keys = pygame.key.get_pressed()

        for key in list(self.key_pressed):
            if not pressed_keys[key]:
                self.key_pressed.remove(key)

        if pressed_keys[HOLD_KEY] and HOLD_KEY not in self.key_pressed and not self.holt:
            self.key_pressed.append(HOLD_KEY)
            if self.hold_piece is None:
                self.hold_piece = self.piece_type
                self.set_next_from_queue()
            else:
                self.hold_piece, self.piece_type = self.piece_type, self.hold_piece
            for cell_pos in self.cells:
                self.grid.get_cell(cell_pos).cell_type = Cell.EMPTY
            self.holt = True
            self.spawn_piece()
            return

        if pressed_keys[HD_KEY] and HD_KEY not in self.key_pressed:
            self.cells = self.grid.move(0, self.grid.height, self.cells)
            self.locked = True
            self.key_pressed.append(HD_KEY)
            return

        if pressed_keys[ROT_CW_KEY] and pressed_keys[ROT_CCW_KEY] and \
            ROT_CW_KEY not in self.key_pressed and ROT_CCW_KEY not in self.key_pressed:
            # nothing happens
            self.key_pressed.append(ROT_CW_KEY)
            self.key_pressed.append(ROT_CCW_KEY)

        if pressed_keys[ROT_CW_KEY] and ROT_CW_KEY not in self.key_pressed:
            self.key_pressed.append(ROT_CW_KEY)
            self._rotate(1)

        if pressed_keys[ROT_CCW_KEY] and ROT_CCW_KEY not in self.key_pressed:
            self.key_pressed.append(ROT_CCW_KEY)
            self._rotate(-1)

        self._translate(pressed_keys)

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
        self.cells = self.grid.move(0, 1, self.cells)
        new_height = self._get_max_height(*self.cells)
        if new_height == self.current_height:
            if self.gravity_lock:
                self.locked = True
            else:
                self.gravity_lock = True
        else:
            if new_height > self.max_height:
                self.max_height = new_height
                self.wiggles_left = self.ALLOWED_WIGGLES
            self.current_height = new_height
            self.last_move = self.MOVE_TRANS

    def _draw_mini_piece(self, surface, cell_type: int, piece: int, pos_left: int, pos_top: int):
        to_draw = Cell(cell_type)
        bonus_shift = 0
        if piece in {self.I_PIECE, self.O_PIECE}:
            bonus_shift = 5
        for cell_pos in self.SPAWN_POS[piece]:
            rect = pygame.Rect(pos_left + cell_pos[1] * 10 - bonus_shift,
                               pos_top + cell_pos[0] * 10,
                               11, 11)
            to_draw.draw(surface, rect)
            pygame.draw.rect(surface, (60, 60, 60), rect, 1)

    def draw(self, surface):
        """
            Draw the grid and its cells
        """
        # HOLD
        rect = pygame.Rect(10, self.grid.margin_top, 50, 60)
        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, (60, 60, 60), rect, 2)
        if self.hold_piece is not None:
            self._draw_mini_piece(surface,
                                  Cell.GARBAGE if self.holt else self.CELL[self.hold_piece],
                                  self.hold_piece,
                                  - 10,
                                  self.grid.margin_top + 20)

        # PREVIEW
        preview_left = self.grid.margin_left + self.grid.width * self.grid.block_size + 12
        preview_top = self.grid.margin_top
        rect = pygame.Rect(preview_left, preview_top, 50, 200)
        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, (60, 60, 60), rect, 2)
        number = 0
        for piece in self._get_preview():
            number += 1
            self._draw_mini_piece(surface,
                                  self.CELL[piece],
                                  piece,
                                  preview_left - 20,
                                  self.grid.margin_top - 15 + number * 35)

        # phantom
        phantom = self.grid.get_hd_pos(self.cells)
        if not set(phantom).intersection(self.cells):
            phantom_cell = Cell(Cell.PHANTOM)
            for cell_pos in phantom:
                rect = pygame.Rect(self.grid.margin_left + cell_pos[1] * self.grid.block_size,
                                   self.grid.margin_top + cell_pos[0] * self.grid.block_size,
                                   self.grid.block_size + 1, self.grid.block_size + 1)
                phantom_cell.draw(surface, rect)
                pygame.draw.rect(surface, (60, 60, 60), rect, 1)
