"""
Main file
"""
import sys
from typing import List, Optional

import pygame
from pygame.locals import *


class Cell(pygame.sprite.Sprite):
    """
        Singular grid cell
    """
    EMPTY = 0
    GARBAGE = 8
    I_MINO = 1

    COLOR = [(20, 20, 20), (0, 0, 200), (), (), (), (), (), (), (150, 150, 150)]

    def __init__(self, cell_type=0):
        super().__init__()
        self._cell_type = cell_type

    @property
    def cell_type(self):
        """
        Cell type
        """
        return self._cell_type

    @cell_type.setter
    def cell_type(self, new_cell_type: int):
        """
        Setter
        """
        self._cell_type = new_cell_type

    def draw(self, surface, rect_pos: pygame.Rect):
        """
            Draw the cell
        """
        pygame.draw.rect(surface, self.COLOR[self.cell_type], rect_pos)


class Grid(pygame.sprite.Sprite):
    """
        Grid containing the cells and minos
    """
    def __init__(self):
        super().__init__()
        self.margin_top = 20
        self.margin_left = 20
        self.block_size = 20
        self.height = 22
        self.width = 10
        empty_line = [None] * self.width
        self.grid: List[List[Cell]] = [empty_line[:] for _ in range(self.height)]
        for line in self.grid:
            for i in range(self.width):
                line[i] = Cell()

    def get_cell(self, pos: (int, int)) -> Optional[Cell]:
        """
        Return cell if exists
        :param pos: cell position
        :return: Ce
        """
        line, col = pos
        if 0 <= line < self.height and 0 <= col < self.width:
            return self.grid[line][col]
        return None

    def move(self, left: int, top: int, *cells_pos):
        """
            Move the cells at given position if there is no border or other cells in the way
        """
        if left == 0 and top == 0:
            return cells_pos

        new_cells_pos = set()
        for cell_pos in cells_pos:
            new_cells_pos.add((cell_pos[0] + top, cell_pos[1]))
        new_cells_pos.difference_update(cells_pos)

        for new_cell_pos in new_cells_pos:
            cell = self.get_cell(new_cell_pos)
            if cell is None or cell.cell_type != Cell.EMPTY:
                # TODO move until obstacle instead of cancelling
                return cells_pos

        new_cells_pos = set()
        for cell_pos in cells_pos:
            new_cells_pos.add((cell_pos[0] + top, cell_pos[1] + left))
        to_clean_pos = set(cells_pos).difference(new_cells_pos)
        new_cells_pos_to_return = set(new_cells_pos)
        new_cells_pos.difference_update(cells_pos)

        for new_cell_pos in new_cells_pos:
            cell = self.get_cell(new_cell_pos)
            if cell is None or cell.cell_type != Cell.EMPTY:
                # TODO move until obstacle instead of cancelling
                return cells_pos

        new_type = self.get_cell(cells_pos[0]).cell_type

        for pos in to_clean_pos:
            self.get_cell(pos).cell_type = Cell.EMPTY

        for pos in new_cells_pos:
            self.get_cell(pos).cell_type = new_type

        return new_cells_pos_to_return

    def draw(self, surface):
        """
            Draw the grid and its cells
        """
        for col in range(0, self.width):
            for line in range(0, self.height):
                rect = pygame.Rect(self.margin_left + col * self.block_size,
                                   self.margin_top + line * self.block_size,
                                   self.block_size, self.block_size)
                self.grid[line][col].draw(surface, rect)
                pygame.draw.rect(surface, (60, 60, 60), rect, 1)


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

    def __init__(self, grid: Grid, piece_type: int):
        super().__init__()
        self.piece_type = piece_type
        self.grid = grid
        self.cells: List[(int, int)] = []

    def spawn_piece(self) -> bool:
        """
        Try to spawn the tetromino piece in the spawn area. Succeed iif all needed cells are empty
        :return: True if succeeded, False otherwise
        """
        for pos in self.SPAWN_POS[self.piece_type]:
            self.grid.get_cell(pos).cell_type = self.CELL[self.piece_type]
        self.cells = self.SPAWN_POS[self.piece_type]
        return True

    def update(self):
        """
            Update piece position following user input
        """
        pressed_keys = pygame.key.get_pressed()
        top = 0
        left = 0
        if pressed_keys[K_UP]:
            top -= 1
        if pressed_keys[K_DOWN]:
            top += 1
        if pressed_keys[K_LEFT]:
            left -= 1
        if pressed_keys[K_RIGHT]:
            left += 1
        self.cells = self.grid.move(left, top, *self.cells)


if __name__ == "__main__":
    pygame.init()

    DISPLAYSURF = pygame.display.set_mode((500, 500))
    FPS = pygame.time.Clock()
    DISPLAYSURF.fill((0, 0, 0))
    pygame.display.set_caption("Pytris")

    g = Grid()
    t = Tetromino(g, Tetromino.I_PIECE)
    t.spawn_piece()

    while True:
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        t.update()

        DISPLAYSURF.fill((150, 150, 150))
        g.draw(DISPLAYSURF)

        FPS.tick(60)
