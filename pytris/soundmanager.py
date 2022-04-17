"""
    Manages game sound
"""
import pygame.mixer


class SoundManager:
    """
        Class to manage game sound
    """

    def __init__(self):
        pygame.mixer.init()
        self.sound = [
            pygame.mixer.Sound("data/sound/arr.ogg"),
            pygame.mixer.Sound("data/sound/clear.ogg"),
            pygame.mixer.Sound("data/sound/das.ogg"),
            pygame.mixer.Sound("data/sound/hit.ogg"),
            pygame.mixer.Sound("data/sound/hold.ogg"),
            pygame.mixer.Sound("data/sound/lock.ogg"),
            pygame.mixer.Sound("data/sound/pc.ogg"),
            pygame.mixer.Sound("data/sound/quad.ogg"),
            pygame.mixer.Sound("data/sound/rotate.ogg"),
            pygame.mixer.Sound("data/sound/softdrop.ogg"),
            pygame.mixer.Sound("data/sound/tspin.ogg")
        ]
        self._volume = 0.6

    @property
    def volume(self):
        return self._volume

    @volume.setter
    def volume(self, new_volume: float):
        if 0 <= new_volume <= 1:
            self._volume = new_volume

    def _play(self, sound_index: int):
        ch = pygame.mixer.find_channel()
        if ch:
            ch.set_volume(self._volume)
            ch.play(self.sound[sound_index])

    def play_arr(self):
        self._play(0)

    def play_clear(self):
        self._play(1)

    def play_das(self):
        self._play(2)

    def play_hit(self):
        self._play(3)

    def play_hold(self):
        self._play(4)

    def play_lock(self):
        self._play(5)

    def play_pc(self):
        self._play(6)

    def play_quad(self):
        self._play(7)

    def play_rotate(self):
        self._play(8)

    def play_softdrop(self):
        self._play(9)

    def play_tspin(self):
        self._play(10)
