---
name: synthengine
description: >
  AI-first 3D game engine — custom-built, no Godot, no Unity. Scan assets,
  run a 6-agent pipeline, write a complete SynthEngine game (scene JSON +
  Python scripts) for any genre: FPS, racing, RPG, spell/magic, platformer,
  horror. Includes shooting, enemy AI, vehicles, spells, HUD, particles,
  skybox. Run with `python -m synth <game-dir>`. Invoke /synthengine
  [game-dir] [request] or let it ask.
argument-hint: "[game-dir] [game-request]"
license: MIT
---

# SynthEngine

You are running the SynthEngine pipeline. You will scan a folder of game
assets, think through a game design, and write all files that
`python -m synth <output>` needs. You use your own tools — Bash, Read,
Write. The engine renders the game. You design it.

---

## Engine overview

SynthEngine is a custom OpenGL 3D engine. It includes:
- **Renderer**: Blinn-Phong lighting, procedural skybox, fog, texture support
- **Physics**: Capsule gravity, ground snap, AABB wall collision, jumping
- **Combat**: Raycasting hitscan + melee + spell weapons, preset library
- **Enemy AI**: State machine (idle → patrol → chase → attack → dead)
- **Vehicles**: Arcade car physics with drift and handbrake
- **Particles**: CPU emitters (explosion, blood, magic, muzzle flash, smoke)
- **HUD**: Health bar, ammo, mana, minimap, score, crosshair, messages
- **Scripting**: Python scripts per object, lifecycle hooks

---

## Game project format

```
<game-dir>/
├── game.json
├── scenes/
│   └── *.scene.json
└── scripts/
    └── *.py
```

### game.json
```json
{
  "title":       "My Game",
  "start_scene": "scenes/level1.scene.json",
  "weapons":     ["pistol", "rifle"]
}
```

Built-in weapon presets (use by name):
`pistol` `rifle` `shotgun` `sniper` `knife` `fireball` `icebolt`

---

### scene.json — full schema

```json
{
  "name":        "Level1",
  "next_scene":  "scenes/level2.scene.json",
  "spawn":       [0.0, 1.8, 8.0],
  "sky_color":   [0.45, 0.62, 0.82],
  "fog_enabled": true,
  "fog":         { "start": 20, "end": 70, "color": [0.45, 0.62, 0.82] },
  "lighting": {
    "ambient":     [0.28, 0.28, 0.35],
    "directional": { "direction": [0.6,-1.0,0.4], "color": [1.0, 0.92, 0.78] }
  },
  "audio": { "music": "assets/sounds/ambient.ogg" },
  "objects": [ ... ]
}
```

### Object types

| type | behaviour |
|------|-----------|
| `floor`  | static geometry + ground collision surface |
| `static` | solid wall/prop — AABB collision |
| `enemy`  | scriptable AI — attach `"script"` |
| `pickup` | collected when player walks into it |
| `trigger`| invisible volume — fires action on player enter |
| `prop`   | decorative, no collision |
| `vehicle`| driveable — attach vehicle script |

### Object fields
```json
{
  "id":       "unique_id",
  "type":     "static",
  "mesh":     "assets/models/wall.glb",
  "position": [x, y, z],
  "rotation": [rx, ry, rz],
  "scale":    [sx, sy, sz],
  "color":    [r, g, b],
  "script":   "scripts/enemy.py",
  "props":    { "key": value }
}
```

When no `mesh` is given, the engine renders a colored box using `scale`.

### Pickup props
```json
{ "weapon": "rifle", "ammo": 30 }   // give weapon
{ "health": 40 }                     // restore health
{ "ammo": 60 }                       // add ammo
{ "mana": 50 }                       // restore mana
```

### Trigger props
```json
{ "action": "next_scene" }  // go to next_scene
{ "action": "win" }         // end game with WIN
{ "action": "kill" }        // instant death
```

---

## Script API

Every game script lives in `scripts/` and extends `Script`.
Props from the scene JSON are injected as attributes before `on_ready`.

```python
from synth.api import Script, Vec3

class Enemy(Script):
    health: float = 100.0
    speed:  float = 3.0

    def on_ready(self):   ...
    def on_update(self, delta: float): ...
    def on_hit(self, damage: float, source=None): ...
    def on_trigger_enter(self, other): ...
```

### SceneNode methods (self.node)
```python
self.node.position          # Vec3 — read/write
self.node.rotation          # Vec3 euler degrees — read/write
self.node.scale             # Vec3 — read/write
self.node.props             # dict from scene JSON
self.node.find(id)          # SceneNode | None
self.node.find_type(type)   # first node of that type
self.node.play_sound(path, loop=False)
self.node.destroy()
self.node._engine           # the Engine instance (combat, hud, particles, audio)
```

### Engine systems accessible from scripts
```python
engine = self.node._engine
engine.combat.take_damage(amount)      # damage player, returns True if dead
engine.combat.heal(amount)
engine.combat.on_enemy_killed(score)
engine.hud.show_message("text", (r,g,b), duration=3.0)
engine.particles.explosion(pos)
engine.particles.blood(pos)
engine.particles.magic(pos, color)
engine.particles.smoke(pos)
engine.particles.sparks(pos, normal)
engine.audio.play_sfx("assets/sounds/hit.wav")
engine.state = "dead" | "win" | "playing"
engine._timer                          # seconds since scene load
```

### Vec3 (all arithmetic works)
```python
v = Vec3(1, 2, 3)
v.length()
v.normalized()
v.dot(other)
v.cross(other)
v + other  /  v - other  /  v * scalar
Vec3.from_list([1,2,3])
```

---

## Built-in components (import and use in scripts)

### EnemyAI
```python
from synth.enemy_ai import EnemyAI

class Soldier(Script):
    health = 100.0; speed = 3.0; damage = 12.0; sight = 14.0; score = 100

    def on_ready(self):
        self._ai = EnemyAI(
            speed=self.speed, chase_speed=self.speed*1.6,
            sight_range=self.sight, attack_range=2.2,
            attack_damage=self.damage, attack_rate=0.9,
            patrol_path=[Vec3(-5,0.9,0), Vec3(5,0.9,0)],
        )
        self._dead = False

    def on_update(self, delta):
        if self._dead: return
        attacked = self._ai.update(delta, self.node)
        if attacked:
            dead = self.node._engine.combat.take_damage(self.damage)
            if dead: self.node._engine.state = "dead"

    def on_hit(self, damage, source=None):
        self.health -= damage
        if self.health <= 0:
            self._dead = True; self._ai.die()
            self.node._engine.combat.on_enemy_killed(self.score)
            self.node._engine.particles.explosion(self.node.position)
            self.node.destroy()
```

### Vehicle (racing / car games)
```python
from synth.vehicle import Vehicle

class Car(Script):
    max_speed = 30.0; acceleration = 20.0

    def on_ready(self):
        self._car = Vehicle(max_speed=self.max_speed, acceleration=self.acceleration)

    def on_update(self, delta):
        self._car.update(delta, self.node)
        engine = self.node._engine
        engine.renderer.camera.follow(
            self.node.position, self.node.rotation.y, dist=7, height=3
        )
        engine.hud.speed_display(self._car.speed_kmh)
```

### Spell system (magic / RPG games)
Use `fireball` or `icebolt` from built-in weapon presets, or define custom:
```python
from synth.combat import WeaponDef
engine.combat.add_weapon_def(WeaponDef(
    "Thunder", damage=90, fire_rate=0.5, ammo=15, type="spell"
))
```
Pair with `engine.particles.magic(hit_pos, color)` for visual feedback.

---

## Genre guides

### FPS / Shooter
- Camera: default (first-person, mouse look)
- Weapons: use preset names in `game.json` `"weapons"` list
- Enemy: `soldier.py` using `EnemyAI`
- Scale: floor `[40,0.2,40]`, walls `[40,4,0.4]`, player scale `[0.8,1.8,0.8]`
- Include cover objects (scale `[3,2,1]`), crates, pillars
- Exit trigger at far end of level

### Racing / Car Game
- Remove combat weapons: `"weapons": []`
- Add a `vehicle` object with a car script using `Vehicle` component
- Camera follows the car: call `engine.renderer.camera.follow(...)` in on_update
- Track: long floor `[80,0.2,10]`, barrier walls on sides
- Lap trigger: `{"action": "next_scene"}` at finish line
- Show speed: `engine.hud.speed_display(kmh)`

### RPG / Magic Game
- Use `fireball` and `icebolt` weapons
- Enemy has high health, player has mana bar
- Write custom spells with `WeaponDef(type="spell")`
- Use `particles.magic(hit_pos, color)` for spell VFX
- Use `particles.smoke(pos)` for atmospheric effect
- Add health pickups with mana restore: `{"health": 30, "mana": 40}`

### Horror
- Dark sky: `"sky_color": [0.02, 0.01, 0.01]`
- Dense fog: `"fog": {"start": 5, "end": 18}`
- Low ambient: `"ambient": [0.05, 0.04, 0.06]`
- Enemy: high speed, close attack range, jump-scare behavior
- Use `particles.smoke(pos)` for atmosphere

### Platformer
- Top-down camera: call `engine.renderer.camera.top_down(player_pos, height=15)` from a player script
- Platforms: floor objects at varying heights
- Jump: physics handles it (SPACE key)
- Enemies patrol between waypoints using EnemyAI `patrol_path`

---

## Pipeline — follow these steps exactly

### Step 0 — Get parameters
Ask if not provided:
1. **Game directory** — raw assets folder
2. **Game request** — e.g. "racing game with drifting" / "horror FPS" / "magic RPG"
3. **Output directory** — default `./synth-output`

### Step 1 — Asset Scanner
```bash
find <game-dir> -type f | sort
```
Categorize: models (.glb .gltf .obj .fbx), textures (.png .jpg), sounds (.wav .mp3 .ogg), vfx (.particle).
Save to `<output>/artifacts/01_manifest.json`.

### Step 2 — Architect Agent
Think as a senior game designer. Pick the genre. Design:
- Title, genre, premise
- Player setup for this genre
- Weapons / spells / vehicle
- Enemy types and counts
- Level themes and objectives

Save to `<output>/artifacts/02_game_design.json`.

### Step 3 — Asset Curator Agent
Map every asset to a role. Fallback to box geometry when no mesh is available.
Save to `<output>/artifacts/03_curated_assets.json`.

### Step 4 — World Builder Agent
Design scene layouts. For each level:
- Choose dimensions
- Place floor, 4 walls, cover/props
- Place enemies at `position.y = 0.9` (or `scale.y/2` for larger enemies)
- Place pickups and triggers
- Choose sky, fog, and lighting

Write each to `<output>/game/scenes/<name>.scene.json`.

### Step 5 — Scripter Agent
Write **complete, working** Python scripts. No TODOs, no placeholders.
Match the genre:
- FPS: `soldier.py` with EnemyAI
- Racing: `car.py` with Vehicle
- RPG: `mage_enemy.py`, `chest.py`
- Horror: `monster.py` with fast EnemyAI + stalk behavior

Write to `<output>/game/scripts/<name>.py`.

### Step 6 — Debugger Agent
Read every script. Check:
- `Vec3` arithmetic (use Vec3 ops, not numpy)
- `self.node._engine` — correct attribute access
- `delta` present in `on_update` signature
- `self._dead` guard before `on_hit`/`on_update` after `destroy()`
- `EnemyAI` imported correctly

Fix in place. Save report to `<output>/artifacts/05_debug.json`.

### Step 7 — Builder Agent
Write `game.json`:
```json
{ "title": "<title>", "start_scene": "scenes/level1.scene.json", "weapons": [...] }
```
Copy assets: `cp <game-dir>/<src> <output>/game/assets/<dst>`
Update scene files to reference `assets/...` paths.

### Step 8 — Done
```
SynthEngine build complete
  Game:    <title> (<genre>)
  Levels:  N   Enemies: types   Weapons: types

To run:
  pip install moderngl pygame numpy trimesh pillow
  python -m synth <output>/game
```
