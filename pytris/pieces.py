"""
Useful constants and tables for pieces and rotation
"""
from typing import List, Tuple, Optional

I_PIECE = 0
S_PIECE = 1
Z_PIECE = 2
L_PIECE = 3
J_PIECE = 4
O_PIECE = 5
T_PIECE = 6

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
    O_PIECE: [
        [(0, 0), (0, 1), (1, 0), (1, 1)]
    ]
}

PIECES_ROT_MIN_MAX = {
    I_PIECE: [
        [(0, 0), (0, 3)],
        [(-1, 2), (2, 2)],
        [(1, 0), (1, 3)],
        [(-1, 1), (2, 1)],
    ],
    J_PIECE: [
        [(0, 0), (1, 2)],
        [(0, 1), (2, 2)],
        [(1, 0), (2, 2)],
        [(0, 0), (2, 1)],
    ],
    L_PIECE: [
        [(0, 0), (1, 2)],
        [(0, 1), (2, 2)],
        [(1, 0), (2, 2)],
        [(0, 0), (2, 1)],
    ],
    S_PIECE: [
        [(0, 0), (1, 2)],
        [(0, 1), (2, 2)],
        [(1, 0), (2, 2)],
        [(0, 0), (2, 1)],
    ],
    Z_PIECE: [
        [(0, 0), (1, 2)],
        [(0, 1), (2, 2)],
        [(1, 0), (2, 2)],
        [(0, 0), (2, 1)],
    ],
    T_PIECE: [
        [(0, 0), (1, 2)],
        [(0, 1), (2, 2)],
        [(1, 0), (2, 2)],
        [(0, 0), (2, 1)],
    ],
    O_PIECE: [
        [(0, 0), (1, 1)]
    ]
}

# coordinates here are (Y, -X)
WALL_KICKS = [
    {
        1: [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        3: [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        2: [(0, 0), (0, 1)]
    },
    {
        0: [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        2: [(0, 0), (1, 0), (1, -1), (0, 2), (1, 2)],
        3: [(0, 0), (1, 0)]
    },
    {
        1: [(0, 0), (-1, 0), (-1, 1), (0, -2), (-1, -2)],
        3: [(0, 0), (1, 0), (1, 1), (0, -2), (1, -2)],
        0: [(0, 0), (0, -1)]
    },
    {
        2: [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
        0: [(0, 0), (-1, 0), (-1, -1), (0, 2), (-1, 2)],
        1: [(0, 0), (-1, 0)]
    }
]

I_WALL_KICKS = [
    {
        1: [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        3: [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
        2: [(1, -1), (1, 0)]
    },
    {
        0: [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        2: [(0, 0), (-1, 0), (2, 0), (-1, 2), (2, -1)],
        3: [(-1, -1), (0, -1)]
    },
    {
        1: [(0, 0), (1, 0), (-2, 2), (1, -2), (-2, 1)],
        3: [(0, 0), (2, 0), (-1, 0), (2, 1), (-1, -2)],
        0: [(-1, 1), (-1, 0)]
    },
    {
        2: [(0, 0), (-2, 0), (1, 0), (-2, -1), (1, 2)],
        0: [(0, 0), (1, 0), (-2, 0), (1, -2), (-2, 1)],
        1: [(1, 1), (0, 1)]
    }
]


def rotate(piece: int, cells: List[Tuple[int, int]],
           grid: List[List[bool]], rotation: int, rotate_val: int) -> List[Tuple[int, int]]:
    """
        return rotated
    """
    if piece == O_PIECE:
        return cells

    old_base = PIECES_ROT[piece][rotation]
    new_rotation = (rotation + rotate_val) % 4
    new_base = PIECES_ROT[piece][new_rotation]
    new_cells = []
    for i in range(4):
        new_cells.append((cells[i][0] - old_base[i][0] + new_base[i][0],
                          cells[i][1] - old_base[i][1] + new_base[i][1]))
    kick_table = I_WALL_KICKS if piece == I_PIECE else WALL_KICKS
    allowed_kicks = kick_table[rotation][new_rotation]
    for mode in range(len(allowed_kicks)):
        correct = True
        transposed_cells = [(cell_pos[0] - allowed_kicks[mode][1],
                             cell_pos[1] + allowed_kicks[mode][0]) for cell_pos in new_cells]
        for cell_pos in set(transposed_cells).difference(cells):
            if cell_pos[0] >= len(grid) or \
                cell_pos[1] < 0 or cell_pos[1] >= len(grid[0]) or \
                    cell_pos[0] >= 0 and grid[cell_pos[0]][cell_pos[1]]:
                correct = False
                break
        if correct:
            new_cells = transposed_cells
            break
    return new_cells


def reverse_rotate(piece: int, cells: List[Tuple[int, int]],
                   grid: List[List[bool]], end_rotation: int,
                   rotate_val: int) -> Optional[List[Tuple[int, int]]]:
    """
         find the original position in which you can rotate
         in given rotate_val to reach end rotation and position
    """
    if piece == O_PIECE:
        return cells

    end_base = PIECES_ROT[piece][end_rotation]
    initial_rotation = (end_rotation - rotate_val) % 4
    initial_base = PIECES_ROT[piece][initial_rotation]
    new_cells = []
    for i in range(4):
        new_cells.append((cells[i][0] - end_base[i][0] + initial_base[i][0],
                          cells[i][1] - end_base[i][1] + initial_base[i][1]))
    kick_table = I_WALL_KICKS if piece == I_PIECE else WALL_KICKS
    allowed_kicks = kick_table[initial_rotation][end_rotation]
    for mode in range(len(allowed_kicks)):
        correct = True
        transposed_cells = [(cell_pos[0] + allowed_kicks[mode][1],
                             cell_pos[1] - allowed_kicks[mode][0]) for cell_pos in new_cells]
        for cell_pos in set(transposed_cells).difference(cells):
            if cell_pos[0] >= len(grid) or \
                    cell_pos[1] < 0 or cell_pos[1] >= len(grid[0]) or \
                    cell_pos[0] >= 0 and grid[cell_pos[0]][cell_pos[1]]:
                correct = False
                break
        if correct:
            if rotate(piece, transposed_cells, grid, initial_rotation, rotate_val) == cells:
                return transposed_cells
    return None
