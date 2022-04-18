"""
Grid
"""
from typing import Optional, List, Tuple

import pygame

from pytris.cell import Cell
from pytris.session import GameSession


class Grid(pygame.sprite.Sprite):
    """
        Grid containing the cells and minos
    """
    HEIGHT = 22
    WIDTH = 10

    def __init__(self, margin_left: int, margin_top: int, session: GameSession):
        super().__init__()
        self.margin_top = margin_top
        self.margin_left = margin_left
        self.block_size = 25
        self.session = session

    def get_cell(self, pos: (int, int)) -> Optional[Cell]:
        """
        Return cell if exists
        :param pos: cell position
        :return: Cell instance (read-only)
        """
        line, col = pos
        if 0 <= line < self.HEIGHT and 0 <= col < self.WIDTH:
            return Cell(self.session.grid[line][col])
        return None

    def set_cell_type(self, cells: List[Tuple[int, int]], new_type: int):
        for cell in cells:
            self.session.grid[cell[0]][cell[1]] = new_type

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

        cells_pos_to_return = cells_pos
        correct_top = 0
        if top != 0:
            iteration = top // abs(top)
            okay = True
            while okay and abs(correct_top) < abs(top):
                correct_top += iteration
                new_cells_pos_to_return = []
                for cell_pos in cells_pos:
                    new_cells_pos_to_return.append((cell_pos[0] + correct_top, cell_pos[1]))
                new_cells_pos = set(new_cells_pos_to_return).difference(cells_pos)

                conflict = False
                for new_cell_pos in new_cells_pos:
                    cell = self.get_cell(new_cell_pos)
                    if cell is None or cell.cell_type != Cell.EMPTY:
                        conflict = True
                        break
                if conflict:
                    okay = False
                    correct_top -= 1
                else:
                    cells_pos_to_return = new_cells_pos_to_return

        correct_left = 0
        if left != 0:
            iteration = left // abs(left)
            okay = True
            while okay and abs(correct_left) < abs(left):
                correct_left += iteration
                new_cells_pos_to_return = []
                for cell_pos in cells_pos_to_return:
                    new_cells_pos_to_return.append((cell_pos[0], cell_pos[1] + correct_left))
                new_cells_pos = set(new_cells_pos_to_return).difference(cells_pos)

                conflict = False
                for new_cell_pos in new_cells_pos:
                    cell = self.get_cell(new_cell_pos)
                    if cell is None or cell.cell_type != Cell.EMPTY:
                        conflict = True
                        break
                if conflict:
                    okay = False
                    correct_left -= 1
                else:
                    cells_pos_to_return = new_cells_pos_to_return

        if correct_top == 0 and correct_left == 0:
            return cells_pos

        new_type = self.get_cell(cells_pos[0]).cell_type

        if cells_pos != cells_pos_to_return:
            self.set_cell_type(cells_pos, Cell.EMPTY)
            self.set_cell_type(cells_pos_to_return, new_type)
            self.session.send_to_server()

        return cells_pos_to_return

    def clear_lines(self) -> int:
        """
            Clear full lines and return the number of cleared lines
        """
        to_clear = []
        cleared = []
        for line in reversed(range(self.HEIGHT)):
            clear = True
            for cell in self.session.grid[line]:
                if cell == Cell.EMPTY:
                    clear = False
                    break
            if clear:
                to_clear.append(line)
        for clear_line in to_clear:
            cleared.append(self.session.grid.pop(clear_line))
        for line in cleared:
            for i in range(len(line)):
                line[i] = Cell.EMPTY
        self.session.grid = cleared + self.session.grid
        if cleared:
            self.session.send_to_server()
        return len(cleared)

    def is_board_empty(self) -> bool:
        for line in self.session.grid:
            for cell in line:
                if cell != Cell.EMPTY:
                    return False
        return True

    def draw(self, surface, topped_out: bool):
        """
            Draw the grid and its cells
        """
        gray = Cell(Cell.GARBAGE)
        for col in range(0, self.WIDTH):
            for line in range(0, self.HEIGHT):
                rect = pygame.Rect(self.margin_left + col * self.block_size,
                                   self.margin_top + line * self.block_size,
                                   self.block_size + 1, self.block_size + 1)
                if topped_out and self.session.grid[line][col] != Cell.EMPTY:
                    gray.draw(surface, rect)
                else:
                    self.get_cell((line, col)).draw(surface, rect)
