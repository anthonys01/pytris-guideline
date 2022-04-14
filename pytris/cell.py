"""
Cell
"""
import pygame


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

