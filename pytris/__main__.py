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
    text = font.render(text, True, (0, 200, 0))
    text_rect = text.get_rect()
    text_rect.center = (x_pos, y_pos)
    surface.blit(text, text_rect)


if __name__ == "__main__":
    pygame.init()

    DISPLAYSURF = pygame.display.set_mode((500, 600))
    FPS = pygame.time.Clock()
    DISPLAYSURF.fill((0, 0, 0))
    pygame.display.set_caption("Pytris")
    pygame.time.set_timer(GRAVITY_TICK_EVENT, 1000)

    g = Grid()
    t = Tetromino(g)
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
            cleared = g.clear_lines()
            if cleared:
                if not tspin and cleared < 4:
                    back_2_back = 0
                text = (
                    f"{'T-spin' if tspin else ''} "
                    f"{['Single', 'Double', 'Triple', 'Quad'][cleared - 1]}"
                    f" {'Back-to-back ' + str(back_2_back) if back_2_back else ''}"
                    f" {str(combo) + 'combo' if combo else ''}")
                print(text)
                if tspin or cleared == 4:
                    back_2_back += 1
                combo += 1
            else:
                combo = 0
            if not t.spawn_piece():
                text = "END"

        t.update()

        DISPLAYSURF.fill((150, 150, 150))
        g.draw(DISPLAYSURF)
        t.draw(DISPLAYSURF)
        render_text(DISPLAYSURF, text, 300, 30)

        FPS.tick(60)
