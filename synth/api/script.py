"""Base class every game script extends."""
from __future__ import annotations
from .node import SceneNode


class Script:
    """
    Extend this in your game scripts. Override lifecycle methods as needed.

    Example (scripts/enemy.py):
        from synth.api import Script, Vec3

        class Enemy(Script):
            health: float = 100.0
            speed:  float = 3.0

            def on_ready(self):
                self.node.play_sound("assets/sounds/growl.wav", loop=True)

            def on_update(self, delta):
                player = self.node.find_type("player")
                if player:
                    direction = (player.position - self.node.position).normalized()
                    self.node.position += direction * self.speed * delta

            def on_hit(self, damage, source=None):
                self.health -= damage
                if self.health <= 0:
                    self.node.destroy()
    """

    node: SceneNode = None   # injected by ScriptRunner

    def on_ready(self):
        """Called once when the scene loads."""

    def on_update(self, delta: float):
        """Called every frame. delta = seconds elapsed."""

    def on_hit(self, damage: float, source=None):
        """Called when a weapon hits this object."""

    def on_trigger_enter(self, other: SceneNode):
        """Called when another node enters this trigger volume."""

    def on_trigger_exit(self, other: SceneNode):
        """Called when another node exits this trigger volume."""
