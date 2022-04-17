"""
Player state on the board.

Manage piece, hold, queue...
"""
import random
from typing import List

import pygame
import pygame_gui.elements.ui_label

from pytris.cell import Cell
from pytris.grid import Grid
from pytris.keymanager import KeyManager, Key
from pytris.pieces import *
from pytris.gamemode import *


class Player(pygame.sprite.Sprite):
    """
        Player state
    """

    CELL = [1, 2, 3, 4, 5, 6, 7]
    SPAWN_POS = {
        I_PIECE: (1, 3),
        J_PIECE: (0, 3),
        L_PIECE: (0, 3),
        O_PIECE: (0, 4),
        S_PIECE: (0, 3),
        Z_PIECE: (0, 3),
        T_PIECE: (0, 3)
    }

    MOVE_ROT = "rotation"
    MOVE_KICK = "wall_kick"
    MOVE_TST_KICK = "tst_fin_kick"
    MOVE_TRANS = "translation"

    ALLOWED_WIGGLES = 5
    UNMOVING_TICKS_LOCK = 2
    MOVING_TICKS_LOCK = 8

    def __init__(self, gui_manager: pygame_gui.UIManager, key_manager: KeyManager, game_mode: int, seed: str = None):
        super().__init__()
        self.player_ui_left = 0
        self.player_ui_top = 70

        self._game_mode = game_mode

        self._key_manager = key_manager
        self._gui_manager = gui_manager
        self._seed = seed
        self._randomizer = random.Random(self._seed)

        # grid with (X,Y) coordinates. X lines going down, Y columns going right
        self.grid = Grid(self.player_ui_left + 95, self.player_ui_top)
        # if current piece is not movable by the player
        self.locked = False

        self._topped_out = False

        # das trigger. start using arr once das_load >= das
        self.das: int = 6

        # arr == 0 -> immediate
        # 0 < arr < 1 -> each frame move int(1 / arr) cell
        # arr >= 1 move 1 block each int(arr) frame
        self.arr: float = 0
        # used if arr >= 1
        self._arr_load = 0

        # sd == 0 -> immediate
        # 0 < sd < 1 -> each frame move int(1 / sd) cell
        # sd >= 1 move 1 block each int(sd) frame
        self.sd: float = 0
        # used if sd >= 1
        self._sd_load = 0

        # current piece type moved by the player
        self._current_piece = None
        # position of the current piece's minos
        self._cells: List[(int, int)] = []
        # number of wiggles allowed at the bottom of the board before locking piece
        self._wiggles_left = self.ALLOWED_WIGGLES
        # current height of piece (height of the "highest" mino, so the lowest on the board)
        self._current_height = 1
        # max height reached with current piece (height is same notion as current_height)
        self._max_height = 1
        # rotation state of current piece
        # (0 - initial state, 1 - CW from initial, 2 - 180 from initial, 3 CCW from initial)
        self._rotation = 0
        # user piece queue
        self._queue = []
        # current holt piece type
        self._hold_piece = None
        # DAS load counter. Piece start scrolling after this counter is charged higher than DAS trigger
        self._das_load = 0
        # last move type (rotation, kick, tst kick, translation)
        self._last_move = None
        # if the piece is unmoving at the bottom, we accept multiple locking ticks before locking
        self._locking_tick_unmoving_lock = self.UNMOVING_TICKS_LOCK
        # if the piece is moving at the bottom, we accept multiple locking ticks before locking
        self._locking_tick_moving_lock = self.MOVING_TICKS_LOCK
        # if player just holt a piece. Cannot hold again until current piece is locked
        self._holt = False
        # last piece translation direction. 0 unmoving, negative left, positive right
        self._last_dir = 0

        # current ren combo
        self._combo = -1
        # current back to back
        self._back_to_back = -1
        # current score
        self.score = 0

        # number of pieces used - for stats
        self.piece_nb = 0
        # number of lines cleared - for stats
        self._lines_cleared = 0
        # time in ms - for stats
        self._time: int = 0
        # misc stats
        self.other_stats = {
            "T-spin": 0,
            "T-spin mini": 0,
            "T-spin Single": 0,
            "T-spin Double": 0,
            "T-spin Triple": 0,
            "T-spin mini Single": 0,
            "T-spin mini Double": 0,
            "Single": 0,
            "Double": 0,
            "Triple": 0,
            "Quad": 0,
            "Max combo": 0,
            "Max Back-to-Back": 0,
            "Perfect Clears": 0
        }

        self._damage_textbox = pygame_gui.elements.UITextBox(
            "",
            pygame.Rect(self.player_ui_left, self.player_ui_top + 130, 90, 150), gui_manager)

        self._combo_textbox = pygame_gui.elements.UITextBox(
            "",
            pygame.Rect(self.player_ui_left, self.player_ui_top + 280, 90, 50), gui_manager)

        self._stats_textbox = pygame_gui.elements.UITextBox(
            self._get_stats_text(),
            pygame.Rect(self.player_ui_left, self.player_ui_top + 330, 90, 200), gui_manager)

        self._score_textbox = pygame_gui.elements.UITextBox(
            self._get_score_text(),
            pygame.Rect(self.player_ui_left + 360, self.player_ui_top + 400, 90, 90), gui_manager)

        self._perfect_clear_textbox = pygame_gui.elements.UILabel(
            pygame.Rect(self.player_ui_left + 120, self.player_ui_top + 180, 200, 50),
            "",
            gui_manager,
            object_id="perfect_clear"
        )

    @property
    def pps(self) -> str:
        pps = 0
        if self._time > 0:
            pps = 1000 * self.piece_nb / self._time
        return f"{pps:.2f}"

    @property
    def time(self) -> str:
        if self._game_mode in (FREE_PLAY_MODE, SPRINT_MODE):
            ms = self._time % 1000
            total_secs = self._time // 1000
            minutes = total_secs // 60
            secs = total_secs % 60
            return f"{minutes:0>2}:{secs:0>2}.{ms:0>3}"
        elif self._game_mode == ULTRA_MODE:
            time_left = 120000 - self._time
            ms = time_left % 1000
            total_secs = time_left // 1000
            minutes = total_secs // 60
            secs = total_secs % 60
            return f"{minutes:0>2}:{secs:0>2}.{ms:0>3}"
        return "00:00.000"

    def reset(self):
        self.grid.reset()
        self._randomizer = random.Random(self._seed)
        self.piece_nb = 0
        self._lines_cleared = 0
        self._queue = []
        self._hold_piece = None
        self._current_piece = None
        self._das_load = 0
        self._combo = -1
        self._back_to_back = -1
        self._arr_load = 0
        self._sd_load = 0
        self.score = 0
        self._time = 0
        self._topped_out = False
        self._damage_textbox.set_text("")
        self._combo_textbox.set_text("")
        self._perfect_clear_textbox.set_text("")
        self.other_stats = {
            "T-spin": 0,
            "T-spin mini": 0,
            "T-spin Single": 0,
            "T-spin Double": 0,
            "T-spin Triple": 0,
            "T-spin mini Single": 0,
            "T-spin mini Double": 0,
            "Single": 0,
            "Double": 0,
            "Triple": 0,
            "Quad": 0,
            "Max combo": 0,
            "Max Back-to-Back": 0,
            "Perfect Clears": 0
        }

    def start(self):
        self.set_next_from_queue()
        self.spawn_piece()

    def game_finished(self) -> bool:
        if self._topped_out:
            return True
        if self._game_mode == SPRINT_MODE:
            return self._lines_cleared >= 40
        if self._game_mode == ULTRA_MODE:
            return 120000 - self._time <= 0
        return False

    def _add_next_bag_to_queue(self):
        next_pieces = list(range(7))
        self._randomizer.shuffle(next_pieces)
        self._queue = next_pieces + self._queue

    def _get_preview(self):
        return reversed(self._queue[-5:])

    def set_next_from_queue(self):
        """
        set piece type to next in queue. If queue is small enough, add a new bag to the queue
        """
        if len(self._queue) < 8:
            self._add_next_bag_to_queue()
        self._current_piece = self._queue.pop()
        self._holt = False

    def _get_spawn_cells(self, piece_type: int):
        return [(self.SPAWN_POS[piece_type][0] + piece[0],
                 self.SPAWN_POS[piece_type][1] + piece[1])
                for piece in PIECES_ROT[piece_type][0]]

    def spawn_piece(self) -> bool:
        """
        Try to spawn the tetromino piece in the spawn area. Succeed iif all needed cells are empty
        :return: True if succeeded, False otherwise
        """
        spawn_cells = self._get_spawn_cells(self._current_piece)
        for pos in spawn_cells:
            if self.grid.get_cell(pos).cell_type != Cell.EMPTY:
                self._topped_out = True
                return False
        for pos in spawn_cells:
            self.grid.get_cell(pos).cell_type = self.CELL[self._current_piece]
        self._cells = spawn_cells
        self.locked = False
        self._current_height = 1
        self._max_height = 1
        self._rotation = 0
        self._last_move = None
        self._locking_tick_unmoving_lock = self.UNMOVING_TICKS_LOCK
        self._locking_tick_moving_lock = self.MOVING_TICKS_LOCK
        return True

    def _is_on_top_of_something(self) -> bool:
        return self._cells == self.grid.get_hd_pos(self._cells)

    @staticmethod
    def _get_max_height(*cells) -> int:
        return max(cell_pos[0] for cell_pos in cells)

    def _rotate(self, rotation: int):
        if self._current_piece == O_PIECE:
            return

        old_base = PIECES_ROT[self._current_piece][self._rotation]
        new_rotation = (self._rotation + rotation) % 4
        new_base = PIECES_ROT[self._current_piece][new_rotation]
        new_cells = []
        for i in range(4):
            new_cells.append((self._cells[i][0] - old_base[i][0] + new_base[i][0],
                              self._cells[i][1] - old_base[i][1] + new_base[i][1]))
        correct_mode = -1
        kick_table = I_WALL_KICKS if self._current_piece == I_PIECE else WALL_KICKS
        allowed_kicks = kick_table[self._rotation][new_rotation]
        for mode in range(len(allowed_kicks)):
            correct = True
            transposed_cells = [(cell_pos[0] - allowed_kicks[mode][1],
                                 cell_pos[1] + allowed_kicks[mode][0]) for cell_pos in new_cells]
            for cell_pos in set(transposed_cells).difference(self._cells):
                cell = self.grid.get_cell(cell_pos)
                if cell is None or cell.cell_type != Cell.EMPTY:
                    correct = False
                    break
            if correct:
                correct_mode = mode
                new_cells = transposed_cells
                break
        if correct_mode == -1:
            return

        if correct_mode == 0:
            self._last_move = self.MOVE_ROT
        elif self._rotation in (0, 2):
            # possible TST or fin kicks
            if correct_mode == 4:
                self._last_move = self.MOVE_TST_KICK
            else:
                self._last_move = self.MOVE_KICK
        else:
            self._last_move = self.MOVE_KICK

        for cell in self._cells:
            self.grid.get_cell(cell).cell_type = Cell.EMPTY
        for cell in new_cells:
            self.grid.get_cell(cell).cell_type = self.CELL[self._current_piece]
        self._cells = new_cells
        self._rotation = new_rotation

    def is_tspin(self) -> bool:
        """
        test if we have a tspin

        we need a T-piece that was rotated or kicked
        3 or its 4 corners need to be filled
        and 2 of its front corners need to be filled (except for tst and fin kicks)
        """
        if self._current_piece != T_PIECE or self._last_move == self.MOVE_TRANS:
            return False
        center = self._cells[1]
        corners = [
            (center[0] - 1, center[1] - 1),
            (center[0] - 1, center[1] + 1),
            (center[0] + 1, center[1] - 1),
            (center[0] + 1, center[1] + 1)
        ]

        def _is_used(cell_pos):
            cell = self.grid.get_cell(cell_pos)
            return cell is None or cell.cell_type != Cell.EMPTY

        # 3 corners rule
        used = sum(_is_used(corner) for corner in corners)
        if used < 3:
            return False

        if self._last_move == self.MOVE_TST_KICK:
            # TST and fins are T-spins event without the 2 corners rule
            return True

        # 2 front corners rule
        if self._rotation == 0 and _is_used(corners[0]) and _is_used(corners[1]):
            return True
        if self._rotation == 1 and _is_used(corners[1]) and _is_used(corners[3]):
            return True
        if self._rotation == 2 and _is_used(corners[2]) and _is_used(corners[3]):
            return True
        if self._rotation == 3 and _is_used(corners[0]) and _is_used(corners[2]):
            return True

        return False

    def is_tspin_mini(self) -> bool:
        """
        test if we have a tspin mini

        need a T piece that was kicked
        3 of its 4 corners need to be filled
        is not a T-spin (not tested, so this will return True also for T-spins)
        """
        if self._current_piece != T_PIECE or self._last_move != self.MOVE_KICK:
            return False
        center = self._cells[1]
        corners = [
            (center[0] - 1, center[1] - 1),
            (center[0] - 1, center[1] + 1),
            (center[0] + 1, center[1] - 1),
            (center[0] + 1, center[1] + 1)
        ]

        def _is_used(cell_pos):
            cell = self.grid.get_cell(cell_pos)
            return cell is None or cell.cell_type != Cell.EMPTY

        # 3 corners rule
        return sum(_is_used(corner) for corner in corners) >= 3

    def _translate(self):
        top = 0
        left = 0
        if self._key_manager.pressing[Key.SD_KEY]:
            top += 1
        if self._key_manager.pressing[Key.LEFT_KEY]:
            left -= 1
        if self._key_manager.pressing[Key.RIGHT_KEY]:
            left += 1

        if left != 0:
            if left * self._last_dir < 0:
                self._das_load = 1
                self._arr_load = 0
            elif self._das_load == 0:
                self._das_load += 1
            elif self._das_load < self.das:
                self._das_load += 1
                left = 0
        else:
            self._das_load = 0
            self._arr_load = 0
        # need to be done before arr calculation
        self._last_dir = left

        if self._das_load >= self.das:
            if self.arr == 0:
                left = left * 10
            elif self.arr < 1:
                left = int(left / self.arr)
            else:
                self._arr_load += 1
                if self._arr_load < int(self.arr):
                    left = 0
                else:
                    self._arr_load = 0

        if top > 0:
            if self.sd == 0:
                top = top * 30
            elif self.sd < 1:
                top = int(top / self.sd)
            else:
                self._sd_load += 1
                if self._sd_load < int(self.sd):
                    top = 0
                else:
                    self._sd_load = 0
        else:
            self._sd_load = 0
        new_cells = self.grid.move(left, top, self._cells)
        if new_cells != self._cells:
            self._cells = new_cells
            self._last_move = self.MOVE_TRANS

    def update(self, time_delta):
        """
            Update piece position following user input
        """
        self._time += time_delta

        if self.locked:
            return

        if self._key_manager.pressed[Key.HOLD_KEY] and not self._holt:
            if self._hold_piece is None:
                self._hold_piece = self._current_piece
                self.set_next_from_queue()
            else:
                self._hold_piece, self._current_piece = self._current_piece, self._hold_piece
            for cell_pos in self._cells:
                self.grid.get_cell(cell_pos).cell_type = Cell.EMPTY
            self._holt = True
            self.spawn_piece()
            return

        if self._key_manager.pressed[Key.HD_KEY]:
            self._cells = self.grid.move(0, self.grid.HEIGHT, self._cells)
            self.locked = True
            return

        new_rot_keys_pressed = []
        for rot_key in (Key.ROT_CW_KEY, Key.ROT_CCW_KEY, Key.ROT_180_KEY):
            if self._key_manager.pressed[rot_key]:
                new_rot_keys_pressed.append(rot_key)

        if len(new_rot_keys_pressed) == 1:
            if self._key_manager.pressed[Key.ROT_CW_KEY]:
                self._rotate(1)
            elif self._key_manager.pressed[Key.ROT_CCW_KEY]:
                self._rotate(-1)
            elif self._key_manager.pressed[Key.ROT_180_KEY]:
                self._rotate(2)

        self._translate()

        new_height = self._get_max_height(*self._cells)
        if new_height > self._max_height:
            self._max_height = new_height
            self._wiggles_left = self.ALLOWED_WIGGLES
            self._locking_tick_unmoving_lock = self.UNMOVING_TICKS_LOCK
            self._locking_tick_moving_lock = self.MOVING_TICKS_LOCK
        elif new_height < self._current_height:
            self._wiggles_left -= 1
        elif self._is_on_top_of_something() and self._wiggles_left == 0:
            self.locked = True

        self._current_height = new_height

    def clear_lines(self):
        """
            Actions to do after a piece was locked
        """
        self.piece_nb += 1
        tspin = self.is_tspin()
        mini = False if tspin else self.is_tspin_mini()
        cleared_lines = self.grid.clear_lines()
        perfect = self.grid.is_board_empty()
        self._lines_cleared += cleared_lines

        if cleared_lines > 0:
            self._combo += 1
        else:
            self._combo = -1
        if cleared_lines == 4 or (cleared_lines > 0 and (tspin or mini)):
            self._back_to_back += 1
        elif cleared_lines > 0:
            self._back_to_back = -1
        clear_type = (
            f"{'T-spin ' if tspin else ''}"
            f"{'T-spin mini ' if mini else ''}"
            f"{['', 'Single', 'Double', 'Triple', 'Quad'][cleared_lines]}")

        if clear_type:
            self.other_stats[clear_type.strip()] += 1
            self.other_stats["Max Back-to-Back"] = max(self.other_stats["Max Back-to-Back"], self._back_to_back)
            self.other_stats["Max combo"] = max(self.other_stats["Max combo"], self._combo)
        if perfect:
            self.other_stats["Perfect Clears"] += 1

        back_to_back = f" {'Back-to-back ' + str(self._back_to_back) if self._back_to_back > 0 else ''}"
        text = clear_type + back_to_back

        combo = f"{str(self._combo) + ' REN' if self._combo > 0 else ''}"
        text = text.strip()
        self._damage_textbox.set_text(text)
        self._combo_textbox.set_text(combo)
        self._perfect_clear_textbox.set_text("PERFECT CLEAR" if perfect else "")

    def go_down(self):
        """
            GODOWN with gravity
        """
        self._cells = self.grid.move(0, 1, self._cells)
        new_height = self._get_max_height(*self._cells)
        if new_height != self._current_height:
            if new_height > self._max_height:
                self._max_height = new_height
                self._wiggles_left = self.ALLOWED_WIGGLES
            self._current_height = new_height
            self._last_move = self.MOVE_TRANS
            self._locking_tick_unmoving_lock = self.UNMOVING_TICKS_LOCK
            self._locking_tick_moving_lock = self.MOVING_TICKS_LOCK

    def lock_tick(self):
        """
            lock tick event
        """
        if self._is_on_top_of_something():
            if self._last_dir == 0:
                self._locking_tick_unmoving_lock -= 1
            else:
                self._locking_tick_moving_lock -= 1
            if self._locking_tick_unmoving_lock <= 0 or self._locking_tick_moving_lock <= 0:
                self.locked = True

    def _draw_mini_piece(self, surface, cell_type: int, piece: int, pos_left: int, pos_top: int):
        to_draw = Cell(cell_type)
        bonus_shift = 0
        if piece in (I_PIECE, O_PIECE):
            bonus_shift = 5
        for cell_pos in self._get_spawn_cells(piece):
            rect = pygame.Rect(pos_left + cell_pos[1] * 14 - bonus_shift,
                               pos_top + cell_pos[0] * 14,
                               15, 15)
            to_draw.draw(surface, rect)

    def _get_stats_text(self) -> str:
        if self._game_mode == FREE_PLAY_MODE:
            return (
                f"<br><br>"
                f"<br><b>Lines</b>"
                f"<br>{self._lines_cleared}"
                f"<br><b>Time</b>"
                f"<br>{self.get_time()}"
            )
        elif self._game_mode == SPRINT_MODE:
            pps = 0
            if self._time > 0:
                pps = 1000 * self.piece_nb / self._time
            return (
                f"<b>PPS</b>"
                f"<br>{pps:.2f}"
                f"<br><b>Lines</b>"
                f"<br>{self._lines_cleared:0>2}/40"
                f"<br><b>Time</b>"
                f"<br>{self.time}"
           )
        elif self._game_mode == ULTRA_MODE:
            pps = 0
            if self._time > 0:
                pps = 1000 * self.piece_nb / self._time
            return (
                f"<b>PPS</b>"
                f"<br>{pps:.2f}"
                f"<br><b>Lines</b>"
                f"<br>{self._lines_cleared}"
                f"<br><b>Time Left</b>"
                f"<br>{self.time}"
            )
        return ""

    def _get_score_text(self) -> str:
        if self._game_mode == ULTRA_MODE:
            return (
                f"<b>Score</b>"
                f"<br>{self.score}"
            )
        return ""

    def draw(self, surface):
        """
            Draw the grid and its cells
        """
        self._stats_textbox.set_text(self._get_stats_text())
        self._score_textbox.set_text(self._get_score_text())

        # GRID
        self.grid.draw(surface)

        # HOLD
        rect = pygame.Rect(self.grid.margin_left - 85, self.grid.margin_top, 73, 73)
        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, (60, 60, 60), rect, 2)
        if self._hold_piece is not None:
            self._draw_mini_piece(surface,
                                  Cell.GARBAGE if self._holt else self.CELL[self._hold_piece],
                                  self._hold_piece,
                                  self.grid.margin_left - 112,
                                  self.grid.margin_top + 20)

        # PREVIEW
        preview_left = self.grid.margin_left + self.grid.WIDTH * self.grid.block_size + 12
        preview_top = self.grid.margin_top
        rect = pygame.Rect(preview_left, preview_top, 73, 250)
        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, (60, 60, 60), rect, 2)
        number = 0
        for piece in self._get_preview():
            number += 1
            self._draw_mini_piece(surface,
                                  self.CELL[piece],
                                  piece,
                                  preview_left - 28,
                                  self.grid.margin_top - 24 + number * 45)

        # phantom
        phantom = self.grid.get_hd_pos(self._cells)
        if not set(phantom).intersection(self._cells):
            phantom_cell = Cell(Cell.PHANTOM)
            for cell_pos in phantom:
                rect = pygame.Rect(self.grid.margin_left + cell_pos[1] * self.grid.block_size,
                                   self.grid.margin_top + cell_pos[0] * self.grid.block_size,
                                   self.grid.block_size + 1, self.grid.block_size + 1)
                phantom_cell.draw(surface, rect)
