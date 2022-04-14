"""
Main file
"""
import sys

import pygame
from pygame.locals import *

from pytris.grid import Grid
from pytris.tetromino import Tetromino

GRAVITY_TICK_EVENT = USEREVENT + 1


if __name__ == "__main__":
    pygame.init()

    DISPLAYSURF = pygame.display.set_mode((500, 500))
    FPS = pygame.time.Clock()
    DISPLAYSURF.fill((0, 0, 0))
    pygame.display.set_caption("Pytris")
    pygame.time.set_timer(GRAVITY_TICK_EVENT, 1000)

    g = Grid()
    t = Tetromino(g, Tetromino.I_PIECE)
    t.spawn_piece()

    while True:
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == GRAVITY_TICK_EVENT:
                t.go_down()
            if event.type == QUIT:
                pygame.quit()
                sys.exit()

        if t.locked:
            t.spawn_piece()

        t.update()

        DISPLAYSURF.fill((150, 150, 150))
        g.draw(DISPLAYSURF)

        FPS.tick(60)
