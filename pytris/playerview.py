"""
    Manage all visual and sound data for player grid
"""
import pygame
import pygame_gui.elements.ui_label

from pytris.cell import Cell
from pytris.grid import Grid
from pytris.pieces import *
from pytris.gamemode import *
from pytris.session import GameSession
from pytris.soundmanager import SoundManager


class PlayerView(pygame.sprite.Sprite):
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

    def __init__(self, gui_manager: pygame_gui.UIManager, sound: SoundManager,
                 session: GameSession, game_mode: int):
        super().__init__()
        self.player_ui_left = 0
        self.player_ui_top = 70

        self.game_mode = game_mode

        self.session = session

        self.sound = sound
        self._gui_manager = gui_manager

        # grid with (X,Y) coordinates. X lines going down, Y columns going right
        self.grid = Grid(self.player_ui_left + 95, self.player_ui_top, session)
        # if current piece is not movable by the player
        self.locked = False

        self._topped_out = False

        # position of the current piece's minos
        self.cells: List[(int, int)] = []

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

        self.searching_pc_textbox = pygame_gui.elements.UILabel(
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
        self._topped_out = False
        self._damage_textbox.set_text("")
        self._combo_textbox.set_text("")
        self._perfect_clear_textbox.set_text("")

    def _get_spawn_cells(self, piece_type: int):
        return [(self.SPAWN_POS[piece_type][0] + piece[0],
                 self.SPAWN_POS[piece_type][1] + piece[1])
                for piece in PIECES_ROT[piece_type][0]]

    def spawn_piece(self, new_cells):
        self.cells = new_cells
        self.locked = False

    def rotate(self, new_cells):
        self.cells = new_cells
        self.sound.play_rotate()

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

    def translate(self, new_cells, used_das: bool, used_arr: bool):
        if new_cells != self.cells:
            if used_das:
                self.sound.play_das()
            elif used_arr:
                self.sound.play_arr()
            if self._hit_wall(self.cells) != self._hit_wall(new_cells):
                self.sound.play_hit()
            self.cells = new_cells

    def hold(self):
        self.sound.play_hold()

    def clear_lines(self, cleared_lines: int, tspin: bool, mini: bool, perfect: bool):
        """
            Actions to do after a piece was locked
        """
        self.searching_pc_textbox.set_text("")

        clear_type = (
            f"{'T-spin ' if tspin else ''}"
            f"{'T-spin mini ' if mini else ''}"
            f"{['', 'Single', 'Double', 'Triple', 'Quad'][cleared_lines]}").strip()
        back_to_back = f" {'Back-to-back ' + str(self.session.back_to_back) if self.session.back_to_back > 0 else ''}"
        text = clear_type + back_to_back
        combo = f"{str(self.session.combo) + ' REN' if self.session.combo > 0 else ''}"

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

        text = text.strip()
        self._damage_textbox.set_text(text)
        self._combo_textbox.set_text(combo)
        self._perfect_clear_textbox.set_text("PERFECT CLEAR" if perfect else "")

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
        for cell_pos in self.cells:
            rect = pygame.Rect(self.grid.margin_left + cell_pos[1] * self.grid.block_size,
                               self.grid.margin_top + cell_pos[0] * self.grid.block_size,
                               self.grid.block_size + 1, self.grid.block_size + 1)
            to_draw.draw(surface, rect)

        # phantom
        phantom = self.grid.get_hd_pos(self.cells)
        if not set(phantom).intersection(self.cells):
            phantom_cell = Cell(Cell.PHANTOM)
            for cell_pos in phantom:
                rect = pygame.Rect(self.grid.margin_left + cell_pos[1] * self.grid.block_size,
                                   self.grid.margin_top + cell_pos[0] * self.grid.block_size,
                                   self.grid.block_size + 1, self.grid.block_size + 1)
                phantom_cell.draw(surface, rect)
