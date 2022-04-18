"""
Main file
"""
import pygame
import pygame_gui

from pytris.keymanager import KeyManager
from pytris.playersettings import PlayerSettings
from pytris.screen.constants import OFFLINE_MENU, ONLINE_MENU
from pytris.screen.game1p import SinglePlayerGameScreen
from pytris.screen.mainmenu import MainMenuScreen
from pytris.screen.spmenu import SPMenuScreen
from pytris.soundmanager import SoundManager

if __name__ == "__main__":
    pygame.init()

    begin_size = (500, 720)
    win = pygame.display.set_mode(begin_size)
    display_surface = pygame.Surface(begin_size)
    clock = pygame.time.Clock()
    display_surface.fill((0, 0, 0))
    pygame.display.set_caption("Pytris - by Anthonys01")

    gui_manager = pygame_gui.UIManager(begin_size, "data/ui_theme.json")
    time_delta = 0
    game_mode = -1

    km = KeyManager()
    settings = PlayerSettings()
    sound = SoundManager(settings)

    main_menu = MainMenuScreen(begin_size, win, display_surface, clock, gui_manager, km, settings, sound)
    sp_menu = SPMenuScreen(begin_size, win, display_surface, clock, gui_manager, km, settings, sound)

    while True:
        main_menu.init_ui()
        main_menu.run()

        if main_menu.next_menu == OFFLINE_MENU:
            sp_menu.init_ui()
            sp_menu.run()

            if sp_menu.game_mode >= 0:
                game = SinglePlayerGameScreen(begin_size, win, display_surface, clock,
                                              gui_manager, km, settings, sound, sp_menu.game_mode)
                game.init_ui()
                game.run()
        elif main_menu.next_menu == ONLINE_MENU:
            ...

        gui_manager.clear_and_reset()
