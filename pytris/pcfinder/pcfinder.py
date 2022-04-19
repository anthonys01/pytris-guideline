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
    def __init__(self):
        ...

    @staticmethod
    def hash_grid(grid_to_hash: BoolGrid) -> int:
        res = 0
        for line in grid_to_hash:
            for cell in line:
                res = (res << 1) + int(cell)
        return res

    @staticmethod
    def hash_piece_pos(piece: int, rotation: int, position: PiecePos) -> int:
        res = ((piece << 8) + rotation << 8)
        for pos in position:
            res = (res << 4) + 8 + pos[0]
            res = (res << 4) + 15 + pos[1]
        return res

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

    def is_reachable(self, piece: int, rotation: int, grid_state: BoolGrid,
                     position: PiecePos,
                     tested_positions: List[PiecePos]) \
            -> Optional[PieceMov]:
        # no going back
        if position in tested_positions:
            return

        tested_positions.append(position)

        for pos in position:
            if pos[0] < 0:
                return [position]

            if pos[0] < 0 or pos[0] >= len(grid_state) or \
                    pos[1] < 0 or pos[1] >= len(grid_state[0]) or \
                    grid_state[pos[0]][pos[1]]:
                return

        # transposition
        for t_line, t_column in ((-1, 0), (0, 1), (0, -1), (1, 0)):
            transposed = [(line + t_line, column + t_column) for line, column in position]
            res_reachable = self.is_reachable(piece, rotation,
                                              grid_state, transposed, tested_positions)
            if res_reachable is not None:
                return res_reachable + [position]

        # rotations
        for rot in (-1, 1, 2):
            res_cells = reverse_rotate(piece, position, grid_state, rotation, rot)
            if res_cells:
                res_reachable = self.is_reachable(piece, (rotation - rot) % 4,
                                                  grid_state, res_cells, tested_positions)
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
            -> Iterable[Tuple[PieceMov, BoolGrid]]:
        rot_pos = PIECES_ROT[piece]

        for rot, piece_rot_pos in enumerate(rot_pos):
            tested_pos = []
            for line_index in reversed(range(-1, len(grid_state))):
                for col_index in range(-1, len(grid_state[line_index])):
                    translated_pos = []
                    in_the_box = True
                    for pos in piece_rot_pos:
                        new_pos = (pos[0] + line_index, pos[1] + col_index)
                        in_the_box &= 0 <= new_pos[0] < len(grid_state) \
                            and 0 <= new_pos[1] < len(grid_state[line_index])
                        translated_pos += [new_pos]
                    if in_the_box:
                        mov = self.is_reachable(piece, rot, grid_state, translated_pos, tested_pos)
                        if mov is not None:
                            yield mov, self.apply_in_grid(grid_state, translated_pos)

    def solve_for(self, queue: Queue,
                  grid_state: BoolGrid, movements: List[PieceMov]) -> Optional[List[PieceMov]]:
        if not grid_state:
            return movements

        if not queue:
            return

        for piece_movements, possible_grid_state in self.grids_after_placing(queue[0], grid_state):
            # TODO test parity to eliminate early
            res = self.solve_for(queue[1:],
                                 possible_grid_state,
                                 movements + [piece_movements])
            if res:
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

    print(pc_finder.generate_possible_queue_combinations([1, 2, 3], 3))
    print(pc_finder.generate_possible_queue_combinations([1, 2, 3, 4], 3))

    grid = [
        [False, False, False],
        [False, True, True]
    ]
    print("minimal horizontal L solve",
          pc_finder.solve([L_PIECE], grid))

    grid = [
       [False, False],
       [False, False]
    ]
    print("minimal horizontal O solve",
          pc_finder.solve([O_PIECE], grid))

    grid = [
        [False, False, False],
        [True, True, False]
    ]
    print("minimal horizontal J solve",
          pc_finder.solve([J_PIECE], grid))

    grid = [
        [False, False, False],
        [True, False, True]
    ]
    print("minimal horizontal T solve",
          pc_finder.solve([T_PIECE], grid))

    grid = [
        [False, False, False, False],
    ]
    print("minimal horizontal I solve",
          pc_finder.solve([I_PIECE], grid))

    grid = [
        [True, False, False],
        [False, False, True]
    ]
    print("minimal horizontal S solve",
          pc_finder.solve([S_PIECE], grid))

    grid = [
        [False, False, True],
        [True, False, False]
    ]
    print("minimal horizontal Z solve",
          pc_finder.solve([Z_PIECE], grid))

    grid = [
        [False, False],
        [False, True],
        [False, True]
    ]
    print("minimal vertical J solve",
          pc_finder.solve([J_PIECE], grid))

    grid = [
        [False, False],
        [True, False],
        [True, False]
    ]
    print("minimal horizontal L solve",
          pc_finder.solve([L_PIECE], grid))

    grid = [
        [False],
        [False],
        [False],
        [False]
    ]
    print("minimal vertical I solve",
          pc_finder.solve([I_PIECE], grid))

    grid = [
        [True, False, False, False],
        [True, False, False, True],
        [True, False, True, True],
        [False, False, True, True]
    ]
    print("180 JT solve",
          pc_finder.solve([J_PIECE, T_PIECE], grid))

    grid = [
        [False, False, False, True],
        [True, False, False, True],
        [True, True, False, True],
        [True, True, False, False]
    ]
    print("180 LT solve",
          pc_finder.solve([L_PIECE, T_PIECE], grid))

    grid = [
        [True, True, True, True, False, False, False, False, True, True],
        [True, True, True, True, False, False, False, True, True, True],
        [True, True, True, True, False, False, True, True, True, True],
        [True, True, True, True, False, False, False, True, True, True]
    ]
    print("No hold, no rotation, 3 pieces solve",
          pc_finder.solve([T_PIECE, S_PIECE, Z_PIECE], grid))
    print("No rotation, 3 pieces solve",
          pc_finder.solve([Z_PIECE, T_PIECE, J_PIECE, L_PIECE], grid))
    print("No hold, 3 pieces solve",
          pc_finder.solve([T_PIECE, J_PIECE, I_PIECE], grid))
    print("3 pieces solve",
          pc_finder.solve([Z_PIECE, T_PIECE, J_PIECE, I_PIECE], grid))

    grid = [
        [True, True, True, False, False, False, False, False, True, True],
        [True, True, True, False, False, False, False, True, True, True],
        [True, True, True, False, False, False, True, True, True, True],
        [True, True, True, False, False, False, False, True, True, True]
    ]
    print("4 pieces solve",
          pc_finder.solve([I_PIECE, J_PIECE, I_PIECE, L_PIECE, O_PIECE], grid))

    grid = [
        [True, False, False, False, False, False, False, False, False, False],
        [True, True, False, False, False, True, False, False, False, False],
        [True, True, True, True, True, True, False, False, False, False],
        [True, True, True, True, True, True, False, False, False, False]
    ]
    print("6 pieces solve",
          pc_finder.solve([L_PIECE, I_PIECE, O_PIECE, T_PIECE, J_PIECE, Z_PIECE, S_PIECE], grid))

    import time
    before = time.perf_counter()
    grid = [
        [False, False, True, True, False, False, False, False, False, False],
        [False, True, True, False, False, False, False, False, False, False],
        [False, True, True, True, False, False, False, False, False, False],
        [True, True, True, True, True, False, False, False, False, False]
    ]
    print("7 pieces solve",
          pc_finder.solve([L_PIECE, Z_PIECE, O_PIECE, T_PIECE, I_PIECE, S_PIECE, J_PIECE], grid))
    print(time.perf_counter() - before)

    grid = [
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False],
        [False, False, False, False, False, False, False, False, False, False]
    ]
    print("11 pieces solve",
          pc_finder.solve([T_PIECE, S_PIECE, Z_PIECE, L_PIECE, Z_PIECE, O_PIECE,
                           T_PIECE, I_PIECE, S_PIECE, J_PIECE, I_PIECE],
                          grid))
