"""Keyboard and mouse state tracker."""
import pygame


class InputHandler:
    def __init__(self):
        self._keys_down  = set()
        self._mouse_down = set()

    def on_keydown(self, key): self._keys_down.add(key)
    def on_keyup(self, key):   self._keys_down.discard(key)
    def on_mousedown(self, b): self._mouse_down.add(b)
    def on_mouseup(self, b):   self._mouse_down.discard(b)

    def key(self, key) -> bool:       return key in self._keys_down
    def mouse(self, btn) -> bool:     return btn in self._mouse_down
    def pressed(self) -> set:         return set(self._keys_down)
    def mouse_pressed(self) -> set:   return set(self._mouse_down)
