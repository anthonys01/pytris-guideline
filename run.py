"""
Main file
"""
import pygame
import pygame_gui

from pytris.keymanager import KeyManager
from pytris.playersettings import PlayerSettings
from pytris.screen.game1p import SinglePlayerGameScreen
from pytris.screen.menu import MenuScreen


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
    settings = PlayerSettings()

    menu = MenuScreen(begin_size, win, display_surface, clock, gui_manager, km, settings)

    while True:
        menu.init_ui()
        menu.run()

        game = SinglePlayerGameScreen(begin_size, win, display_surface, clock,
                                      gui_manager, km, settings, menu.game_mode)
        game.init_ui()
        game.run()

        gui_manager.clear_and_reset()
