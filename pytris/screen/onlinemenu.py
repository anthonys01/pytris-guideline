"""
    menu screen
"""
import sys

import pygame
import pygame_gui
from pygame.locals import *

from pytris.gamemode import *
from pytris.keymanager import KeyManager
from pytris.playersettings import PlayerSettings
from pytris.screen.options import OptionsWindow
from pytris.session import GameSession
from pytris.soundmanager import SoundManager


class OnlineMenuScreen:
    """
        Main menu screen
    """
    def __init__(self, size, window, display_surface, clock, gui_manager,
                 key_manager: KeyManager, settings: PlayerSettings, sound: SoundManager):
        self.size = size
        self.gui_manager = gui_manager
        self.display_surface = display_surface
        self.clock = clock
        self.win = window
        self.game_mode = -1
        self.new_pc_session_button: pygame_gui.elements.UIButton = None
        self.back_button: pygame_gui.elements.UIButton = None
        self.error_window: pygame_gui.elements.UIWindow = None
        self.prompt_textbox: pygame_gui.elements.UITextEntryLine = None
        self.join_pc_session_button: pygame_gui.elements.UIButton = None
        self.key_manager = key_manager
        self.settings = settings
        self.sound = sound
        self.session: GameSession = None
        self.session_timeout_event = pygame.event.custom_type()

    def init_ui(self):
        self.session = None
        self.game_mode = -1
        self.new_pc_session_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 110, 2 * (self.size[1] // 10), 200, 50),
            "NEW PC SESSION",
            self.gui_manager
        )
        self.prompt_textbox = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(self.size[0] // 2 - 110, 3 * (self.size[1] // 10), 200, 30),
            self.gui_manager
        )
        self.join_pc_session_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 + 100, 3 * (self.size[1] // 10), 70, 30),
            "JOIN",
            self.gui_manager
        )
        self.back_button = pygame_gui.elements.UIButton(
            pygame.Rect(10, 10, 70, 30),
            "BACK",
            self.gui_manager
        )

    def run(self):
        display_menu = True
        time_delta = 0
        while display_menu:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame_gui.UI_WINDOW_CLOSE:
                    if event.ui_element == self.error_window:
                        display_menu = False
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.new_pc_session_button:
                        self.game_mode = ONLINE_CHILL_PC_MODE
                        self.new_pc_session_button.disable()
                        self.back_button.disable()
                        self.prompt_textbox.disable()
                        self.join_pc_session_button.disable()
                        self.session = GameSession("NEW_ID")
                        pygame.time.set_timer(self.session_timeout_event, 5000, 1)
                    elif event.ui_element == self.join_pc_session_button:
                        self.game_mode = ONLINE_CHILL_PC_MODE
                        session_id = self.prompt_textbox.get_text()
                        self.new_pc_session_button.disable()
                        self.back_button.disable()
                        self.prompt_textbox.disable()
                        self.join_pc_session_button.disable()
                        self.session = GameSession(session_id)
                        pygame.time.set_timer(self.session_timeout_event, 5000, 1)
                    elif event.ui_element == self.back_button:
                        display_menu = False
                elif event.type == self.session_timeout_event:
                    if not self.session.session_ready:
                        self.session.error_msg = "Request timeout"
                elif event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                self.gui_manager.process_events(event)

            if self.session:
                self.session.update()
                if self.session.error_msg and self.error_window is None:
                    self.game_mode = -1
                    self.error_window = pygame_gui.windows.UIMessageWindow(
                        pygame.Rect(self.size[0] // 2 - 140, self.size[1] // 2 - 150, 200, 200),
                        self.session.error_msg,
                        self.gui_manager,
                        window_title="Server Error"
                    )
                elif self.session.session_ready:
                    display_menu = False

            self.gui_manager.update(time_delta / 1000.0)
            self.display_surface.fill((150, 150, 150))
            self.gui_manager.draw_ui(self.display_surface)

            scaled = pygame.transform.smoothscale(self.display_surface, self.win.get_size())
            self.win.blit(scaled, (0, 0))
            time_delta = self.clock.tick(60)

        self.new_pc_session_button.hide()
        self.back_button.hide()
        self.prompt_textbox.hide()
        self.join_pc_session_button.hide()
