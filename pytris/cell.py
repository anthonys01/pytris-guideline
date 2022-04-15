"""
Cell
"""
import pygame


class Cell(pygame.sprite.Sprite):
    """
        Singular grid cell
    """
    EMPTY = 0
    I_MINO = 1
    S_MINO = 2
    Z_MINO = 3
    L_MINO = 4
    J_MINO = 5
    O_MINO = 6
    T_MINO = 7
    GARBAGE = 8
    PHANTOM = 9

    COLOR = [(20, 20, 20),
             (15, 155, 215),
             (89, 177, 1),
             (215, 15, 55),
             (227, 91, 2),
             (33, 65, 198),
             (227, 159, 2),
             (175, 41, 138),
             (120, 120, 120),
             (200, 200, 200)]

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
