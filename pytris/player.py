"""
Player state on the board.

Manage piece, hold, queue...
"""
from multiprocessing.pool import ThreadPool, AsyncResult
from typing import List

import pygame
import pygame_gui.elements.ui_label

from pytris.cell import Cell
from pytris.grid import Grid
from pytris.keymanager import KeyManager, Key
from pytris.pcfinder.pcfinder import Queue, PieceMov, PCFinder
from pytris.pieces import *
from pytris.gamemode import *
from pytris.playersettings import PlayerSettings
from pytris.session import GameSession
from pytris.soundmanager import SoundManager


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

    SCORE_TABLE = {
        "T-spin": 400,
        "T-spin mini": 100,
        "T-spin Single": 800,
        "T-spin Double": 1200,
        "T-spin Triple": 1600,
        "T-spin mini Single": 200,
        "T-spin mini Double": 1200,
        "Single": 100,
        "Double": 300,
        "Triple": 500,
        "Quad": 800,
        "Perfect Clear Single": 800,
        "Perfect Clear Double": 1200,
        "Perfect Clear Triple": 1800,
        "Perfect Clear Quad": 2000,
        "B2B Perfect Clear Quad": 3200,
        "B2B": 1.5,
        "HD": 1,
        "SD": 2,
        "Combo": 50
    }

    MOVE_ROT = "rotation"
    MOVE_KICK = "wall_kick"
    MOVE_TST_KICK = "tst_fin_kick"
    MOVE_TRANS = "translation"

    ALLOWED_WIGGLES = 5
    UNMOVING_TICKS_LOCK = 4
    MOVING_TICKS_LOCK = 8

    def __init__(self, gui_manager: pygame_gui.UIManager,
                 key_manager: KeyManager, settings: PlayerSettings, sound: SoundManager,
                 session: GameSession, game_mode: int, seed: str = None):
        super().__init__()
        self._pool = ThreadPool(processes=1)

        self.player_ui_left = 0
        self.player_ui_top = 70

        self.game_mode = game_mode

        self.session = session

        self._key_manager = key_manager
        self.settings = settings
        self.sound = sound
        self._gui_manager = gui_manager

        # grid with (X,Y) coordinates. X lines going down, Y columns going right
        self.grid = Grid(self.player_ui_left + 95, self.player_ui_top, session)
        # if current piece is not movable by the player
        self.locked = False

        self._topped_out = False

        # das trigger. start using arr once das_load >= das
        self.das: int = settings.das

        # arr == 0 -> immediate
        # 0 < arr < 1 -> each frame move int(1 / arr) cell
        # arr >= 1 move 1 block each int(arr) frame
        self.arr: float = settings.arr
        # used if arr >= 1
        self._arr_load = 0

        # sd == 0 -> immediate
        # 0 < sd < 1 -> each frame move int(1 / sd) cell
        # sd >= 1 move 1 block each int(sd) frame
        self.sd: float = settings.sdf
        # used if sd >= 1
        self._sd_load = 0

        self.replaying = False
        self.replaying_future: AsyncResult = None
        self.replay_solves = []
        self.replay_queue: Queue = []
        self.replay_moves: List[PieceMov] = []
        self.replay_coordinate_shift = (0, 0)
        self.grid_history = []
        self.grid_index = 0
        self.piece_history = []

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
        # DAS load counter. Piece start scrolling after this counter is charged higher than DAS trigger
        self._das_load = 0
        # last move type (rotation, kick, tst kick, translation)
        self._last_move = None
        # if the piece is unmoving at the bottom, we accept multiple locking ticks before locking
        self._locking_tick_unmoving_lock = self.UNMOVING_TICKS_LOCK
        # if the piece is moving at the bottom, we accept multiple locking ticks before locking
        self._locking_tick_moving_lock = self.MOVING_TICKS_LOCK
        # last piece translation direction. 0 unmoving, negative left, positive right
        self._last_dir = 0

        self._damage_textbox = pygame_gui.elements.UITextBox(
            "",
            pygame.Rect(self.player_ui_left, self.player_ui_top + 130, 90, 150), gui_manager)

        self._combo_textbox = pygame_gui.elements.UITextBox(
            "",
            pygame.Rect(self.player_ui_left, self.player_ui_top + 280, 90, 50), gui_manager)

        move = 60 if self.game_mode == ONLINE_CHILL_PC_MODE else 0
        self._stats_textbox = pygame_gui.elements.UITextBox(
            self._get_stats_text(),
            pygame.Rect(self.player_ui_left, self.player_ui_top + 330 - move, 90, 300), gui_manager)

        self._score_textbox = pygame_gui.elements.UITextBox(
            self._get_score_text(),
            pygame.Rect(self.player_ui_left + 360, self.player_ui_top + 400, 90, 90), gui_manager)

        self._session_id_textbox = pygame_gui.elements.UITextBox(
            "" if self.session.session_id is None else f"Session ID: {self.session.session_id}",
            pygame.Rect(self.player_ui_left + 110, self.player_ui_top - 50, 250, 30), gui_manager)

        self._perfect_clear_textbox = pygame_gui.elements.UILabel(
            pygame.Rect(self.player_ui_left + 120, self.player_ui_top + 180, 200, 50),
            "",
            gui_manager,
            object_id="perfect_clear"
        )

        self._searching_pc_textbox = pygame_gui.elements.UILabel(
            pygame.Rect(self.player_ui_left + 120, self.player_ui_top + 180, 210, 50),
            "",
            gui_manager,
            object_id="searching_pc"
        )

    @property
    def topped_out(self):
        return self._topped_out

    @topped_out.setter
    def topped_out(self, topout):
        if not self._topped_out and topout:
            self.session.topped_out()
        self._topped_out = topout

    @property
    def pps(self) -> str:
        pps = 0
        if self.session.timer > 0:
            pps = 1000 * self.session.used_pieces / self.session.timer
        return f"{pps:.2f}"

    @property
    def time(self) -> str:
        if self.game_mode == ULTRA_MODE:
            time_left = 120000 - self.session.timer
            ms = time_left % 1000
            total_secs = max(0, time_left // 1000)
            minutes = total_secs // 60
            secs = total_secs % 60
            return f"{minutes:0>2}:{secs:0>2}.{ms:0>3}"
        else:
            ms = self.session.timer % 1000
            total_secs = self.session.timer // 1000
            minutes = total_secs // 60
            secs = total_secs % 60
            return f"{minutes:0>2}:{secs:0>2}.{ms:0>3}"

    def reset(self):
        self.session.reset()
        self._das_load = 0
        self._arr_load = 0
        self._sd_load = 0
        self._topped_out = False
        self._damage_textbox.set_text("")
        self._combo_textbox.set_text("")
        self._perfect_clear_textbox.set_text("")
        self.grid_history = []
        self.piece_history = []
        self.grid_index = 0

    def start(self):
        self.session.set_next_in_queue(start=True)
        if self.game_mode == PC_TRAINING:
            self.grid_history.append([line[:] for line in self.session.grid])
            self.grid_index += 1
        self.spawn_piece()

    def game_finished(self) -> bool:
        if self.topped_out:
            return True
        if self.game_mode == SPRINT_MODE:
            return self.session.lines_cleared >= 40
        if self.game_mode == ULTRA_MODE:
            return 120000 - self.session.timer <= 0
        return False

    def _get_spawn_cells(self, piece_type: int):
        return [(self.SPAWN_POS[piece_type][0] + piece[0],
                 self.SPAWN_POS[piece_type][1] + piece[1])
                for piece in PIECES_ROT[piece_type][0]]

    def spawn_piece(self) -> bool:
        """
        Try to spawn the tetromino piece in the spawn area. Succeed iif all needed cells are empty
        :return: True if succeeded, False otherwise
        """
        spawn_cells = self._get_spawn_cells(self.session.current_piece)
        for pos in spawn_cells:
            if self.grid.get_cell(pos).cell_type != Cell.EMPTY:
                self.topped_out = True
                return False
        if self.game_mode == PC_MODE and self.session.pieces_since_pc >= 10:
            self.topped_out = True
            return False
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
        if self.session.current_piece == O_PIECE:
            return

        old_base = PIECES_ROT[self.session.current_piece][self._rotation]
        new_rotation = (self._rotation + rotation) % 4
        new_base = PIECES_ROT[self.session.current_piece][new_rotation]
        new_cells = []
        for i in range(4):
            new_cells.append((self._cells[i][0] - old_base[i][0] + new_base[i][0],
                              self._cells[i][1] - old_base[i][1] + new_base[i][1]))
        correct_mode = -1
        kick_table = I_WALL_KICKS if self.session.current_piece == I_PIECE else WALL_KICKS
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

        self._cells = new_cells
        self._rotation = new_rotation
        self.sound.play_rotate()

    def is_tspin(self) -> bool:
        """
        test if we have a tspin

        we need a T-piece that was rotated or kicked
        3 or its 4 corners need to be filled
        and 2 of its front corners need to be filled (except for tst and fin kicks)
        """
        if self.session.current_piece != T_PIECE or self._last_move == self.MOVE_TRANS:
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
        if self.session.current_piece != T_PIECE or self._last_move != self.MOVE_KICK:
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

    def _hit_wall(self, cells) -> int:
        """
            -1 hit left wall, 0 don't hit wall, +1 hit right wall
        """
        for cell in cells:
            if cell[0] == 0:
                return -1
            if cell[0] == self.grid.WIDTH - 1:
                return 1
        return 0

    def _translate(self):
        top = 0
        left = 0
        if self._key_manager.pressing[Key.SD_KEY]:
            top += 1
        if self._key_manager.pressing[Key.LEFT_KEY]:
            left -= 1
        if self._key_manager.pressing[Key.RIGHT_KEY]:
            left += 1

        used_das = False
        used_arr = False

        if left != 0:
            if left * self._last_dir < 0:
                self._das_load = 1
                self._arr_load = 0
            elif self._das_load == 0:
                self._das_load += 1
                used_das = True
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
                used_arr = True
            else:
                self._arr_load += 1
                if self._arr_load < int(self.arr):
                    left = 0
                else:
                    self._arr_load = 0
                    used_arr = True

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
            if used_das:
                self.sound.play_das()
            elif used_arr:
                self.sound.play_arr()
            if self._hit_wall(self._cells) != self._hit_wall(new_cells):
                self.sound.play_hit()
            self._cells = new_cells
            self._last_move = self.MOVE_TRANS

    def _hold(self):
        if self.session.hold_piece is None:
            self.session.hold_piece = self.session.current_piece
            self.session.set_next_in_queue()
        else:
            self.session.hold_piece, self.session.current_piece = \
                self.session.current_piece, self.session.hold_piece
        self.session.holt = True
        self.sound.play_hold()
        self.spawn_piece()

    def update(self, time_delta):
        """
            Update piece position following user input
        """
        if self.replaying:
            if self.replaying_future and self.replaying_future.ready():
                print(f"Solutions : {self.replay_solves}")
                self.replaying_future = None
                if self.replay_solves:
                    self.replay_queue, self.replay_moves = self.replay_solves[0]
                    self._searching_pc_textbox.set_text("")
                else:
                    self.replaying = False
                    self._searching_pc_textbox.set_text("NO PC FOUND")
            return

        self.session.update_time(time_delta)

        if self.game_mode == PC_TRAINING:
            if self._key_manager.pressed[Key.SOLVE_KEY]:
                self.solve_board()
                return
            elif self._key_manager.pressing[Key.CTRL_KEY] and self._key_manager.pressed[Key.Z_KEY]:
                if self.grid_index > 1:
                    self.grid_index -= 1
                    self.session.grid = [line[:] for line in self.grid_history[self.grid_index - 1]]
                    if self.session.holt:
                        self.session.hold_piece, self.session.current_piece = \
                            self.session.current_piece, self.session.hold_piece
                    self.session.queue.append(self.session.current_piece)
                    self.session.hold_piece, self.session.current_piece = self.piece_history[self.grid_index - 1]
                    self.session.piece_count -= 1
                    self.spawn_piece()
                    return
            elif self._key_manager.pressing[Key.CTRL_KEY] and self._key_manager.pressed[Key.Y_KEY]:
                if self.grid_index < len(self.grid_history):
                    self.grid_index += 1
                    self.session.grid = [line[:] for line in self.grid_history[self.grid_index - 1]]
                    self.session.set_next_in_queue()
                    self.session.holt = False
                    if self.grid_index < len(self.grid_history) - 1:
                        self.session.hold_piece, self.session.current_piece = self.piece_history[self.grid_index - 1]
                    self.spawn_piece()
                    return

        if self.locked:
            return

        if self._key_manager.pressed[Key.HOLD_KEY] and not self.session.holt:
            self._hold()
            return

        if self._key_manager.pressed[Key.HD_KEY]:
            self._cells = self.grid.move(0, self.grid.HEIGHT, self._cells)
            height = self._get_max_height(*self._cells)
            self.session.score += self.SCORE_TABLE["HD"] * (height - self._current_height)
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
            self.session.score += self.SCORE_TABLE["SD"] * (new_height - self._current_height)
            self._max_height = new_height
            self._wiggles_left = self.ALLOWED_WIGGLES
            self._locking_tick_unmoving_lock = self.UNMOVING_TICKS_LOCK
            self._locking_tick_moving_lock = self.MOVING_TICKS_LOCK
            if self._is_on_top_of_something():
                self.sound.play_softdrop()
        elif new_height < self._current_height:
            self._wiggles_left -= 1
        elif self._is_on_top_of_something() and self._wiggles_left == 0:
            self.locked = True

        self._current_height = new_height

    def clear_lines(self):
        """
            Actions to do after a piece was locked
        """
        self._searching_pc_textbox.set_text("")
        # write locked piece in grid
        self.grid.set_cell_type(self._cells, self.CELL[self.session.current_piece])
        if self.game_mode == PC_TRAINING:
            if self.grid_index < len(self.grid_history):
                self.grid_history = self.grid_history[:self.grid_index]
                self.piece_history = self.piece_history[:self.grid_index - 1]

            if self.session.holt:
                self.piece_history.append([self.session.current_piece, self.session.hold_piece])
            else:
                self.piece_history.append([self.session.hold_piece, self.session.current_piece])

        self.session.pieces_since_pc += 1
        tspin = self.is_tspin()
        mini = False if tspin else self.is_tspin_mini()
        cleared_lines = self.grid.clear_lines()
        perfect = self.grid.is_board_empty()
        self.session.lines_cleared += cleared_lines

        if cleared_lines > 0:
            self.session.combo += 1
        else:
            self.session.combo = -1
        if cleared_lines == 4 or (cleared_lines > 0 and (tspin or mini)):
            self.session.back_to_back += 1
        elif cleared_lines > 0:
            self.session.back_to_back = -1
        clear_type = (
            f"{'T-spin ' if tspin else ''}"
            f"{'T-spin mini ' if mini else ''}"
            f"{['', 'Single', 'Double', 'Triple', 'Quad'][cleared_lines]}").strip()

        # play sounds
        self.sound.play_lock()
        if perfect:
            self.sound.play_pc()
        else:
            if cleared_lines == 4:
                self.sound.play_quad()
            elif tspin or mini:
                self.sound.play_tspin()
            elif cleared_lines > 0:
                self.sound.play_clear()

        if self.replaying:
            self.replay_coordinate_shift = (self.replay_coordinate_shift[0] + cleared_lines, 0)
            return

        # update stats
        if clear_type:
            self.session.stats[clear_type.strip()] += 1
            self.session.stats["Max Back-to-Back"] = max(self.session.stats["Max Back-to-Back"], self.session.back_to_back)
            self.session.stats["Max combo"] = max(self.session.stats["Max combo"], self.session.combo)

            score_to_add = 0
            combo_add = self.SCORE_TABLE["Combo"] if self.session.combo > 0 else 0
            if perfect:
                score_key = f"{'B2B ' if self.session.back_to_back > 0 else ''}Perfect Clear {clear_type}"
                score_to_add = self.SCORE_TABLE[score_key]
            else:
                b2b_mult = self.SCORE_TABLE["B2B"] if self.session.back_to_back > 0 else 1
                score_to_add = b2b_mult * self.SCORE_TABLE[clear_type]
            self.session.score += int((score_to_add + combo_add) * self.session.level)
            if perfect:
                self.session.stats["Perfect Clears"] += 1
                self.session.pieces_since_pc = 0
                self.session.successive_pc += 1
                self.session.max_successive_pc = max(self.session.max_successive_pc, self.session.successive_pc)
        else:
            if self.session.pieces_since_pc >= 10:
                self.session.successive_pc = 0

        back_to_back = f" {'Back-to-back ' + str(self.session.back_to_back) if self.session.back_to_back > 0 else ''}"
        text = clear_type + back_to_back

        combo = f"{str(self.session.combo) + ' REN' if self.session.combo > 0 else ''}"
        text = text.strip()
        self._damage_textbox.set_text(text)
        self._combo_textbox.set_text(combo)
        self._perfect_clear_textbox.set_text("PERFECT CLEAR" if perfect else "")
        self.session.current_piece = None
        if self.game_mode == PC_TRAINING:
            self.grid_history.append([line[:] for line in self.session.grid])
            self.grid_index += 1
        self.session.send_to_server()

    def solve_board(self):
        self.replaying = True
        queue = []
        if self.session.hold_piece is not None:
            queue.append(self.session.hold_piece)
        if self.session.current_piece is not None:
            queue.append(self.session.current_piece)
        queue += list(reversed(self.session.queue[-11 + len(queue):]))
        converted_grid = []
        for line in self.session.grid[-4:]:
            converted_grid.append([cell != Cell.EMPTY for cell in line])
        print(f"Solving grid for {queue}, {converted_grid}")
        self.replay_coordinate_shift = (18, 0)
        pc_finder = PCFinder()
        self._searching_pc_textbox.set_text("SEARCHING FOR PC...")
        self.replay_solves = []
        self.replaying_future = self._pool.apply_async(pc_finder.solve, (queue, converted_grid, self.replay_solves))

    def next_move_replay(self):
        if self.replaying and self.replaying_future is None:
            if not self.replay_queue:
                self.replaying = False
                return
            piece = self.replay_queue[0]
            moves = self.replay_moves[0]
            if piece == self.session.current_piece:
                if not moves:
                    self.replay_queue = self.replay_queue[1:]
                    self.replay_moves = self.replay_moves[1:]
                    self.clear_lines()
                    self.session.set_next_in_queue()
                    self.spawn_piece()
                else:
                    move = moves[0]
                    self.replay_moves[0] = moves[1:]
                    new_cells = []
                    for cell in move:
                        new_cells.append((cell[0] + self.replay_coordinate_shift[0],
                                          cell[1] + self.replay_coordinate_shift[1]))
                    self._cells = new_cells
            else:
                self._hold()

    def go_down(self):
        """
            GODOWN with gravity
        """
        if self.replaying:
            return
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
        if self.replaying:
            return
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
        if self.game_mode == FREE_PLAY_MODE:
            return (
                f"<br><br>"
                f"<br><b>Lines</b>"
                f"<br>{self.session.lines_cleared}"
                f"<br><b>Time</b>"
                f"<br>{self.time}"
            )
        elif self.game_mode == SPRINT_MODE:
            pps = 0
            if self.session.timer > 0:
                pps = 1000 * self.session.used_pieces / self.session.timer
            return (
                f"<b>PPS</b>"
                f"<br>{pps:.2f}"
                f"<br><b>Lines</b>"
                f"<br>{self.session.lines_cleared:0>2}/40"
                f"<br><b>Time</b>"
                f"<br>{self.time}"
           )
        elif self.game_mode == ULTRA_MODE:
            pps = 0
            if self.session.timer > 0:
                pps = 1000 * self.session.used_pieces / self.session.timer
            return (
                f"<b>PPS</b>"
                f"<br>{pps:.2f}"
                f"<br><b>Lines</b>"
                f"<br>{self.session.lines_cleared}"
                f"<br><b>Time Left</b>"
                f"<br>{self.time}"
            )
        elif self.game_mode == PC_MODE:
            return (
                f"<b>Perfect Clears</b>"
                f"<br>{self.session.stats['Perfect Clears']}"
                f"<br><b>Pieces</b>"
                f"<br>{self.session.used_pieces}"
                f"<br><b>Time</b>"
                f"<br>{self.time}"
            )
        elif self.game_mode == ONLINE_CHILL_PC_MODE:
            return (
                f"<b>PCs</b>"
                f"<br>{self.session.stats['Perfect Clears']}"
                f"<br><b>Succ. PCs</b>"
                f"<br>{self.session.successive_pc}"
                f"<br><b>Max Succ. PCs</b>"
                f"<br>{self.session.max_successive_pc}"
                f"<br><b>Pieces</b>"
                f"<br>{self.session.used_pieces}"
                f"<br><b>Time</b>"
                f"<br>{self.time}"
            )
        elif self.game_mode == PC_TRAINING:
            return (
                f"<b>Perfect Clears</b>"
                f"<br>{self.session.stats['Perfect Clears']}"
                f"<br><b>Pieces</b>"
                f"<br>{self.session.used_pieces}"
            )
        return ""

    def _get_score_text(self) -> str:
        if self.game_mode in (ULTRA_MODE, ONLINE_CHILL_PC_MODE):
            return (
                f"<b>Score</b>"
                f"<br>{self.session.score}"
            )
        return ""

    def draw(self, surface):
        """
            Draw the grid and its cells
        """
        self._stats_textbox.set_text(self._get_stats_text())
        self._score_textbox.set_text(self._get_score_text())

        # GRID
        self.grid.draw(surface, self.topped_out)

        # HOLD
        rect = pygame.Rect(self.grid.margin_left - 85, self.grid.margin_top, 73, 73)
        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, (60, 60, 60), rect, 2)
        if self.session.hold_piece is not None:
            self._draw_mini_piece(surface,
                                  Cell.GARBAGE if self.session.holt else self.CELL[self.session.hold_piece],
                                  self.session.hold_piece,
                                  self.grid.margin_left - 112,
                                  self.grid.margin_top + 20)

        # PREVIEW
        preview_left = self.grid.margin_left + self.grid.WIDTH * self.grid.block_size + 12
        preview_top = self.grid.margin_top
        rect = pygame.Rect(preview_left, preview_top, 73, 250)
        pygame.draw.rect(surface, (20, 20, 20), rect)
        pygame.draw.rect(surface, (60, 60, 60), rect, 2)
        number = 0
        for piece in self.session.get_preview():
            number += 1
            self._draw_mini_piece(surface,
                                  self.CELL[piece],
                                  piece,
                                  preview_left - 28,
                                  self.grid.margin_top - 24 + number * 45)

        # piece
        to_draw = Cell(self.CELL[self.session.current_piece])
        if self.topped_out:
            to_draw = Cell(Cell.GARBAGE)
        for cell_pos in self._cells:
            rect = pygame.Rect(self.grid.margin_left + cell_pos[1] * self.grid.block_size,
                               self.grid.margin_top + cell_pos[0] * self.grid.block_size,
                               self.grid.block_size + 1, self.grid.block_size + 1)
            to_draw.draw(surface, rect)

        # phantom
        phantom = self.grid.get_hd_pos(self._cells)
        if not set(phantom).intersection(self._cells):
            phantom_cell = Cell(Cell.PHANTOM)
            for cell_pos in phantom:
                rect = pygame.Rect(self.grid.margin_left + cell_pos[1] * self.grid.block_size,
                                   self.grid.margin_top + cell_pos[0] * self.grid.block_size,
                                   self.grid.block_size + 1, self.grid.block_size + 1)
                phantom_cell.draw(surface, rect)
