"""
Main file
"""
import sys

import pygame
import pygame_gui
from pygame.locals import *

from pytris.gamemode import *
from pytris.keymanager import KeyManager, Key
from pytris.player import Player

GRAVITY_TICK_EVENT = pygame.event.custom_type()
LOCK_TICK_EVENT = pygame.event.custom_type()


if __name__ == "__main__":
    pygame.init()

    begin_size = (500, 720)
    win = pygame.display.set_mode(begin_size)
    display_surface = pygame.Surface(begin_size)
    clock = pygame.time.Clock()
    display_surface.fill((0, 0, 0))
    pygame.display.set_caption("Pytris")

    gui_manager = pygame_gui.UIManager(begin_size, "data/ui_theme.json")
    time_delta = 0
    game_mode = -1

    km = KeyManager()

    while True:
        free_play_button = pygame_gui.elements.UIButton(
            pygame.Rect(begin_size[0] // 2 - 60, 2 * (begin_size[1] // 10), 100, 50),
            "PRACTICE",
            gui_manager
        )
        sprint_button = pygame_gui.elements.UIButton(
            pygame.Rect(begin_size[0] // 2 - 60, 3 * (begin_size[1] // 10), 100, 50),
            "SPRINT",
            gui_manager
        )
        ultra_button = pygame_gui.elements.UIButton(
            pygame.Rect(begin_size[0] // 2 - 60, 4 * (begin_size[1] // 10), 100, 50),
            "ULTRA",
            gui_manager
        )
        display_menu = True
        while display_menu:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    display_menu = False
                    if event.ui_element == free_play_button:
                        game_mode = FREE_PLAY_MODE
                    elif event.ui_element == sprint_button:
                        game_mode = SPRINT_MODE
                    elif event.ui_element == ultra_button:
                        game_mode = ULTRA_MODE
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                gui_manager.process_events(event)
            gui_manager.update(time_delta / 1000.0)
            display_surface.fill((150, 150, 150))
            gui_manager.draw_ui(display_surface)

            scaled = pygame.transform.smoothscale(display_surface, win.get_size())
            win.blit(scaled, (0, 0))
            time_delta = clock.tick(60)

        free_play_button.hide()
        sprint_button.hide()
        ultra_button.hide()

        pygame.time.set_timer(GRAVITY_TICK_EVENT, 1000)
        pygame.time.set_timer(LOCK_TICK_EVENT, 500)
        p = Player(gui_manager, km, game_mode)
        p.start()
        text = ''
        go_down = False
        lock_tick = False
        reset = False

        while not p.game_finished():
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == GRAVITY_TICK_EVENT:
                    go_down = True
                if event.type == LOCK_TICK_EVENT:
                    lock_tick = True
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                gui_manager.process_events(event)

            # need to update keyboard manager before updating player
            km.update()
            if not reset and km.pressed[Key.RESET_KEY]:
                # reset the game
                p.reset()
                p.start()
                go_down = False
                reset = True
            elif not km.pressed[Key.RESET_KEY]:
                reset = False

            if not p.game_finished():
                if p.locked:
                    p.clear_lines()
                    p.set_next_from_queue()
                    p.spawn_piece()
                else:
                    if go_down:
                        p.go_down()
                        go_down = False
                    if lock_tick:
                        p.lock_tick()
                        lock_tick = False

                p.update(time_delta)
                gui_manager.update(time_delta / 1000.0)

                display_surface.fill((150, 150, 150))
                p.draw(display_surface)
                gui_manager.draw_ui(display_surface)

            scaled = pygame.transform.smoothscale(display_surface, win.get_size())
            win.blit(scaled, (0, 0))

            time_delta = clock.tick(60)

        res_window_size = (450, 500)
        result_window = pygame_gui.elements.UIWindow(
            pygame.Rect(50, 50, res_window_size[0], res_window_size[1]),
            gui_manager,
            "Results"
        )
        menu_rect = pygame.Rect(0, 0, 60, 50)
        menu_rect.bottomright = (-10, -10)
        menu_button = pygame_gui.elements.UIButton(
            menu_rect,
            "MENU",
            gui_manager,
            result_window,
            anchors={
                'left': 'right',
                'right': 'right',
                'top': 'bottom',
                'bottom': 'bottom'
            }
        )
        retry_rect = pygame.Rect(0, 0, 70, 50)
        retry_rect.bottomright = (-90, -10)
        retry_button = pygame_gui.elements.UIButton(
            retry_rect,
            "RETRY",
            gui_manager,
            result_window,
            anchors={
                'left': 'right',
                'right': 'right',
                'top': 'bottom',
                'bottom': 'bottom',
            }
        )
        text1 = f"Time : {p.time}<br><br>Pieces used : {p.piece_nb}"
        stats = list(p.other_stats)
        for stat in stats[:7]:
            text1 += f"<br>{stat} : {p.other_stats[stat]}"
        text2 = f"PPS : {p.pps}<br><br>"
        for stat in stats[7:]:
            text2 += f"<br>{stat} : {p.other_stats[stat]}"

        result_textbox_1 = pygame_gui.elements.UITextBox(
            text1,
            pygame.Rect(10, 10, 200, 350),
            gui_manager,
            container=result_window
        )
        result_textbox_2 = pygame_gui.elements.UITextBox(
            text2,
            pygame.Rect(220, 10, 200, 350),
            gui_manager,
            container=result_window
        )
        display_results = True
        while display_results:
            pygame.display.update()
            for event in pygame.event.get():
                if event.type == pygame_gui.UI_WINDOW_CLOSE:
                    display_results = False
                if event.type == pygame_gui.UI_BUTTON_PRESSED:
                    if event.ui_element == menu_button:
                        display_results = False
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                gui_manager.process_events(event)
            gui_manager.update(time_delta / 1000.0)

            display_surface.fill((150, 150, 150))
            p.draw(display_surface)
            gui_manager.draw_ui(display_surface)
            scaled = pygame.transform.smoothscale(display_surface, win.get_size())
            win.blit(scaled, (0, 0))

            time_delta = clock.tick(60)

        gui_manager.clear_and_reset()
