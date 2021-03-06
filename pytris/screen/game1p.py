"""
    Single-player game screen
"""
import sys

import pygame
from pygame.locals import *

from pytris.keymanager import Key, KeyManager
from pytris.player import Player
from pytris.playersettings import PlayerSettings
from pytris.screen.gameresult1p import SinglePlayerResultWindow
from pytris.session import GameSession
from pytris.soundmanager import SoundManager


class SinglePlayerGameScreen:
    """
        Main single player game screen
    """
    def __init__(self, size, window, display_surface, clock, gui_manager,
                 keyboard_manager: KeyManager, settings: PlayerSettings, sound: SoundManager, game_mode: int,
                 session: GameSession = None):
        self.size = size
        self.gui_manager = gui_manager
        self.display_surface = display_surface
        self.clock = clock
        self.win = window
        self.game_mode = game_mode
        self.km = keyboard_manager
        self.settings = settings
        self.sound = sound
        self.gravity_tick_event = pygame.event.custom_type()
        self.lock_tick_event = pygame.event.custom_type()
        self.session = GameSession() if session is None else session
        self.player = Player(self.gui_manager, self.km, self.settings, self.sound, self.session, self.game_mode)
        self._result_window = SinglePlayerResultWindow(size, window, display_surface, clock, gui_manager, self.player)
        self._loop = True

    def init_ui(self):
        self._result_window.init_ui()

    def _run(self):
        pygame.time.set_timer(self.gravity_tick_event, 1000)
        pygame.time.set_timer(self.lock_tick_event, 500)
        self.player.reset()
        self.player.start()
        go_down = False
        lock_tick = False
        reset = False
        time_delta = 0

        display_game = True
        display_result = True
        while display_game:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == self.gravity_tick_event:
                    go_down = True
                if event.type == self.lock_tick_event:
                    lock_tick = True
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                self.gui_manager.process_events(event)

            self.session.update()

            # need to update keyboard manager before updating player
            self.km.update()
            if self.km.pressed[Key.EXIT_KEY]:
                display_game = False
                self._loop = False
                self.session.exit_session()
                continue
            if not reset and self.km.pressed[Key.RESET_KEY] and self.session.session_id is None:
                # reset the game (only local games)
                self.player.reset()
                self.player.start()
                go_down = False
                reset = True
            elif not self.km.pressed[Key.RESET_KEY]:
                reset = False

            if not self.player.game_finished():
                if self.player.locked:
                    self.player.clear_lines()
                    self.session.set_next_in_queue()
                    self.player.spawn_piece()
                else:
                    if go_down:
                        self.player.go_down()
                        go_down = False
                    if lock_tick:
                        self.player.lock_tick()
                        lock_tick = False

                self.player.update(time_delta)
                self.gui_manager.update(time_delta / 1000.0)

                self.display_surface.fill((150, 150, 150))
                self.player.draw(self.display_surface)
                self.gui_manager.draw_ui(self.display_surface)
                scaled = pygame.transform.smoothscale(self.display_surface, self.win.get_size())
                self.win.blit(scaled, (0, 0))
            elif display_result and not self.player.topped_out:
                self._result_window.run()
                display_result = False
                if self._result_window.back_to_menu:
                    self._loop = False
                    display_game = False
                elif self._result_window.retry:
                    display_game = False
            else:
                scaled = pygame.transform.smoothscale(self.display_surface, self.win.get_size())
                self.win.blit(scaled, (0, 0))

            time_delta = self.clock.tick(60)

    def run(self):
        while self._loop:
            self._run()

