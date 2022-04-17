"""
    menu screen
"""
import sys

import pygame
import pygame_gui
from pygame.locals import *

from pytris.gamemode import *
from pytris.keymanager import KeyManager
from pytris.screen.options import OptionsWindow


class MenuScreen:
    """
        Main menu screen
    """
    def __init__(self, size, window, display_surface, clock, gui_manager, key_manager: KeyManager):
        self.size = size
        self.gui_manager = gui_manager
        self.display_surface = display_surface
        self.clock = clock
        self.win = window
        self.free_play_button = None
        self.sprint_button = None
        self.ultra_button = None
        self.options_button = None
        self.game_mode = -1
        self.key_manager = key_manager

    def init_ui(self):
        self.free_play_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 60, 2 * (self.size[1] // 10), 100, 50),
            "PRACTICE",
            self.gui_manager
        )
        self.sprint_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 60, 3 * (self.size[1] // 10), 100, 50),
            "SPRINT",
            self.gui_manager
        )
        self.ultra_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 60, 4 * (self.size[1] // 10), 100, 50),
            "ULTRA",
            self.gui_manager
        )
        self.options_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 60, 5 * (self.size[1] // 10), 100, 50),
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
                    if event.ui_element == self.free_play_button:
                        display_menu = False
                        self.game_mode = FREE_PLAY_MODE
                    elif event.ui_element == self.sprint_button:
                        display_menu = False
                        self.game_mode = SPRINT_MODE
                    elif event.ui_element == self.ultra_button:
                        display_menu = False
                        self.game_mode = ULTRA_MODE
                    elif event.ui_element == self.options_button:
                        self.free_play_button.disable()
                        self.sprint_button.disable()
                        self.ultra_button.disable()
                        self.options_button.disable()

                        options = OptionsWindow(self.size, self.win, self.display_surface,
                                                self.clock, self.gui_manager, self.key_manager)
                        options.init_ui()
                        options.run()
                        self.free_play_button.enable()
                        self.sprint_button.enable()
                        self.ultra_button.enable()
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

        self.free_play_button.hide()
        self.sprint_button.hide()
        self.ultra_button.hide()
        self.options_button.hide()
