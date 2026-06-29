"""FPS physics: gravity, ground snap, AABB wall collision, jumping."""
import numpy as np
from .api.math3d import Vec3


GRAVITY      = 18.0   # units/s²
JUMP_SPEED   = 7.0
PLAYER_H     = 1.8    # eye height above ground
PLAYER_R     = 0.4    # capsule radius for wall push


class Physics:
    def __init__(self):
        self._vy       = 0.0   # vertical velocity
        self._grounded = False
        self._floors:  list[dict] = []
        self._walls:   list[dict] = []

    def load_scene(self, scene: dict):
        self._vy = 0.0
        self._grounded = False
        self._floors = []
        self._walls  = []
        for obj in scene.get("objects", []):
            t = obj.get("type", "static")
            if t in ("floor", "static", "prop"):
                # Treat everything solid as potential floor/wall
                self._walls.append(obj)
                if obj.get("type") == "floor":
                    self._floors.append(obj)

    def clear(self):
        self._floors.clear()
        self._walls.clear()
        self._vy = 0.0

    def jump(self, camera):
        if self._grounded:
            self._vy = JUMP_SPEED
            self._grounded = False

    def update(self, camera, delta: float):
        pos = camera.position  # numpy array [x, y, z]

        # Apply gravity
        if not self._grounded:
            self._vy -= GRAVITY * delta
        pos[1] += self._vy * delta

        # Ground snap — find floor height under player
        floor_y = self._floor_height_at(pos[0], pos[2])
        if pos[1] <= floor_y + PLAYER_H:
            pos[1] = floor_y + PLAYER_H
            self._vy = 0.0
            self._grounded = True
        else:
            self._grounded = False

        # Simple AABB wall push
        self._push_walls(pos)
        camera.position = pos

    # ── helpers ────────────────────────────────────────────────────────────

    def _floor_height_at(self, x: float, z: float) -> float:
        """Return the highest floor Y below the player XZ, default 0."""
        best = 0.0
        for obj in self._floors:
            p = obj.get("position", [0, 0, 0])
            s = obj.get("scale", [1, 1, 1])
            # Flat floor AABB XZ check
            hw, hd = s[0] * 0.5, s[2] * 0.5
            if p[0]-hw <= x <= p[0]+hw and p[2]-hd <= z <= p[2]+hd:
                top = p[1] + s[1] * 0.5
                if top > best:
                    best = top
        return best

    def _push_walls(self, pos: np.ndarray):
        """Slide player outside any intersecting wall AABB."""
        for obj in self._walls:
            if obj.get("type") == "floor":
                continue
            p = obj.get("position", [0, 0, 0])
            s = obj.get("scale", [1, 1, 1])
            min_x, max_x = p[0]-s[0]*0.5, p[0]+s[0]*0.5
            min_y, max_y = p[1]-s[1]*0.5, p[1]+s[1]*0.5
            min_z, max_z = p[2]-s[2]*0.5, p[2]+s[2]*0.5

            # Only push if overlapping in Y
            if not (min_y < pos[1] < max_y + PLAYER_H):
                continue

            dx = min(abs(pos[0]-min_x), abs(pos[0]-max_x))
            dz = min(abs(pos[2]-min_z), abs(pos[2]-max_z))

            if abs(pos[0] - p[0]) < s[0]*0.5 + PLAYER_R and \
               abs(pos[2] - p[2]) < s[2]*0.5 + PLAYER_R:
                if dx < dz:
                    pos[0] = min_x - PLAYER_R if pos[0] < p[0] else max_x + PLAYER_R
                else:
                    pos[2] = min_z - PLAYER_R if pos[2] < p[2] else max_z + PLAYER_R
