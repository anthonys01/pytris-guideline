"""
Grid
"""
from typing import Optional, List

import pygame

from pytris.cell import Cell


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
