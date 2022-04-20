"""
    Find PC sequences for given queue and board
"""
from typing import List, Tuple, Optional, Iterable

from pytris.pieces import T_PIECE, Z_PIECE, L_PIECE, J_PIECE, S_PIECE, I_PIECE, O_PIECE, PIECES_ROT, reverse_rotate
from pytris.typehints import BoolGrid, PiecePos


Queue = List[int]
PieceMov = List[PiecePos]


class PCFinder:
    """
        PC Solver
    """
    def __init__(self, *, deep_drop: bool = False):
        self.deep_drop = deep_drop

    @staticmethod
    def generate_possible_queue_combinations(queue: Queue, res_size: int) -> List[Queue]:
        """
            Possible pieces order by user hold. Only generate queues of given size
        """
        if res_size > len(queue):
            return []

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

    @staticmethod
    def get_column_parity(grid_state: BoolGrid) -> int:
        if not grid_state:
            return 0

        col_sums = [0, len(grid_state) * (len(grid_state[0]) % 2)]
        for line in grid_state:
            for col in range(len(grid_state[0])):
                col_sums[col % 2] += int(line[col])
        return ((col_sums[0] - col_sums[1]) // 2) % 2

    def is_placable(self, grid_state: BoolGrid, position: PiecePos) -> bool:
        for pos in position:
            if pos[0] >= len(grid_state) or pos[1] < 0 or pos[1] >= len(grid_state[0]) or \
                    pos[0] >= 0 and grid_state[pos[0]][pos[1]]:
                return False
        return True

    def is_reachable(self, piece: int, rotation: int, grid_state: BoolGrid,
                     position: PiecePos, final: bool,
                     tested_positions: List[PiecePos]) \
            -> Optional[PieceMov]:
        # no going back
        if position in tested_positions:
            return

        tested_positions.append(position)

        high_enough = False

        for pos in position:
            if pos[0] >= len(grid_state) or pos[1] < 0 or pos[1] >= len(grid_state[0]) or \
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
                if self.is_placable(grid_state, transposed):
                    return
            else:
                res_reachable = self.is_reachable(piece, rotation,
                                                  grid_state, transposed, False, tested_positions)
                if res_reachable is not None:
                    return res_reachable + [position]

        # rotations
        for rot in (-1, 1, 2):
            res_cells = reverse_rotate(piece, position, grid_state, rotation, rot)
            if res_cells:
                res_reachable = self.is_reachable(piece, (rotation - rot) % 4,
                                                  grid_state, res_cells, False, tested_positions)
                if res_reachable is not None:
                    return res_reachable + [position]

    def apply_in_grid(self, grid_state: BoolGrid, pos: PiecePos) -> BoolGrid:
        # apply and clear lines
        new_grid_state = [line[:] for line in grid_state]
        for cell in pos:
            new_grid_state[cell[0]][cell[1]] = True

        to_delete = []
        for line_index in reversed(range(len(new_grid_state))):
            if sum(new_grid_state[line_index]) == len(new_grid_state[line_index]):
                to_delete.append(line_index)

        for i in to_delete:
            new_grid_state.remove(new_grid_state[i])

        return new_grid_state

    def grids_after_placing(self, piece: int, grid_state: BoolGrid) \
            -> Iterable[Tuple[int, PiecePos, BoolGrid]]:
        rot_pos = PIECES_ROT[piece]

        for rot, piece_rot_pos in enumerate(rot_pos):
            for line_index in reversed(range(-1, len(grid_state))):
                for col_index in range(-1, len(grid_state[line_index])):
                    translated_pos: PiecePos = []
                    in_the_box = True
                    for pos in piece_rot_pos:
                        new_pos = (pos[0] + line_index, pos[1] + col_index)
                        in_the_box &= 0 <= new_pos[0] < len(grid_state) \
                            and 0 <= new_pos[1] < len(grid_state[line_index])
                        translated_pos += [new_pos]
                    if in_the_box and self.is_placable(grid_state, translated_pos):
                        yield rot, translated_pos, self.apply_in_grid(grid_state, translated_pos)

    def solve_for(self, queue: Queue,
                  grid_state: BoolGrid, movements: List[PieceMov]) -> Optional[List[PieceMov]]:
        if not grid_state:
            return movements

        if not queue:
            return

        grid_parity = self.get_column_parity(grid_state)
        lj_count = sum(piece in (L_PIECE, J_PIECE) for piece in queue)
        current_parity = (grid_parity + lj_count) % 2
        if current_parity != 0 and T_PIECE not in queue:
            # no solution because cannot correct parity
            return

        tested_pos = []

        for piece_rot, piece_pos, possible_grid_state in self.grids_after_placing(queue[0], grid_state):
            res = self.solve_for(queue[1:],
                                 possible_grid_state,
                                 movements + [[piece_pos]])
            if res:
                mov = self.is_reachable(queue[0], piece_rot, grid_state, piece_pos, True, tested_pos)
                if mov:
                    res[res.index([piece_pos])] = mov
                    return res

    def solve(self, queue: Queue, grid_state: BoolGrid) -> Optional[Tuple[Queue, List[PieceMov]]]:
        """
            Solve for given queue and grid state
        """
        filled_cell = sum(sum(line) for line in grid_state)
        unused_cells = len(grid_state) * len(grid_state[0]) - filled_cell
        if unused_cells % 4 != 0:
            print("invalid grid")
            return
        needed_pieces = unused_cells // 4
        if len(queue) < needed_pieces:
            print(f"invalid queue length : need at least {needed_pieces} but we have {len(queue)}")
            return
        for gen_queue in self.generate_possible_queue_combinations(queue, needed_pieces):
            res = self.solve_for(gen_queue, grid_state, [])
            if res:
                return gen_queue, res


if __name__ == "__main__":
    pc_finder = PCFinder()

    import time

    print(pc_finder.generate_possible_queue_combinations([1, 2, 3], 3))
    print(pc_finder.generate_possible_queue_combinations([1, 2, 3, 4], 3))

    grid = [
        [False, False, False],
        [False, True, True]
    ]
    before = time.perf_counter()
    print("minimal horizontal L solve",
          pc_finder.solve([L_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
       [False, False],
       [False, False]
    ]
    before = time.perf_counter()
    print("minimal horizontal O solve",
          pc_finder.solve([O_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, False],
        [True, True, False]
    ]
    before = time.perf_counter()
    print("minimal horizontal J solve",
          pc_finder.solve([J_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, False],
        [True, False, True]
    ]
    before = time.perf_counter()
    print("minimal horizontal T solve",
          pc_finder.solve([T_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, False, False],
    ]
    before = time.perf_counter()
    print("minimal horizontal I solve",
          pc_finder.solve([I_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [True, False, False],
        [False, False, True]
    ]
    before = time.perf_counter()
    print("minimal horizontal S solve",
          pc_finder.solve([S_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, True],
        [True, False, False]
    ]
    before = time.perf_counter()
    print("minimal horizontal Z solve",
          pc_finder.solve([Z_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False],
        [False, True],
        [False, True]
    ]
    before = time.perf_counter()
    print("minimal vertical J solve",
          pc_finder.solve([J_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False],
        [True, False],
        [True, False]
    ]
    before = time.perf_counter()
    print("minimal vertical L solve",
          pc_finder.solve([L_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False],
        [False],
        [False],
        [False]
    ]
    before = time.perf_counter()
    print("minimal vertical I solve",
          pc_finder.solve([I_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [True, False, False, False],
        [True, False, False, True],
        [True, False, True, True],
        [False, False, True, True]
    ]
    before = time.perf_counter()
    print("180 JT solve",
          pc_finder.solve([J_PIECE, T_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, False, True],
        [True, False, False, True],
        [True, True, False, True],
        [True, True, False, False]
    ]
    before = time.perf_counter()
    print("180 LT solve",
          pc_finder.solve([L_PIECE, T_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [True, True, True, True, False, False, False, False, True, True],
        [True, True, True, True, False, False, False, True, True, True],
        [True, True, True, True, False, False, True, True, True, True],
        [True, True, True, True, False, False, False, True, True, True]
    ]
    before = time.perf_counter()
    print("No hold, no rotation, 3 pieces solve",
          pc_finder.solve([T_PIECE, S_PIECE, Z_PIECE], grid))
    print(time.perf_counter() - before)
    before = time.perf_counter()
    print("No rotation, 3 pieces solve",
          pc_finder.solve([Z_PIECE, T_PIECE, J_PIECE, L_PIECE], grid))
    print(time.perf_counter() - before)
    before = time.perf_counter()
    print("No hold, 3 pieces solve",
          pc_finder.solve([T_PIECE, J_PIECE, I_PIECE], grid))
    print(time.perf_counter() - before)
    before = time.perf_counter()
    print("3 pieces solve",
          pc_finder.solve([Z_PIECE, T_PIECE, J_PIECE, I_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [True, True, True, False, False, False, False, False, True, True],
        [True, True, True, False, False, False, False, True, True, True],
        [True, True, True, False, False, False, True, True, True, True],
        [True, True, True, False, False, False, False, True, True, True]
    ]
    before = time.perf_counter()
    print("4 pieces solve",
          pc_finder.solve([I_PIECE, J_PIECE, I_PIECE, L_PIECE, O_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [True, False, False, False, False, False, False, False, False, False],
        [True, True, False, False, False, True, False, False, False, False],
        [True, True, True, True, True, True, False, False, False, False],
        [True, True, True, True, True, True, False, False, False, False]
    ]
    before = time.perf_counter()
    print("6 pieces solve",
          pc_finder.solve([L_PIECE, I_PIECE, O_PIECE, T_PIECE, J_PIECE, Z_PIECE, S_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, True, True, False, False, False, False, False, False],
        [False, True, True, False, False, False, False, False, False, False],
        [False, True, True, True, False, False, False, False, False, False],
        [True, True, True, True, True, False, False, False, False, False]
    ]
    before = time.perf_counter()
    print("7 pieces solve",
          pc_finder.solve([L_PIECE, Z_PIECE, O_PIECE, T_PIECE, I_PIECE, S_PIECE, J_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False]
    ]
    before = time.perf_counter()
    print("11 pieces solve",
          pc_finder.solve([T_PIECE, S_PIECE, Z_PIECE, L_PIECE, Z_PIECE, O_PIECE,
                           T_PIECE, I_PIECE, S_PIECE, J_PIECE, I_PIECE],
                          grid))
    print(time.perf_counter() - before)

    before = time.perf_counter()
    print("11 pieces solve",
          pc_finder.solve([L_PIECE, S_PIECE, O_PIECE, Z_PIECE, Z_PIECE, J_PIECE,
                           T_PIECE, O_PIECE, S_PIECE, L_PIECE, I_PIECE],
                          grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, False, False, False, False, True, True, False, False],
        [False, False, False, False, False, True, True, True, True, False],
        [False, False, False, False, False, False, True, True, True, False],
        [False, False, False, False, False, False, False, True, True, True]
    ]

    before = time.perf_counter()
    print("8 pieces no solve",
          pc_finder.solve([O_PIECE, I_PIECE, L_PIECE, Z_PIECE, J_PIECE,
                           J_PIECE, I_PIECE, S_PIECE, T_PIECE, Z_PIECE, L_PIECE],
                          grid))
    print(time.perf_counter() - before)

