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
from pytris.screen.constants import ONLINE_MENU, OFFLINE_MENU
from pytris.screen.options import OptionsWindow
from pytris.soundmanager import SoundManager


class MainMenuScreen:
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
        self.online_button = None
        self.offline_button = None
        self.options_button = None
        self.next_menu = -1
        self.key_manager = key_manager
        self.settings = settings
        self.sound = sound

    def init_ui(self):
        self.online_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 80, 3 * (self.size[1] // 10), 150, 50),
            "ONLINE",
            self.gui_manager
        )
        self.offline_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 80, 4 * (self.size[1] // 10), 150, 50),
            "OFFLINE MODES",
            self.gui_manager
        )
        self.options_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 80, 6 * (self.size[1] // 10), 150, 50),
            "OPTIONS",
            self.gui_manager
        )

    def run(self):
        display_menu = True
        time_delta = 0
        while display_menu:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.online_button:
                        display_menu = False
                        self.next_menu = ONLINE_MENU
                    elif event.ui_element == self.offline_button:
                        display_menu = False
                        self.next_menu = OFFLINE_MENU
                    elif event.ui_element == self.options_button:
                        self.online_button.disable()
                        self.offline_button.disable()
                        self.options_button.disable()

                        options = OptionsWindow(self.size, self.win, self.display_surface,
                                                self.clock, self.gui_manager,
                                                self.key_manager, self.settings, self.sound)
                        options.init_ui()
                        options.run()
                        self.online_button.enable()
                        self.offline_button.enable()
                        self.options_button.enable()
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                self.gui_manager.process_events(event)
            self.gui_manager.update(time_delta / 1000.0)
            self.display_surface.fill((150, 150, 150))
            self.gui_manager.draw_ui(self.display_surface)

            scaled = pygame.transform.smoothscale(self.display_surface, self.win.get_size())
            self.win.blit(scaled, (0, 0))
            time_delta = self.clock.tick(60)

        self.online_button.hide()
        self.offline_button.hide()
        self.options_button.hide()
