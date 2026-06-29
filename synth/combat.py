"""Weapon / spell / ability system with raycasting hit detection."""
from __future__ import annotations
import math
from .raycast  import raycast
from .api.math3d import Vec3


class WeaponDef:
    __slots__ = ("name", "damage", "fire_rate", "ammo", "max_ammo",
                 "reload_time", "range", "spread", "type", "sound_fire", "sound_reload")

    def __init__(self, name: str, damage=25.0, fire_rate=2.0, ammo=30, max_ammo=120,
                 reload_time=1.5, range=100.0, spread=0.0,
                 type="hitscan", sound_fire=None, sound_reload=None):
        self.name         = name
        self.damage       = damage
        self.fire_rate    = fire_rate
        self.ammo         = ammo
        self.max_ammo     = max_ammo
        self.reload_time  = reload_time
        self.range        = range
        self.spread       = spread          # radians
        self.type         = type            # hitscan | projectile | melee | spell
        self.sound_fire   = sound_fire
        self.sound_reload = sound_reload


# ── Preset weapons ──────────────────────────────────────────────────────────

PRESETS: dict[str, WeaponDef] = {
    "pistol":   WeaponDef("Pistol",   damage=30,  fire_rate=2.5,  ammo=12,  max_ammo=60,  spread=0.01),
    "rifle":    WeaponDef("Rifle",    damage=40,  fire_rate=8.0,  ammo=30,  max_ammo=120, spread=0.02),
    "shotgun":  WeaponDef("Shotgun",  damage=20,  fire_rate=1.2,  ammo=8,   max_ammo=32,  spread=0.15),  # 8 pellets
    "sniper":   WeaponDef("Sniper",   damage=150, fire_rate=0.6,  ammo=5,   max_ammo=20,  spread=0.0),
    "knife":    WeaponDef("Knife",    damage=60,  fire_rate=1.5,  ammo=999, max_ammo=999, range=2.5, type="melee"),
    "fireball": WeaponDef("Fireball", damage=80,  fire_rate=0.8,  ammo=20,  max_ammo=80,  type="spell"),
    "icebolt":  WeaponDef("Icebolt",  damage=45,  fire_rate=1.5,  ammo=30,  max_ammo=90,  type="spell"),
}


class CombatSystem:
    """
    Manages player weapons, ammo, health, and shooting.
    Instantiated by the Engine; accessible from scripts via engine.combat.
    """

    def __init__(self, engine):
        self._engine      = engine
        self.player_health     = 100.0
        self.player_max_health = 100.0
        self.weapons: list[WeaponDef] = []
        self.weapon_idx   = 0
        self._cooldown    = 0.0
        self._reloading   = 0.0
        self.kills        = 0
        self.score        = 0

    # ── setup ─────────────────────────────────────────────────────────────

    def add_weapon(self, weapon_name: str, ammo_override: int = None):
        if weapon_name in PRESETS:
            import copy
            w = copy.copy(PRESETS[weapon_name])
            if ammo_override is not None:
                w.ammo = ammo_override
            self.weapons.append(w)

    def add_weapon_def(self, weapon: WeaponDef):
        self.weapons.append(weapon)

    def pickup_weapon(self, weapon_name: str, ammo: int = None):
        for w in self.weapons:
            if w.name.lower() == weapon_name.lower():
                w.ammo = min(w.max_ammo, w.ammo + (ammo or w.ammo))
                return
        self.add_weapon(weapon_name, ammo)

    def pickup_ammo(self, amount: int):
        if self.current:
            self.current.ammo = min(self.current.max_ammo, self.current.ammo + amount)

    # ── per-frame ─────────────────────────────────────────────────────────

    def update(self, delta: float):
        self._cooldown = max(0.0, self._cooldown - delta)
        if self._reloading > 0:
            self._reloading -= delta

    def switch_weapon(self, direction: int = 1):
        if len(self.weapons) > 1:
            self.weapon_idx = (self.weapon_idx + direction) % len(self.weapons)
            self._cooldown = 0.3

    def try_shoot(self, pellets: int = None) -> list:
        """
        Attempt to fire. Returns list of (node_id, damage, hit_pos) tuples for each hit.
        Empty list = no hit or can't fire.
        """
        if not self.weapons or self._cooldown > 0 or self._reloading > 0:
            return []
        w = self.current
        if w.ammo <= 0:
            self.reload()
            return []

        w.ammo -= 1
        self._cooldown = 1.0 / max(0.1, w.fire_rate)

        cam     = self._engine.renderer.camera
        origin  = Vec3(*cam.position)
        forward = Vec3(*cam.front)

        if w.sound_fire:
            self._engine.audio.play_sfx(w.sound_fire)

        results = []
        n_shots = pellets or (8 if w.name.lower() == "shotgun" else 1)

        for _ in range(n_shots):
            d = _spread(forward, w.spread)
            hit, dist, node_id, normal = raycast(
                origin, d, self._engine.current_scene, max_dist=w.range
            )
            if hit and node_id:
                dmg = w.damage if n_shots == 1 else w.damage
                hit_pos = Vec3(
                    origin.x + d.x * dist,
                    origin.y + d.y * dist,
                    origin.z + d.z * dist,
                )
                self._engine.scripting.hit(node_id, dmg)
                results.append((node_id, dmg, hit_pos))

        return results

    def reload(self):
        if self.current and self._reloading <= 0:
            self._reloading = self.current.reload_time
            if self.current.sound_reload:
                self._engine.audio.play_sfx(self.current.sound_reload)

    def try_melee(self) -> list:
        if not self.current or self.current.type != "melee" or self._cooldown > 0:
            return []
        self._cooldown = 1.0 / max(0.1, self.current.fire_rate)
        cam    = self._engine.renderer.camera
        origin = Vec3(*cam.position)
        fwd    = Vec3(*cam.front)
        hit, dist, nid, _ = raycast(
            origin, fwd, self._engine.current_scene, max_dist=self.current.range
        )
        if hit and nid:
            self._engine.scripting.hit(nid, self.current.damage)
            return [(nid, self.current.damage, None)]
        return []

    # ── health ────────────────────────────────────────────────────────────

    def take_damage(self, amount: float) -> bool:
        self.player_health = max(0.0, self.player_health - amount)
        return self.player_health <= 0.0

    def heal(self, amount: float):
        self.player_health = min(self.player_max_health, self.player_health + amount)

    def on_enemy_killed(self, bonus_score: int = 100):
        self.kills += 1
        self.score += bonus_score

    # ── properties ────────────────────────────────────────────────────────

    @property
    def current(self) -> WeaponDef | None:
        return self.weapons[self.weapon_idx] if self.weapons else None

    @property
    def is_reloading(self) -> bool:
        return self._reloading > 0

    @property
    def ammo_display(self) -> tuple[int, int]:
        w = self.current
        return (w.ammo, w.max_ammo) if w else (0, 0)


def _spread(direction: Vec3, angle: float) -> Vec3:
    import random, math
    if angle <= 0:
        return direction
    theta = random.uniform(-angle, angle)
    phi   = random.uniform(0, math.pi * 2)
    perp1 = Vec3(-direction.z, 0, direction.x).normalized()
    perp2 = direction.cross(perp1).normalized()
    offset = perp1 * (math.cos(phi) * math.sin(theta)) + \
             perp2 * (math.sin(phi) * math.sin(theta))
    return (direction + offset).normalized()
