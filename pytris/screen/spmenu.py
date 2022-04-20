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
from pytris.soundmanager import SoundManager


class SPMenuScreen:
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
        self.free_play_button = None
        self.sprint_button = None
        self.ultra_button = None
        self.pc_button = None
        self.pc_training_button = None
        self.back_button = None
        self.game_mode = -1
        self.key_manager = key_manager
        self.settings = settings
        self.sound = sound

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
        self.pc_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 60, 5 * (self.size[1] // 10), 100, 50),
            "PC MODE",
            self.gui_manager
        )
        self.pc_training_button = pygame_gui.elements.UIButton(
            pygame.Rect(self.size[0] // 2 - 60, 6 * (self.size[1] // 10), 100, 50),
            "PC TRAINING",
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
                    elif event.ui_element == self.pc_button:
                        display_menu = False
                        self.game_mode = PC_MODE
                    elif event.ui_element == self.pc_training_button:
                        display_menu = False
                        self.game_mode = PC_TRAINING
                    elif event.ui_element == self.back_button:
                        display_menu = False
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
        self.pc_button.hide()
        self.pc_training_button.hide()
        self.back_button.hide()
