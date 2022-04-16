"""
Grid
"""
from typing import Optional, List, Tuple

import pygame

from pytris.cell import Cell


class Grid(pygame.sprite.Sprite):
    """
        Grid containing the cells and minos
    """
    HEIGHT = 22
    WIDTH = 10

    def __init__(self, margin_left: int, margin_top: int):
        super().__init__()
        self.margin_top = margin_top
        self.margin_left = margin_left
        self.block_size = 25

        empty_line = [None] * self.WIDTH
        self.grid: List[List[Cell]] = [empty_line[:] for _ in range(self.HEIGHT)]
        for line in self.grid:
            for i in range(self.WIDTH):
                line[i] = Cell()

    def reset(self):
        """
            Reset all cells to empty
        """
        for line in self.grid:
            for cell in line:
                cell.cell_type = Cell.EMPTY

    def get_cell(self, pos: (int, int)) -> Optional[Cell]:
        """
        Return cell if exists
        :param pos: cell position
        :return: Ce
        """
        line, col = pos
        if 0 <= line < self.HEIGHT and 0 <= col < self.WIDTH:
            return self.grid[line][col]
        return None

    def get_hd_pos(self, cells_pos: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
            Get hard drop position for given cells. Order is kept
        """
        okay = True
        top = 0

        cells_pos_to_return = cells_pos
        while okay:
            top += 1
            new_cells_pos_to_return = []
            for cell_pos in cells_pos:
                new_cells_pos_to_return.append((cell_pos[0] + top, cell_pos[1]))
            new_cells_pos = set(new_cells_pos_to_return).difference(cells_pos)

            conflict = False
            for new_cell_pos in new_cells_pos:
                cell = self.get_cell(new_cell_pos)
                if cell is None or cell.cell_type != Cell.EMPTY:
                    conflict = True
                    break
            if conflict:
                okay = False
            else:
                cells_pos_to_return = new_cells_pos_to_return
        return cells_pos_to_return

    def move(self, left: int, top: int, cells_pos: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """
            Move the cells at given position if there is no border or other cells in the way.
            :return: the new cells positions. Cell order is kept
        """
        if left == 0 and top == 0:
            return cells_pos

        if top != 0:
            iteration = top // abs(top)
            okay = False
            while top != 0 and not okay:
                new_cells_pos = set()
                for cell_pos in cells_pos:
                    new_cells_pos.add((cell_pos[0] + top, cell_pos[1]))
                new_cells_pos.difference_update(cells_pos)
                conflict = False
                for new_cell_pos in new_cells_pos:
                    cell = self.get_cell(new_cell_pos)
                    if cell is None or cell.cell_type != Cell.EMPTY:
                        conflict = True
                        break
                if conflict:
                    top -= iteration
                else:
                    okay = True

        new_cells_pos_to_return = []
        for cell_pos in cells_pos:
            new_cells_pos_to_return.append((cell_pos[0] + top, cell_pos[1] + left))
        to_clean_pos = set(cells_pos).difference(new_cells_pos_to_return)
        new_cells_pos = set(new_cells_pos_to_return).difference(cells_pos)

        if left != 0:
            iteration = left // abs(left)
            okay = False
            while left != 0 and not okay:
                conflict = False
                for new_cell_pos in new_cells_pos:
                    cell = self.get_cell(new_cell_pos)
                    if cell is None or cell.cell_type != Cell.EMPTY:
                        conflict = True
                        break
                if conflict:
                    left -= iteration
                    new_cells_pos_to_return = []
                    for cell_pos in cells_pos:
                        new_cells_pos_to_return.append((cell_pos[0] + top, cell_pos[1] + left))
                    to_clean_pos = set(cells_pos).difference(new_cells_pos_to_return)
                    new_cells_pos = set(new_cells_pos_to_return).difference(cells_pos)
                else:
                    okay = True

        if left == 0 and top == 0:
            return cells_pos

        new_type = self.get_cell(cells_pos[0]).cell_type

        for pos in to_clean_pos:
            self.get_cell(pos).cell_type = Cell.EMPTY

        for pos in new_cells_pos:
            self.get_cell(pos).cell_type = new_type

        return new_cells_pos_to_return

    def clear_lines(self) -> int:
        """
            Clear full lines and return the number of cleared lines
        """
        to_clear = []
        cleared = []
        for line in reversed(range(self.HEIGHT)):
            clear = True
            for cell in self.grid[line]:
                if cell.cell_type == cell.EMPTY:
                    clear = False
                    break
            if clear:
                to_clear.append(line)
        for clear_line in to_clear:
            cleared.append(self.grid.pop(clear_line))
        for line in cleared:
            for cell in line:
                cell.cell_type = Cell.EMPTY
        self.grid = cleared + self.grid
        return len(cleared)

    def is_board_empty(self) -> bool:
        for line in self.grid:
            for cell in line:
                if cell.cell_type != Cell.EMPTY:
                    return False
        return True

    def draw(self, surface):
        """
            Draw the grid and its cells
        """
        for col in range(0, self.WIDTH):
            for line in range(0, self.HEIGHT):
                rect = pygame.Rect(self.margin_left + col * self.block_size,
                                   self.margin_top + line * self.block_size,
                                   self.block_size + 1, self.block_size + 1)
                self.grid[line][col].draw(surface, rect)
