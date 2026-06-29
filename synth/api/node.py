"""SceneNode — runtime object that scripts interact with."""
from __future__ import annotations
from .math3d import Vec3


class SceneNode:
    def __init__(self, obj_data: dict, engine):
        self._data    = obj_data
        self._engine  = engine
        self._alive   = True

        pos = obj_data.get("position", [0, 0, 0])
        rot = obj_data.get("rotation", [0, 0, 0])
        scl = obj_data.get("scale",    [1, 1, 1])

        self.position = Vec3(*pos)
        self.rotation = Vec3(*rot)   # euler degrees
        self.scale    = Vec3(*scl)
        self.id       = obj_data.get("id", "")
        self.type     = obj_data.get("type", "static")
        self.props    = dict(obj_data.get("props", {}))

    # ── public API for scripts ──────────────────────────────────────────────

    def destroy(self):
        """Remove this object from the scene."""
        self._alive = False
        self._engine.renderer.remove_mesh(self.id)

    def play_sound(self, path: str, loop: bool = False):
        self._engine.audio.play_sfx(path, loop=loop)

    def find(self, node_id: str) -> SceneNode | None:
        return self._engine.scripting.nodes.get(node_id)

    def find_type(self, node_type: str) -> SceneNode | None:
        for node in self._engine.scripting.nodes.values():
            if node.type == node_type:
                return node
        return None

    @property
    def scene(self):
        return self._engine.current_scene

    @property
    def is_alive(self) -> bool:
        return self._alive
