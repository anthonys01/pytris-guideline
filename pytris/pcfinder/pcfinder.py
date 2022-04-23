"""
    Find PC sequences for given queue and board
"""
import time
import itertools
from typing import List, Tuple, Optional, Iterable

import more_itertools

from pytris.pcfinder.node_grid import has_orphan_cells_after, has_orphan_cells
from pytris.pieces import T_PIECE, Z_PIECE, L_PIECE, J_PIECE, S_PIECE, I_PIECE, O_PIECE, PIECES_ROT, reverse_rotate, \
    PIECES_ROT_MIN_MAX
from pytris.typehints import BoolGrid, PiecePos


Queue = List[int]
PieceMov = List[PiecePos]


class PCFinder:
    """
        PC Solver
    """
    def __init__(self, *, deep_drop: bool = False, no_hold: bool = False):
        self.deep_drop = deep_drop
        self.no_hold = no_hold

    def generate_possible_queue_combinations(self, queue: Queue, res_size: int) -> List[Queue]:
        """
            Possible pieces order by user hold. Only generate queues of given size
        """
        if res_size > len(queue):
            return []

        if self.no_hold:
            return [queue[:res_size]]

        working_nodes = [[queue[:], [], []]]

        to_return = []

        while True:
            if not working_nodes:
                break
            node = working_nodes.pop()
            if len(node[2]) == res_size:
                if node[2] not in to_return:
                    to_return += [node[2]]
                continue
            res = []
            if node[0]:
                piece = node[0][0]
                # place
                res += [[node[0][1:], node[1][:], node[2] + [piece]]]
                # hold and place
                if not node[1]:
                    if len(node[0]) > 1:
                        second_piece = node[0][1]
                        res += [[node[0][2:], [piece], node[2] + [second_piece]]]
                    else:
                        res += [[node[0][2:], [piece], node[2]]]
                else:
                    res += [[node[0][1:], [piece], node[2] + node[1]]]
            else:
                res += [[[], [], node[2] + node[1]]]
            working_nodes = res + working_nodes

        return to_return

    def generate_sub_queue(self, queue: Queue, sub_size: int)\
            -> Iterable[Tuple[Queue, List[int], Queue]]:
        max_size = len(queue)
        reduced = queue[:]
        sub_filter = [0] * max_size
        for i in range(sub_size):
            sub_filter[i] = 1
        for perm in more_itertools.distinct_permutations(sub_filter):
            sub_res = list(itertools.compress(reduced, perm))
            left_queue = [reduced[i] for i in range(max_size) if perm[i] == 0]
            yield sub_res, perm, left_queue

    @staticmethod
    def get_column_parity(grid_state: BoolGrid, line_nb: int, col_nb: int) -> int:
        if not grid_state:
            return 0

        col_sums = [0, line_nb * (col_nb % 2)]
        for line in grid_state:
            for col in range(col_nb):
                col_sums[col % 2] += int(line[col])
        return ((col_sums[0] - col_sums[1]) // 2) % 2

    def is_placable(self, grid_state: BoolGrid, line_nb: int, col_nb: int, position: PiecePos) -> bool:
        for pos in position:
            if pos[0] >= line_nb or pos[1] < 0 or pos[1] >= col_nb or \
                    pos[0] >= 0 and grid_state[pos[0]][pos[1]]:
                return False
        return True

    def is_reachable(self, piece: int, rotation: int, grid_state: BoolGrid, line_nb: int, col_nb: int,
                     position: PiecePos, final: bool,
                     tested_positions: List[PiecePos]) \
            -> Optional[PieceMov]:
        # no going back
        if position in tested_positions:
            return

        tested_positions.append(position)

        high_enough = False

        for pos in position:
            if pos[0] >= line_nb or pos[1] < 0 or pos[1] >= col_nb or \
                    pos[0] >= 0 and grid_state[pos[0]][pos[1]]:
                return

            if pos[0] < 0:
                high_enough = True

        if high_enough or self.deep_drop:
            return [position]

        # transposition
        for t_line, t_column in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            transposed = [(line + t_line, column + t_column) for line, column in position]
            if final and t_line == 1:
                if self.is_placable(grid_state, line_nb, col_nb, transposed):
                    return
            else:
                res_reachable = self.is_reachable(piece, rotation, grid_state, line_nb, col_nb,
                                                  transposed, False, tested_positions)
                if res_reachable is not None:
                    return res_reachable + [position]

        # rotations
        for rot in (-1, 1, 2):
            res_cells = reverse_rotate(piece, position, grid_state, rotation, rot)
            if res_cells:
                res_reachable = self.is_reachable(piece, (rotation - rot) % 4, grid_state, line_nb, col_nb,
                                                  res_cells, False, tested_positions)
                if res_reachable is not None:
                    return res_reachable + [position]

    def apply_in_grid(self, grid_state: BoolGrid, pos: PiecePos, clear: bool = True) -> Tuple[BoolGrid, bool]:
        # apply and clear lines
        new_grid_state = [line[:] for line in grid_state]
        for cell in pos:
            new_grid_state[cell[0]][cell[1]] = True
        skim = False

        if clear:
            to_delete = []
            for line_index in reversed(range(len(new_grid_state))):
                if sum(new_grid_state[line_index]) == len(new_grid_state[line_index]):
                    to_delete.append(line_index)

            skim = len(to_delete) > 0 and len(grid_state) - 1 not in to_delete
            for i in to_delete:
                new_grid_state.remove(new_grid_state[i])

        return new_grid_state, skim

    def grids_after_placing(self, piece: int, grid_state: BoolGrid, line_nb: int, col_nb: int,
                            column_parity: int, ignore_left: int, ignore_right: int) \
            -> Iterable[Tuple[int, PiecePos, BoolGrid, bool]]:
        rot_pos = PIECES_ROT[piece]

        authorized_rot = [0, 1, 2, 3]
        if piece == T_PIECE:
            if column_parity == 0:
                authorized_rot = [0, 2]
            elif column_parity == 1:
                authorized_rot = [1, 3]

        for rot, piece_rot_pos in enumerate(rot_pos):
            if rot not in authorized_rot:
                continue
            rot_pos_min_max = PIECES_ROT_MIN_MAX[piece][rot]
            for line_index in reversed(range(-rot_pos_min_max[0][0], line_nb - rot_pos_min_max[1][0])):
                for col_index in range(-rot_pos_min_max[0][1] + ignore_left,
                                       col_nb - ignore_right - rot_pos_min_max[1][1]):
                    translated_pos: PiecePos = []
                    pos_occupied = False
                    for pos in piece_rot_pos:
                        new_pos = (pos[0] + line_index, pos[1] + col_index)
                        if grid_state[new_pos[0]][new_pos[1]]:
                            pos_occupied = True
                            break
                        translated_pos += [new_pos]
                    if not pos_occupied:
                        if not has_orphan_cells_after(grid_state, translated_pos,
                                                      (rot_pos_min_max[0][0] + line_index,
                                                       rot_pos_min_max[0][1] + col_index),
                                                      (rot_pos_min_max[1][0] + line_index,
                                                       rot_pos_min_max[1][1] + col_index)):
                            new_grid, skim = self.apply_in_grid(grid_state, translated_pos)
                            yield rot, translated_pos, new_grid, skim

    def solve_for(self, queue: Queue, col_parity: int,
                  grid_state: BoolGrid, movements: List[PieceMov]) -> Optional[List[PieceMov]]:
        if not grid_state:
            return movements

        if not queue:
            return

        line_nb, col_nb = len(grid_state), len(grid_state[0])

        lj_count = sum(piece in (L_PIECE, J_PIECE) for piece in queue)
        current_parity = (col_parity + lj_count) % 2
        if current_parity != 0 and T_PIECE not in queue:
            # no solution because cannot correct parity
            return

        if T_PIECE in queue[1:]:
            # set to -1 for it to be ignored
            current_parity = -1

        tested_pos = []

        ignore_left, ignore_right = 0, 0
        for col in range(col_nb // 2):
            if sum(line[col] for line in grid_state) < line_nb:
                break
            ignore_left += 1
        for col in reversed(range(col_nb)):
            if sum(line[col] for line in grid_state) < line_nb:
                break
            ignore_right += 1

        new_parity = col_parity
        if queue[0] in (L_PIECE, J_PIECE):
            new_parity = (col_parity + 1) % 2

        for piece_rot, piece_pos, possible_grid_state, skim in self.grids_after_placing(queue[0], grid_state,
                                                                                        line_nb, col_nb,
                                                                                        current_parity,
                                                                                        ignore_left, ignore_right):
            if queue[0] == T_PIECE and piece_rot in (1, 3):
                new_parity = (col_parity + 1) % 2
            res = self.solve_for(queue[1:], new_parity,
                                 possible_grid_state,
                                 movements + [[piece_pos]])
            if res:
                mov = self.is_reachable(queue[0], piece_rot, grid_state,
                                        line_nb, col_nb, piece_pos, True, tested_pos)
                if mov:
                    res[res.index([piece_pos])] = mov
                    return res

    def verify_solution(self, queue: Queue, moves: List[PieceMov], grid_state: BoolGrid) -> bool:
        grid_test = [line[:] for line in grid_state]
        line_nb, col_nb = len(grid_state), len(grid_state[0])
        for i in range(len(queue)):
            pos = moves[i][-1]
            if not self.is_placable(grid_state, line_nb, col_nb, pos):
                return False
            grid_test, _ = self.apply_in_grid(grid_test, pos)
        return not grid_test

    def colums_filled(self, grid_to_test: BoolGrid) -> int:
        count = 0
        line_nb = len(grid_to_test)
        for col in range(len(grid_to_test[0])):
            count += int(sum(line[col] for line in grid_to_test) == line_nb)
        return count

    def rejected_not_contained(self, current_grid: BoolGrid, rejected: List[int],
                               queue: Queue, moves: List[PieceMov]) -> bool:
        relevant = []
        for r in rejected:
            if r + 1 > len(queue):
                continue
            relevant.append(r + 1)
        if relevant:
            for i in range(1, len(queue) - 1):
                for x in itertools.combinations(zip(queue, moves), i):
                    grid_to_test = [line[:] for line in current_grid]
                    for piece, move in x:
                        grid_to_test, _ = self.apply_in_grid(grid_to_test, move[-1], False)
                    if self.colums_filled(grid_to_test) in relevant:
                        return False
        return True

    four_boxes = [(0, 0, 0, 0), (0, 0, 3, 3), (0, 0, 3, 4), (0, 0, 4, 3), (0, 0, 4, 4), (0, 0, 5, 5), (0, 0, 6, 3), (0, 0, 6, 4), (0, 1, 3, 3), (0, 1, 3, 4), (0, 1, 6, 3), (0, 1, 6, 4), (0, 2, 4, 3), (0, 2, 4, 4), (0, 2, 6, 3), (0, 2, 6, 4), (0, 3, 0, 3), (0, 3, 0, 4), (0, 3, 1, 3), (0, 3, 1, 4), (0, 3, 2, 4), (0, 3, 3, 0), (0, 3, 3, 2), (0, 3, 3, 5), (0, 3, 3, 6), (0, 3, 4, 1), (0, 3, 4, 2), (0, 3, 4, 5), (0, 3, 4, 6), (0, 3, 5, 3), (0, 3, 5, 4), (0, 3, 6, 3), (0, 3, 6, 4), (0, 3, 6, 6), (0, 4, 0, 3), (0, 4, 0, 4), (0, 4, 1, 3), (0, 4, 2, 3), (0, 4, 2, 4), (0, 4, 3, 1), (0, 4, 3, 2), (0, 4, 3, 5), (0, 4, 3, 6), (0, 4, 4, 0), (0, 4, 4, 1), (0, 4, 4, 5), (0, 4, 4, 6), (0, 4, 5, 3), (0, 4, 5, 4), (0, 4, 6, 3), (0, 4, 6, 4), (0, 4, 6, 6), (0, 5, 0, 5), (0, 5, 3, 3), (0, 5, 3, 4), (0, 5, 4, 3), (0, 5, 4, 4), (0, 5, 5, 0), (0, 5, 6, 3), (0, 5, 6, 4), (0, 6, 0, 3), (0, 6, 0, 4), (0, 6, 1, 4), (0, 6, 2, 3), (0, 6, 3, 4), (0, 6, 3, 6), (0, 6, 4, 3), (0, 6, 4, 6), (0, 6, 5, 3), (0, 6, 5, 4), (0, 6, 6, 1), (0, 6, 6, 2), (0, 6, 6, 3), (0, 6, 6, 4), (0, 6, 6, 5), (1, 0, 3, 3), (1, 0, 3, 4), (1, 0, 6, 3), (1, 0, 6, 4), (1, 1, 3, 4), (1, 1, 4, 3), (1, 2, 6, 3), (1, 2, 6, 4), (1, 3, 0, 3), (1, 3, 0, 4), (1, 3, 4, 0), (1, 3, 6, 6), (1, 4, 1, 4), (1, 4, 3, 0), (1, 4, 4, 5), (1, 5, 3, 3), (1, 5, 6, 3), (1, 6, 0, 3), (1, 6, 0, 4), (1, 6, 2, 3), (1, 6, 3, 2), (1, 6, 3, 6), (1, 6, 4, 0), (1, 6, 6, 2), (1, 6, 6, 4), (1, 6, 6, 6), (2, 0, 4, 3), (2, 0, 4, 4), (2, 0, 6, 3), (2, 0, 6, 4), (2, 1, 6, 3), (2, 1, 6, 4), (2, 2, 3, 4), (2, 2, 4, 3), (2, 3, 2, 3), (2, 3, 3, 5), (2, 3, 4, 0), (2, 4, 0, 3), (2, 4, 0, 4), (2, 4, 3, 0), (2, 4, 6, 6), (2, 5, 4, 4), (2, 5, 6, 4), (2, 6, 0, 3), (2, 6, 0, 4), (2, 6, 1, 4), (2, 6, 3, 0), (2, 6, 4, 1), (2, 6, 4, 6), (2, 6, 6, 1), (2, 6, 6, 3), (2, 6, 6, 6), (3, 0, 0, 3), (3, 0, 0, 4), (3, 0, 1, 3), (3, 0, 1, 4), (3, 0, 2, 4), (3, 0, 3, 0), (3, 0, 3, 2), (3, 0, 3, 5), (3, 0, 3, 6), (3, 0, 4, 1), (3, 0, 4, 2), (3, 0, 4, 5), (3, 0, 4, 6), (3, 0, 5, 3), (3, 0, 5, 4), (3, 0, 6, 3), (3, 0, 6, 4), (3, 0, 6, 6), (3, 1, 0, 3), (3, 1, 0, 4), (3, 1, 3, 0), (3, 1, 4, 0), (3, 1, 5, 3), (3, 1, 6, 6), (3, 2, 0, 4), (3, 2, 2, 3), (3, 2, 3, 2), (3, 2, 3, 5), (3, 2, 4, 0), (3, 2, 5, 3), (3, 2, 5, 4), (3, 2, 6, 6), (3, 3, 0, 0), (3, 3, 0, 2), (3, 3, 0, 5), (3, 3, 1, 6), (3, 3, 2, 0), (3, 3, 2, 5), (3, 3, 3, 3), (3, 3, 3, 4), (3, 3, 4, 3), (3, 3, 4, 4), (3, 3, 5, 0), (3, 3, 5, 1), (3, 3, 5, 5), (3, 3, 6, 3), (3, 3, 6, 4), (3, 4, 0, 1), (3, 4, 0, 2), (3, 4, 0, 5), (3, 4, 0, 6), (3, 4, 1, 0), (3, 4, 1, 2), (3, 4, 1, 6), (3, 4, 2, 0), (3, 4, 2, 1), (3, 4, 2, 6), (3, 4, 3, 3), (3, 4, 3, 4), (3, 4, 4, 3), (3, 4, 4, 4), (3, 4, 5, 0), (3, 4, 5, 1), (3, 4, 5, 2), (3, 4, 6, 0), (3, 4, 6, 3), (3, 4, 6, 4), (3, 5, 0, 3), (3, 5, 0, 4), (3, 5, 1, 3), (3, 5, 2, 3), (3, 5, 2, 4), (3, 5, 3, 0), (3, 5, 3, 1), (3, 5, 3, 5), (3, 5, 3, 6), (3, 5, 4, 0), (3, 5, 5, 3), (3, 5, 5, 4), (3, 5, 6, 4), (3, 6, 0, 4), (3, 6, 0, 6), (3, 6, 1, 2), (3, 6, 2, 3), (3, 6, 2, 6), (3, 6, 3, 2), (3, 6, 3, 3), (3, 6, 3, 4), (3, 6, 4, 0), (3, 6, 4, 3), (3, 6, 4, 5), (3, 6, 5, 4), (3, 6, 6, 0), (3, 6, 6, 6), (4, 0, 0, 3), (4, 0, 0, 4), (4, 0, 1, 3), (4, 0, 2, 3), (4, 0, 2, 4), (4, 0, 3, 1), (4, 0, 3, 2), (4, 0, 3, 5), (4, 0, 3, 6), (4, 0, 4, 0), (4, 0, 4, 1), (4, 0, 4, 5), (4, 0, 4, 6), (4, 0, 5, 3), (4, 0, 5, 4), (4, 0, 6, 3), (4, 0, 6, 4), (4, 0, 6, 6), (4, 1, 0, 3), (4, 1, 1, 4), (4, 1, 3, 0), (4, 1, 4, 1), (4, 1, 4, 5), (4, 1, 5, 3), (4, 1, 5, 4), (4, 1, 6, 6), (4, 2, 0, 3), (4, 2, 0, 4), (4, 2, 3, 0), (4, 2, 4, 0), (4, 2, 5, 4), (4, 2, 6, 6), (4, 3, 0, 1), (4, 3, 0, 2), (4, 3, 0, 5), (4, 3, 0, 6), (4, 3, 1, 0), (4, 3, 1, 2), (4, 3, 1, 6), (4, 3, 2, 0), (4, 3, 2, 1), (4, 3, 2, 6), (4, 3, 3, 3), (4, 3, 3, 4), (4, 3, 4, 3), (4, 3, 4, 4), (4, 3, 5, 0), (4, 3, 5, 1), (4, 3, 5, 2), (4, 3, 6, 0), (4, 3, 6, 3), (4, 3, 6, 4), (4, 4, 0, 0), (4, 4, 0, 1), (4, 4, 0, 5), (4, 4, 1, 0), (4, 4, 1, 5), (4, 4, 2, 6), (4, 4, 3, 3), (4, 4, 3, 4), (4, 4, 4, 3), (4, 4, 4, 4), (4, 4, 5, 0), (4, 4, 5, 2), (4, 4, 5, 5), (4, 4, 6, 3), (4, 4, 6, 4), (4, 5, 0, 3), (4, 5, 0, 4), (4, 5, 1, 3), (4, 5, 1, 4), (4, 5, 2, 4), (4, 5, 3, 0), (4, 5, 4, 0), (4, 5, 4, 2), (4, 5, 4, 5), (4, 5, 4, 6), (4, 5, 5, 3), (4, 5, 5, 4), (4, 5, 6, 3), (4, 6, 0, 3), (4, 6, 0, 6), (4, 6, 1, 4), (4, 6, 1, 6), (4, 6, 2, 1), (4, 6, 3, 0), (4, 6, 3, 4), (4, 6, 3, 5), (4, 6, 4, 1), (4, 6, 4, 3), (4, 6, 4, 4), (4, 6, 5, 3), (4, 6, 6, 0), (4, 6, 6, 6), (5, 0, 0, 5), (5, 0, 3, 3), (5, 0, 3, 4), (5, 0, 4, 3), (5, 0, 4, 4), (5, 0, 5, 0), (5, 0, 6, 3), (5, 0, 6, 4), (5, 1, 3, 3), (5, 2, 4, 4), (5, 3, 0, 3), (5, 3, 0, 4), (5, 3, 3, 0), (5, 3, 3, 5), (5, 3, 3, 6), (5, 3, 4, 0), (5, 3, 5, 3), (5, 3, 5, 4), (5, 4, 0, 3), (5, 4, 0, 4), (5, 4, 3, 0), (5, 4, 4, 0), (5, 4, 4, 5), (5, 4, 4, 6), (5, 4, 5, 3), (5, 4, 5, 4), (5, 5, 0, 0), (5, 5, 3, 3), (5, 5, 3, 4), (5, 5, 4, 3), (5, 5, 4, 4), (5, 5, 5, 5), (5, 5, 6, 3), (5, 5, 6, 4), (5, 6, 0, 3), (5, 6, 0, 4), (5, 6, 3, 0), (5, 6, 3, 5), (5, 6, 3, 6), (5, 6, 4, 0), (5, 6, 4, 5), (5, 6, 4, 6), (5, 6, 5, 3), (5, 6, 5, 4), (6, 0, 0, 3), (6, 0, 0, 4), (6, 0, 1, 4), (6, 0, 2, 3), (6, 0, 3, 4), (6, 0, 3, 6), (6, 0, 4, 3), (6, 0, 4, 6), (6, 0, 5, 3), (6, 0, 5, 4), (6, 0, 6, 1), (6, 0, 6, 2), (6, 0, 6, 3), (6, 0, 6, 4), (6, 0, 6, 5), (6, 1, 0, 4), (6, 1, 2, 3), (6, 1, 3, 2), (6, 1, 3, 4), (6, 1, 4, 0), (6, 1, 4, 1), (6, 1, 6, 4), (6, 1, 6, 6), (6, 2, 0, 3), (6, 2, 1, 4), (6, 2, 3, 0), (6, 2, 3, 2), (6, 2, 4, 1), (6, 2, 4, 3), (6, 2, 6, 3), (6, 2, 6, 6), (6, 3, 0, 6), (6, 3, 1, 4), (6, 3, 2, 6), (6, 3, 3, 3), (6, 3, 3, 4), (6, 3, 3, 5), (6, 3, 4, 3), (6, 3, 6, 0), (6, 3, 6, 2), (6, 3, 6, 4), (6, 3, 6, 6), (6, 4, 0, 6), (6, 4, 1, 6), (6, 4, 2, 3), (6, 4, 3, 4), (6, 4, 4, 3), (6, 4, 4, 4), (6, 4, 4, 5), (6, 4, 6, 0), (6, 4, 6, 1), (6, 4, 6, 3), (6, 4, 6, 6), (6, 5, 0, 3), (6, 5, 0, 4), (6, 5, 3, 0), (6, 5, 3, 5), (6, 5, 3, 6), (6, 5, 4, 0), (6, 5, 4, 5), (6, 5, 4, 6), (6, 5, 5, 3), (6, 5, 5, 4), (6, 5, 6, 3), (6, 5, 6, 4), (6, 6, 0, 1), (6, 6, 0, 2), (6, 6, 0, 3), (6, 6, 0, 4), (6, 6, 0, 5), (6, 6, 1, 2), (6, 6, 1, 4), (6, 6, 2, 1), (6, 6, 2, 3), (6, 6, 3, 0), (6, 6, 3, 2), (6, 6, 3, 3), (6, 6, 3, 4), (6, 6, 4, 0), (6, 6, 4, 1), (6, 6, 4, 3), (6, 6, 4, 4), (6, 6, 5, 0), (6, 6, 5, 3), (6, 6, 5, 4), (6, 6, 6, 1), (6, 6, 6, 2), (6, 6, 6, 6)]

    def solve(self, queue: Queue, grid_state: BoolGrid, no_split: bool = False) -> Optional[Tuple[Queue, List[PieceMov]]]:
        """
            Solve for given queue and grid state
        """
        before = time.perf_counter()
        line_nb, col_nb = len(grid_state), len(grid_state[0])
        filled_cell = sum(sum(line) for line in grid_state)
        unused_cells = line_nb * col_nb - filled_cell
        if unused_cells % 4 != 0:
            print("invalid grid")
            return
        needed_pieces = unused_cells // 4
        if len(queue) < needed_pieces:
            print(f"invalid queue length : need at least {needed_pieces} but we have {len(queue)}")
            return

        grid_parity = self.get_column_parity(grid_state, line_nb, col_nb)

        if no_split:
            for queue_with_hold in self.generate_possible_queue_combinations(queue, needed_pieces):
                if filled_cell == 0:
                    ljt_sum = sum(piece in (L_PIECE, J_PIECE, T_PIECE) for piece in queue_with_hold)
                    sz_sum = sum(piece in (S_PIECE, Z_PIECE) for piece in queue_with_hold)
                    if sz_sum >= 2 and ljt_sum < 2:
                        continue
                res = self.solve_for(queue_with_hold, grid_parity, grid_state, [])
                if res:
                    print(time.perf_counter() - before)
                    return queue_with_hold, res
            return

        possible_splits = []
        col_iter = list(range((col_nb + 1) // 2)) + [col_nb - 1]
        if col_nb == 10:
            if filled_cell == 0:
                ljt_sum = sum(piece in (L_PIECE, J_PIECE, T_PIECE) for piece in queue)
                if ljt_sum < 4:
                    print("cannot split with this queue")
                    col_iter = [9]
                else:
                    col_iter = (3, 4, 2, 1, 0, 9)
            else:
                col_iter = (3, 4, 2, 1, 0, 5, 6, 7, 8, 9)
        for col in col_iter:
            current_unused = line_nb * (col + 1) - sum(sum(line[:col + 1]) for line in grid_state)
            if current_unused % 4 == 0:
                possible_splits.append(col)
        # print(f"Found possible splits : {possible_splits}")

        rejected_splits = []
        for split in possible_splits:
            # print(f"Trying split {split}")
            sub_grid = [line[:split + 1] for line in grid_state]
            filled = sum(sum(line) for line in sub_grid)
            unused = line_nb * (split + 1) - filled
            sub_needed = unused // 4
            sub_parity = self.get_column_parity(sub_grid, line_nb, split + 1)

            for queue_with_hold in self.generate_possible_queue_combinations(queue, needed_pieces):
                if split + 1 == col_nb:
                    if filled_cell == 0:
                        ljt_sum = sum(piece in (L_PIECE, J_PIECE, T_PIECE) for piece in queue_with_hold)
                        sz_sum = sum(piece in (S_PIECE, Z_PIECE) for piece in queue_with_hold)
                        if sz_sum >= 2 and ljt_sum < 2:
                            continue
                    res = self.solve_for(queue_with_hold, grid_parity, grid_state, [])
                    if res:
                        print(time.perf_counter() - before)
                        return queue_with_hold, res
                else:
                    if filled_cell == 0:
                        ljt_sum = sum(piece in (L_PIECE, J_PIECE, T_PIECE) for piece in queue_with_hold)
                        if ljt_sum < 4:
                            continue
                    left_grid = [line[:] for line in grid_state]
                    for line in left_grid:
                        for col in range(split + 1):
                            line[col] = True
                    left_parity = self.get_column_parity(left_grid, line_nb, col_nb)

                    for sub_queue, mask, left_queue in self.generate_sub_queue(queue_with_hold, sub_needed):
                        if filled == 0:
                            ljt_sum = sum(piece in (L_PIECE, J_PIECE, T_PIECE) for piece in sub_queue)
                            oi_sum = sum(piece in (I_PIECE, O_PIECE) for piece in sub_queue)
                            if oi_sum < len(sub_queue) and ljt_sum < 2:
                                continue
                        if filled_cell - filled == 0:
                            ljt_sum = sum(piece in (L_PIECE, J_PIECE, T_PIECE) for piece in left_queue)
                            sz_sum = sum(piece in (S_PIECE, Z_PIECE) for piece in left_queue)
                            if sz_sum >= 2 and ljt_sum < 2:
                                continue
                        sub_sol = self.solve_for(sub_queue, sub_parity, sub_grid, [])
                        if sub_sol and self.rejected_not_contained(sub_grid, rejected_splits, sub_queue, sub_sol):
                            full_solve = self.solve_for(left_queue, left_parity, left_grid, [])
                            if full_solve:
                                moves = []
                                for m in mask:
                                    if m == 0:
                                        moves.append(full_solve[0])
                                        full_solve = full_solve[1:]
                                    else:
                                        moves.append(sub_sol[0])
                                        sub_sol = sub_sol[1:]
                                if self.verify_solution(queue_with_hold, moves, grid_state):
                                    print(time.perf_counter() - before)
                                    return queue_with_hold, moves
                                else:
                                    print("Un-split solution failed")
                rejected_splits.append(split)
        print(time.perf_counter() - before)


if __name__ == "__main__":
    pc_finder = PCFinder()

    # print(pc_finder.generate_possible_queue_combinations([1, 2, 3], 3))
    # print(pc_finder.generate_possible_queue_combinations([1, 2, 3, 4], 3))
    #
    # grid = [
    #     [False, False, False],
    #     [False, True, True]
    # ]
    # before = time.perf_counter()
    # print("minimal horizontal L solve",
    #       pc_finder.solve([L_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #    [False, False],
    #    [False, False]
    # ]
    # before = time.perf_counter()
    # print("minimal horizontal O solve",
    #       pc_finder.solve([O_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False, False],
    #     [True, True, False]
    # ]
    # before = time.perf_counter()
    # print("minimal horizontal J solve",
    #       pc_finder.solve([J_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False, False],
    #     [True, False, True]
    # ]
    # before = time.perf_counter()
    # print("minimal horizontal T solve",
    #       pc_finder.solve([T_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False, False, False],
    # ]
    # before = time.perf_counter()
    # print("minimal horizontal I solve",
    #       pc_finder.solve([I_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [True, False, False],
    #     [False, False, True]
    # ]
    # before = time.perf_counter()
    # print("minimal horizontal S solve",
    #       pc_finder.solve([S_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False, True],
    #     [True, False, False]
    # ]
    # before = time.perf_counter()
    # print("minimal horizontal Z solve",
    #       pc_finder.solve([Z_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False],
    #     [False, True],
    #     [False, True]
    # ]
    # before = time.perf_counter()
    # print("minimal vertical J solve",
    #       pc_finder.solve([J_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False],
    #     [True, False],
    #     [True, False]
    # ]
    # before = time.perf_counter()
    # print("minimal vertical L solve",
    #       pc_finder.solve([L_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False],
    #     [False],
    #     [False],
    #     [False]
    # ]
    # before = time.perf_counter()
    # print("minimal vertical I solve",
    #       pc_finder.solve([I_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [True, False, False, False],
    #     [True, False, False, True],
    #     [True, False, True, True],
    #     [False, False, True, True]
    # ]
    # before = time.perf_counter()
    # print("180 JT solve",
    #       pc_finder.solve([J_PIECE, T_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False, False, True],
    #     [True, False, False, True],
    #     [True, True, False, True],
    #     [True, True, False, False]
    # ]
    # before = time.perf_counter()
    # print("180 LT solve",
    #       pc_finder.solve([L_PIECE, T_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [True, True, True, True, False, False, False, False, True, True],
    #     [True, True, True, True, False, False, False, True, True, True],
    #     [True, True, True, True, False, False, True, True, True, True],
    #     [True, True, True, True, False, False, False, True, True, True]
    # ]
    # before = time.perf_counter()
    # print("No hold, no rotation, 3 pieces solve",
    #       pc_finder.solve([T_PIECE, S_PIECE, Z_PIECE], grid))
    # print(time.perf_counter() - before)
    # before = time.perf_counter()
    # print("No rotation, 3 pieces solve",
    #       pc_finder.solve([Z_PIECE, T_PIECE, J_PIECE, L_PIECE], grid))
    # print(time.perf_counter() - before)
    # before = time.perf_counter()
    # print("No hold, 3 pieces solve",
    #       pc_finder.solve([T_PIECE, J_PIECE, I_PIECE], grid))
    # print(time.perf_counter() - before)
    # before = time.perf_counter()
    # print("3 pieces solve",
    #       pc_finder.solve([Z_PIECE, T_PIECE, J_PIECE, I_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [True, True, True, False, False, False, False, False, True, True],
    #     [True, True, True, False, False, False, False, True, True, True],
    #     [True, True, True, False, False, False, True, True, True, True],
    #     [True, True, True, False, False, False, False, True, True, True]
    # ]
    # before = time.perf_counter()
    # print("4 pieces solve",
    #       pc_finder.solve([I_PIECE, J_PIECE, I_PIECE, L_PIECE, O_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [True, False, False, False, False, False, False, False, False, False],
    #     [True, True, False, False, False, True, False, False, False, False],
    #     [True, True, True, True, True, True, False, False, False, False],
    #     [True, True, True, True, True, True, False, False, False, False]
    # ]
    # before = time.perf_counter()
    # print("6 pieces solve",
    #       pc_finder.solve([L_PIECE, I_PIECE, O_PIECE, T_PIECE, J_PIECE, Z_PIECE, S_PIECE], grid))
    # print(time.perf_counter() - before)
    #
    # grid = [
    #     [False, False, True, True, False, False, False, False, False, False],
    #     [False, True, True, False, False, False, False, False, False, False],
    #     [False, True, True, True, False, False, False, False, False, False],
    #     [True, True, True, True, True, False, False, False, False, False]
    # ]
    # before = time.perf_counter()
    # print("7 pieces solve",
    #       pc_finder.solve([L_PIECE, Z_PIECE, O_PIECE, T_PIECE, I_PIECE, S_PIECE, J_PIECE], grid))
    # print(time.perf_counter() - before)

    import cProfile
    import pstats

    grid = [
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False]
    ]
    # before = time.perf_counter()
    #
    # with cProfile.Profile() as pr:
    #     res = pc_finder.solve([T_PIECE, S_PIECE, Z_PIECE, L_PIECE, Z_PIECE, O_PIECE,
    #                            T_PIECE, I_PIECE, S_PIECE, J_PIECE, I_PIECE],
    #                           grid)
    #     print("11 pieces solve", res)
    #
    # print(time.perf_counter() - before)
    # stats = pstats.Stats(pr)
    # stats.sort_stats(pstats.SortKey.TIME)
    # stats.dump_stats(filename="11_piece_solve_1.prof")

    before = time.perf_counter()
    with cProfile.Profile() as pr:
        res = pc_finder.solve([L_PIECE, S_PIECE, O_PIECE, Z_PIECE, Z_PIECE, J_PIECE,
                               T_PIECE, O_PIECE, S_PIECE, L_PIECE, I_PIECE],
                              grid)
        print("11 pieces solve", res)
    print(time.perf_counter() - before)
    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename="11_piece_solve_1.prof")
    #
    # grid = [
    #     [False, False, False, False, False, False, True, True, False, False],
    #     [False, False, False, False, False, True, True, True, True, False],
    #     [False, False, False, False, False, False, True, True, True, False],
    #     [False, False, False, False, False, False, False, True, True, True]
    # ]
    #
    # before = time.perf_counter()
    # print("8 pieces no solve",
    #       pc_finder.solve([O_PIECE, I_PIECE, L_PIECE, Z_PIECE, J_PIECE,
    #                        J_PIECE, I_PIECE, S_PIECE, T_PIECE, Z_PIECE, L_PIECE],
    #                       grid))
    # print(time.perf_counter() - before)

    # grid = [
    #     [False, False, False, False],
    #     [False, False, False, False],
    #     [False, False, False, False],
    #     [False, False, False, False]
    # ]
    # pc_finder.no_hold = True
    # solves = []
    # solves_printable = []
    # tjl_count = [0, 0, 0, 0, 0]
    # n = ['I', 'S', 'Z', 'L', 'J', 'O', 'T']
    # for queue in itertools.product(list(range(7)), repeat=len(grid[0])):
    #     s = pc_finder.solve(queue, grid, no_split=True)
    #     if s:
    #         solves.append(queue)
    #         solves_printable.append(''.join(n[p] for p in queue))
    #         tjl_count[queue.count(L_PIECE) + queue.count(J_PIECE) + queue.count(T_PIECE)] += 1
    # print(solves)
    # print(solves_printable)
    # print(tjl_count)


