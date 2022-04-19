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
    def generate_possible_queue_combinations(queue: Queue, res_size: int) -> List[Queue]:
        """
            Possible pieces order by user hold. Only generate queues of given size
        """
        if res_size > len(queue):
            return []
        if res_size == len(queue):
            return [queue[:]]

        working_nodes = [[queue[:], [], []]]

        finished = False
        while not finished:
            node = working_nodes.pop()
            if len(node[2]) == res_size:
                working_nodes += [node]
                finished = True
                break
            res = []
            piece = node[0][0]
            # place
            res += [[node[0][1:], node[1][:], node[2] + [piece]]]
            # hold and place
            if not node[1]:
                second_piece = node[0][1]
                res += [[node[0][2:], [piece], node[2] + [second_piece]]]
            else:
                res += [[node[0][1:], [piece], node[2] + node[1]]]
            working_nodes = res + working_nodes

        return [node[2] for node in working_nodes]

    def is_reachable_for(self, piece: int, rotation: int, grid_state: BoolGrid,
                         position: PiecePos,
                         tested_positions: List[PiecePos]) \
            -> Optional[List[PiecePos]]:
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
            res_reachable = self.is_reachable_for(piece, rotation,
                                                  grid_state, transposed, tested_positions)
            if res_reachable is not None:
                return res_reachable + [position]

        # rotations
        for rot in (-1, 1, 2):
            res_cells = reverse_rotate(piece, position, grid_state, rotation, rot)
            if res_cells:
                res_reachable = self.is_reachable_for(piece, (rotation - rot) % 4,
                                                      grid_state, res_cells, tested_positions)
                if res_reachable is not None:
                    return res_reachable + [position]

    def is_reachable(self, piece: int, rotation: int, grid_state: BoolGrid,
                     position: PiecePos) -> Optional[List]:
        return self.is_reachable_for(piece, rotation, grid_state, position, [])

    def apply_in_grid(self, grid_state: BoolGrid,
                      pos: PiecePos) -> List[List[int]]:
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
        rot_pos = []

        if piece == I_PIECE:
            rot_pos = [[(0, 0), (0, 1), (0, 2), (0, 3)],
                       [(0, 2), (1, 2), (2, 2), (3, 2)]]
        elif piece in (S_PIECE, Z_PIECE):
            rot_pos = PIECES_ROT[piece][:2]
        else:
            rot_pos = PIECES_ROT[piece]

        for rot, piece_rot_pos in enumerate(rot_pos):
            for line_index in reversed(range(len(grid_state))):
                for col_index in range(len(grid_state[line_index])):
                    translated_pos = []
                    for pos in piece_rot_pos:
                        translated_pos += [(pos[0] + line_index, pos[1] + col_index)]
                    mov = self.is_reachable(piece, rot, grid_state, translated_pos)
                    if mov:
                        yield mov, self.apply_in_grid(grid_state, translated_pos)

    def solve_for(self, queue: Queue,
                  grid_state: BoolGrid, movements: List[PieceMov]) -> Optional[List[PieceMov]]:
        if not grid_state:
            return movements

        if not queue:
            return

        for i, piece in enumerate(queue):
            for piece_movements, possible_grid_state in self.grids_after_placing(piece, grid_state):
                res = self.solve_for(queue[i + 1:],
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
    print("no hold, 4 pieces solve",
          pc_finder.solve([I_PIECE, I_PIECE, L_PIECE, O_PIECE], grid))
