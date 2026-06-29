"""Audio system — music + SFX via pygame.mixer."""
import pygame
from pathlib import Path


class AudioSystem:
    MAX_CHANNELS = 16

    def __init__(self, game_dir: Path):
        self.game_dir = game_dir
        pygame.mixer.set_num_channels(self.MAX_CHANNELS)
        self._sfx_cache: dict[str, pygame.mixer.Sound] = {}

    def play_music(self, rel_path: str, volume: float = 0.6):
        path = str(self.game_dir / rel_path)
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.set_volume(volume)
            pygame.mixer.music.play(-1)
        except Exception as e:
            print(f"[audio] music load failed: {rel_path} — {e}")

    def stop_music(self):
        pygame.mixer.music.stop()

    def play_sfx(self, rel_path: str, volume: float = 1.0, loop: bool = False) -> pygame.mixer.Channel | None:
        path = str(self.game_dir / rel_path)
        if path not in self._sfx_cache:
            try:
                self._sfx_cache[path] = pygame.mixer.Sound(path)
            except Exception as e:
                print(f"[audio] sfx load failed: {rel_path} — {e}")
                return None
        sound = self._sfx_cache[path]
        sound.set_volume(volume)
        return sound.play(-1 if loop else 0)

    def set_master_volume(self, v: float):
        pygame.mixer.music.set_volume(v)
        for s in self._sfx_cache.values():
            s.set_volume(v)
