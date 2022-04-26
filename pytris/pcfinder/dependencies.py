"""
    Piece dependencies from grid or cell groups
"""
from typing import Tuple, Set, List, Optional

from pytris.pcfinder.node_grid import get_cell_groups
from pytris.pieces import PIECES_ROT, PIECES_ROT_MIN_MAX
from pytris.typehints import Cell, BoolGrid


def remove_interlines(group: Set[Cell]) -> Tuple[Set[Cell], Tuple[int, int]]:
    sorted_group = sorted(group, key=lambda x: x[0])
    min_line, min_col = sorted_group[0]
    current_min = min_line
    new_group = {sorted_group[0]}
    for cell in sorted_group[1:]:
        min_col = min(cell[1], min_col)
        if cell[0] == current_min:
            new_group.add(cell)
        else:
            current_min += 1
            new_group.add((current_min, cell[1]))
    return new_group, (min_line, min_col)


def transpose_to_min(cell: Cell, group_min: Tuple[int, int], piece_min: Tuple[int, int]) -> Cell:
    return cell[0] + piece_min[0] - group_min[0], cell[1] + piece_min[1] - group_min[1]


def get_dependency(group: Set[Cell]) -> Optional[Tuple[int, int]]:
    """
        Find if a piece can fit in the cell group
    """
    if len(group) != 4:
        return
    fixed_group, group_min = remove_interlines(group)
    for piece in range(7):
        for rot, rot_piece in enumerate(PIECES_ROT[piece]):
            is_dependency = True
            for cell in fixed_group:
                if not transpose_to_min(cell, group_min, PIECES_ROT_MIN_MAX[piece][rot][0]) in rot_piece:
                    is_dependency = False
                    break
            if is_dependency:
                return piece, rot


def get_dependencies(grid: BoolGrid) -> List[Tuple[int, int]]:
    groups = get_cell_groups(grid)
    deps = []
    for group in groups:
        dep = get_dependency(group)
        if dep:
            deps.append(dep)
    return deps
