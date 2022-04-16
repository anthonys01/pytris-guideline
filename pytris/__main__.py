"""
Main file
"""
import sys

import pygame
import pygame_gui
from pygame.locals import *

from pytris.player import Player

GRAVITY_TICK_EVENT = USEREVENT + 1
LOCK_TICK_EVENT = USEREVENT + 2


def render_text(surface, text: str, x_pos: int, y_pos: int):
    if not text:
        return
    font = pygame.font.Font('freesansbold.ttf', 24)
    text = font.render(text, True, (20, 200, 20))
    text_rect = text.get_rect()
    text_rect.center = (x_pos, y_pos)
    surface.blit(text, text_rect)


if __name__ == "__main__":
    pygame.init()

    begin_size = (500, 720)
    win = pygame.display.set_mode(begin_size)
    display_surface = pygame.Surface(begin_size)
    clock = pygame.time.Clock()
    display_surface.fill((0, 0, 0))
    pygame.display.set_caption("Pytris")
    pygame.time.set_timer(GRAVITY_TICK_EVENT, 1000)
    pygame.time.set_timer(LOCK_TICK_EVENT, 500)

    gui_manager = pygame_gui.UIManager(begin_size)
    time_delta = 0

    p = Player()
    p.set_next_from_queue()
    p.spawn_piece()
    combo = 0
    back_2_back = 0
    text = ''
    end = False
    go_down = False
    lock_tick = False
    reset = False

    while True:
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

        keys = pygame.key.get_pressed()
        if not reset and keys[K_BACKSPACE]:
            # reset the game
            p.reset()
            p.set_next_from_queue()
            p.spawn_piece()
            combo = 0
            back_2_back = 0
            text = ''
            end = False
            go_down = False
            reset = True
        if not keys[K_BACKSPACE]:
            reset = False

        if not end:
            if p.locked:
                tspin = p.is_tspin()
                mini = False if tspin else p.is_tspin_mini()
                cleared = p.grid.clear_lines()
                perfect = p.grid.is_board_empty()
                if cleared:
                    if not tspin and cleared < 4:
                        back_2_back = 0
                    text = (
                        f"{'Perfect Clear ' if perfect else ''}"
                        f"{'T-spin ' if tspin else ''}"
                        f"{'T-spin mini ' if mini else ''}"
                        f"{['Single', 'Double', 'Triple', 'Quad'][cleared - 1]}"
                        f" {'Back-to-back ' + str(back_2_back) if back_2_back else ''}"
                        f" {str(combo) + '-combo' if combo else ''}")
                    print(text)
                    if tspin or cleared == 4 or mini:
                        back_2_back += 1
                    combo += 1
                else:
                    if tspin:
                        text = "T-spin"
                    combo = 0
                p.set_next_from_queue()
                if not p.spawn_piece():
                    text = "END"
                    end = True
            else:
                if go_down:
                    p.go_down()
                    go_down = False
                if lock_tick:
                    p.lock_tick()
                    lock_tick = False

            p.update()
            gui_manager.update(time_delta)

            display_surface.fill((150, 150, 150))
            p.draw(display_surface)
            render_text(display_surface, text, begin_size[0] // 2, 30)
            gui_manager.draw_ui(display_surface)

        scaled = pygame.transform.smoothscale(display_surface, win.get_size())
        win.blit(scaled, (0, 0))

        time_delta = clock.tick(60) / 1000.0
