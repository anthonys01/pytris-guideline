"""
    Node grid
"""
from typing import List

from pytris.typehints import BoolGrid, Cell, PiecePos


def get_group(grid_state, line_nb, col_nb, pos, tested, current_group):
    if pos in tested or pos in current_group:
        return

    tested.add(pos)
    line, col = pos
    if grid_state[line][col]:
        return

    current_group.add(pos)

    if col != col_nb - 1:
        get_group(grid_state, line_nb, col_nb, (line, col + 1), tested, current_group)
    if col != 0:
        get_group(grid_state, line_nb, col_nb, (line, col - 1), tested, current_group)
    for next_line in range(line_nb):
        if next_line == line or (next_line, col) in tested or grid_state[next_line][col]:
            continue
        get_group(grid_state, line_nb, col_nb, (next_line, col), tested, current_group)


def has_orphan_cells(grid_state: BoolGrid) -> bool:
    """
        true if there is a group of cells that is not a multiple of 4
    """
    if not grid_state:
        return False

    line_nb, col_nb = len(grid_state), len((grid_state[0]))
    tested = set()

    for line in range(line_nb):
        for col in range(col_nb):
            pos = (line, col)
            if pos in tested:
                continue
            if grid_state[line][col]:
                continue
            group = set()
            get_group(grid_state, line_nb, col_nb, pos, tested, group)
            if len(group) % 4 != 0:
                return True
    return False


def has_orphan_cells_after(grid_state: BoolGrid, piece_pos: PiecePos, min_pos, max_pos) -> bool:
    """
        true if there is a group of cells that is not a multiple of 4 after placing piece
    """
    if not grid_state:
        return False

    line_nb, col_nb = len(grid_state), len((grid_state[0]))
    tested = set(piece_pos)

    for line in range(max(min_pos[0] - 1, 0), min(max_pos[0] + 2, line_nb)):
        for col in range(max(min_pos[1] - 1, 0), min(max_pos[1] + 2, col_nb)):
            pos = (line, col)
            if pos in tested:
                continue
            if grid_state[line][col]:
                continue
            group = set()
            get_group(grid_state, line_nb, col_nb, pos, tested, group)
            if len(group) % 4 != 0:
                return True
    return False


if __name__ == "__main__":
    grid = [
        [True, True, True, True, False, False, False, False, False, True],
        [True, True, True, False, False, False, False, False, False, True],
        [True, True, True, False, False, False, False, False, False, True],
        [True, True, False, False, False, False, False, False, False, True]
    ]
    print("should be False:", has_orphan_cells(grid))
    print("should be False:", has_orphan_cells_after(grid, [(1, 4), (2, 4), (2, 5), (3, 4)]))
    print("should be True:", has_orphan_cells_after(grid, [(1, 3), (2, 3), (2, 4), (3, 3)]))

    grid = [
        [True, True, True, True, False, False, False, False, False, True],
        [True, True, True, False, False, False, False, False, False, True],
        [False, True, True, False, False, False, False, False, False, True],
        [False, False, True, True, False, False, False, False, False, True]
    ]
    print("should be True:", has_orphan_cells(grid))

    grid = [
        [True, True, True, True, False, False, False, False, False, True],
        [True, True, True, True, False, False, False, False, False, True],
        [False, True, True, True, False, False, False, False, False, True],
        [False, False, False, True, False, False, False, False, False, True]
    ]
    print("should be False:", has_orphan_cells(grid))

    grid = [
        [True, True, True, True, False, False],
        [True, True, True, False, False, True]
    ]
    print("should be False:", has_orphan_cells(grid))
