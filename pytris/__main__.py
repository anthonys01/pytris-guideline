"""
Main file
"""
import sys

import pygame
from pygame.locals import *

from pytris.grid import Grid
from pytris.tetromino import Tetromino

GRAVITY_TICK_EVENT = USEREVENT + 1


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

    begin_size = (500, 600)
    win = pygame.display.set_mode(begin_size, RESIZABLE)
    display_surface = pygame.Surface(begin_size)
    FPS = pygame.time.Clock()
    display_surface.fill((0, 0, 0))
    pygame.display.set_caption("Pytris")
    pygame.time.set_timer(GRAVITY_TICK_EVENT, 1000)

    g = Grid()
    t = Tetromino(g)
    t.set_next_from_queue()
    t.spawn_piece()
    combo = 0
    back_2_back = 0
    text = ''

    while True:
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == GRAVITY_TICK_EVENT:
                t.go_down()
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        if t.locked:
            tspin = t.is_tspin()
            mini = False if tspin else t.is_tspin_mini()
            cleared = g.clear_lines()
            perfect = g.is_board_empty()
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
                if tspin or cleared == 4:
                    back_2_back += 1
                combo += 1
            else:
                if tspin:
                    text = "T-spin"
                combo = 0
            t.set_next_from_queue()
            if not t.spawn_piece():
                text = "END"

        t.update()

        display_surface.fill((150, 150, 150))
        g.draw(display_surface)
        t.draw(display_surface)
        render_text(display_surface, text, begin_size[0] // 2, 30)

        scaled = pygame.transform.smoothscale(display_surface, win.get_size())
        win.blit(scaled, (0, 0))

        FPS.tick(60)
