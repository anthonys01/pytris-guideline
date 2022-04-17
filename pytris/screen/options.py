"""
    Single player game result window
"""
import sys
from typing import Dict

import pygame
import pygame_gui
from pygame.locals import *

from pytris.keymanager import Key, KeyManager
from pytris.playersettings import PlayerSettings


class OptionsWindow:
    """
        Window to modify different player settings
    """
    def __init__(self, size, window, display_surface, clock, gui_manager,
                 key_manager: KeyManager, settings: PlayerSettings):
        self.size = size
        self.gui_manager = gui_manager
        self.display_surface = display_surface
        self.clock = clock
        self.win = window
        self.options_window: pygame_gui.elements.UIWindow = None
        self.key_manager = key_manager
        self.settings = settings
        self.key_to_button: Dict[Key, pygame_gui.elements.UIButton] = {}
        self.das_slider: pygame_gui.elements.UIHorizontalSlider = None
        self.das_text: pygame_gui.elements.UILabel = None
        self.arr_slider: pygame_gui.elements.UIHorizontalSlider = None
        self.arr_text: pygame_gui.elements.UILabel = None
        self.sdf_slider: pygame_gui.elements.UIHorizontalSlider = None
        self.sdf_text: pygame_gui.elements.UILabel = None
        self._waiting_keypress = None

    def init_ui(self):
        res_window_size = (450, 500)
        self.options_window = pygame_gui.elements.UIWindow(
            pygame.Rect(20, 50, res_window_size[0], res_window_size[1]),
            self.gui_manager,
            "Options",
            visible=0
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(240, 10, 100, 30),
            "DAS",
            self.gui_manager,
            container=self.options_window
        )
        self.das_slider = pygame_gui.elements.UIHorizontalSlider(
            pygame.Rect(220, 40, 150, 20),
            self.settings.das,
            (0, 30),
            manager=self.gui_manager,
            container=self.options_window
        )
        self.das_text = pygame_gui.elements.UILabel(
            pygame.Rect(370, 35, 35, 30),
            str(self.settings.das),
            self.gui_manager,
            container=self.options_window
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(240, 60, 100, 30),
            "ARR",
            self.gui_manager,
            container=self.options_window
        )
        self.arr_slider = pygame_gui.elements.UIHorizontalSlider(
            pygame.Rect(220, 90, 150, 20),
            self.settings.arr,
            (0.0, 4.0),
            click_increment=0.1,
            manager=self.gui_manager,
            container=self.options_window
        )
        self.arr_text = pygame_gui.elements.UILabel(
            pygame.Rect(370, 85, 35, 30),
            str(self.settings.arr),
            self.gui_manager,
            container=self.options_window
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(240, 110, 100, 30),
            "SDF",
            self.gui_manager,
            container=self.options_window
        )
        self.sdf_slider = pygame_gui.elements.UIHorizontalSlider(
            pygame.Rect(220, 140, 150, 20),
            self.settings.sdf,
            (0.0, 4.0),
            click_increment=0.1,
            manager=self.gui_manager,
            container=self.options_window
        )
        self.sdf_text = pygame_gui.elements.UILabel(
            pygame.Rect(370, 135, 35, 30),
            str(self.settings.sdf),
            self.gui_manager,
            container=self.options_window
        )
        i = 0
        for key in Key:
            pygame_gui.elements.UILabel(
                pygame.Rect(10, 10 + 30 * i, 100, 30),
                key,
                self.gui_manager,
                container=self.options_window
            )
            self.key_to_button[Key(key)] = pygame_gui.elements.UIButton(
                pygame.Rect(110, 10 + 30 * i, 100, 30),
                pygame.key.name(self.key_manager.key_for(Key(key))),
                self.gui_manager,
                container=self.options_window
            )
            i += 1

    def run(self):
        self.options_window.show()
        time_delta = 0
        display_options = True
        while display_options:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame_gui.UI_WINDOW_CLOSE:
                    if event.ui_element == self.options_window:
                        display_options = False
                elif event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
                    if event.ui_element == self.das_slider:
                        self.settings.das = self.das_slider.get_current_value()
                        self.das_text.set_text(str(self.settings.das))
                    elif event.ui_element == self.arr_slider:
                        self.settings.arr = int(self.arr_slider.get_current_value() * 10) / 10
                        self.arr_text.set_text(str(self.settings.arr))
                    elif event.ui_element == self.sdf_slider:
                        self.settings.sdf = int(self.sdf_slider.get_current_value() * 10) / 10
                        self.sdf_text.set_text(str(self.settings.sdf))
                elif event.type == pygame_gui.UI_BUTTON_PRESSED:
                    for key, button in self.key_to_button.items():
                        if event.ui_element == button:
                            self.options_window.disable()
                            self._waiting_keypress = key
                            break
                elif event.type == pygame.KEYDOWN:
                    if self._waiting_keypress:
                        self.options_window.enable()
                        new_key = event.key
                        self.key_to_button[self._waiting_keypress].set_text(pygame.key.name(new_key))
                        self.key_to_button[self._waiting_keypress].rebuild()
                        self.key_manager.update_binding(self._waiting_keypress, new_key)
                        self._waiting_keypress = None
                elif event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                self.gui_manager.process_events(event)

            self.gui_manager.update(time_delta / 1000.0)

            self.display_surface.fill((150, 150, 150))
            self.gui_manager.draw_ui(self.display_surface)
            scaled = pygame.transform.smoothscale(self.display_surface, self.win.get_size())
            self.win.blit(scaled, (0, 0))

            time_delta = self.clock.tick(60)
        self.options_window.hide()
