"""
    Single player game result window
"""
import sys

import pygame
import pygame_gui
from pygame.locals import *

from pytris.gamemode import SPRINT_MODE, ULTRA_MODE


class SinglePlayerResultWindow:
    def __init__(self, size, window, display_surface, clock, gui_manager, player):
        self.size = size
        self.gui_manager = gui_manager
        self.display_surface = display_surface
        self.clock = clock
        self.win = window
        self.player = player
        self.result_window: pygame_gui.elements.UIWindow = None
        self.menu_button = None
        self.retry_button = None
        self.result_textbox_1: pygame_gui.elements.UITextBox = None
        self.result_textbox_2: pygame_gui.elements.UITextBox = None
        self.retry = False
        self.back_to_menu = False

    def init_ui(self):
        res_window_size = (450, 500)
        self.result_window = pygame_gui.elements.UIWindow(
            pygame.Rect(50, 50, res_window_size[0], res_window_size[1]),
            self.gui_manager,
            "Results",
            visible=0
        )
        menu_rect = pygame.Rect(0, 0, 60, 50)
        menu_rect.bottomright = (-10, -10)
        self.menu_button = pygame_gui.elements.UIButton(
            menu_rect,
            "MENU",
            self.gui_manager,
            self.result_window,
            anchors={
                'left': 'right',
                'right': 'right',
                'top': 'bottom',
                'bottom': 'bottom'
            }
        )
        retry_rect = pygame.Rect(0, 0, 70, 50)
        retry_rect.bottomright = (-90, -10)
        self.retry_button = pygame_gui.elements.UIButton(
            retry_rect,
            "RETRY",
            self.gui_manager,
            self.result_window,
            anchors={
                'left': 'right',
                'right': 'right',
                'top': 'bottom',
                'bottom': 'bottom',
            }
        )
        self.result_textbox_1 = pygame_gui.elements.UITextBox(
            "",
            pygame.Rect(10, 10, 200, 350),
            self.gui_manager,
            container=self.result_window
        )
        self.result_textbox_2 = pygame_gui.elements.UITextBox(
            "",
            pygame.Rect(220, 10, 200, 350),
            self.gui_manager,
            container=self.result_window
        )

    def init_result_text(self):
        text = ""
        if self.player.game_mode == SPRINT_MODE:
            text = f"Time : {self.player.time}"
        elif self.player.game_mode == ULTRA_MODE:
            text = f"Score : {self.player.score}"

        text1 = f"{text}<br><br>Pieces used : {self.player.piece_nb}"
        stats = list(self.player.other_stats)
        for stat in stats[:7]:
            text1 += f"<br>{stat} : {self.player.other_stats[stat]}"
        text2 = f"PPS : {self.player.pps}<br><br>"
        for stat in stats[7:]:
            text2 += f"<br>{stat} : {self.player.other_stats[stat]}"
        self.result_textbox_1.set_text(text1)
        self.result_textbox_2.set_text(text2)

    def run(self):
        self.init_result_text()
        self.result_window.show()
        time_delta = 0
        display_results = True
        while display_results:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame_gui.UI_WINDOW_CLOSE:
                    display_results = False
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == self.menu_button:
                        display_results = False
                        self.back_to_menu = True
                    elif event.ui_element == self.retry_button:
                        display_results = False
                        self.retry = True
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                self.gui_manager.process_events(event)
            self.gui_manager.update(time_delta / 1000.0)

            self.display_surface.fill((150, 150, 150))
            self.player.draw(self.display_surface)
            self.gui_manager.draw_ui(self.display_surface)
            scaled = pygame.transform.smoothscale(self.display_surface, self.win.get_size())
            self.win.blit(scaled, (0, 0))

            time_delta = self.clock.tick(60)
        self.result_window.hide()
