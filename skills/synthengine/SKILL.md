---
name: synthengine
description: >
  AI-first 3D game engine. Scans an asset folder, runs a 6-agent pipeline
  (Architect, Asset Curator, World Builder, Scripter, Debugger, Builder),
  and writes a complete SynthEngine game project (scene JSON + Python scripts)
  ready to run with `python -m synth <game-dir>` — no Godot, no Unity,
  no existing engine. Pure custom engine designed for AI agents.
  Invoke with /synthengine [game-dir] [request] or let it ask you.
argument-hint: "[game-dir] [game-request]"
license: MIT
---

# SynthEngine

You are running the SynthEngine pipeline. Your tools (Bash, Read, Write) are
the engine. You will scan a folder of game assets, design a game, and write
all the files that `python -m synth <output-dir>` needs to run it.

## SynthEngine Game Format

A SynthEngine game is a directory with:
```
<game-dir>/
├── game.json              ← manifest (start scene, title)
├── scenes/
│   └── *.scene.json       ← one file per level
└── scripts/
    └── *.py               ← one file per game object class
```

### game.json
```json
{
  "title": "My FPS Game",
  "start_scene": "scenes/level1.scene.json"
}
```

### scene.json schema
Every field is optional except `name`.
```json
{
  "name": "Level1",
  "next_scene": "scenes/level2.scene.json",
  "spawn": [0.0, 1.8, 0.0],
  "sky_color": [0.4, 0.6, 0.9],
  "fog_enabled": true,
  "fog": { "start": 20, "end": 80, "color": [0.5, 0.6, 0.7] },
  "lighting": {
    "ambient": [0.25, 0.25, 0.3],
    "directional": {
      "direction": [0.5, -1.0, 0.3],
      "color": [1.0, 0.95, 0.8]
    }
  },
  "audio": { "music": "assets/sounds/ambient.ogg" },
  "objects": [
    {
      "id":       "floor_main",
      "type":     "floor",
      "mesh":     "assets/models/floor.glb",
      "position": [0, 0, 0],
      "rotation": [0, 0, 0],
      "scale":    [20, 0.2, 20],
      "color":    [0.5, 0.5, 0.5]
    },
    {
      "id":       "wall_north",
      "type":     "static",
      "position": [0, 2, -10],
      "scale":    [20, 4, 0.3],
      "color":    [0.6, 0.55, 0.5]
    },
    {
      "id":       "enemy_01",
      "type":     "enemy",
      "mesh":     "assets/models/enemy.glb",
      "position": [5, 0.9, -8],
      "scale":    [1, 1, 1],
      "color":    [0.8, 0.2, 0.2],
      "script":   "scripts/enemy.py",
      "props":    { "health": 100, "speed": 3.0, "damage": 15 }
    },
    {
      "id":       "rifle_pickup",
      "type":     "pickup",
      "position": [3, 0.5, -3],
      "scale":    [0.5, 0.5, 0.5],
      "color":    [0.3, 0.3, 0.9],
      "props":    { "weapon": "rifle", "ammo": 30 }
    },
    {
      "id":       "exit_door",
      "type":     "trigger",
      "position": [0, 1, -18],
      "scale":    [3, 3, 1],
      "props":    { "action": "next_scene" }
    }
  ]
}
```

### Object types
| type | behaviour |
|------|-----------|
| `floor` | static geometry + ground collision surface |
| `static` | solid wall/prop, AABB collision |
| `enemy` | scriptable AI object |
| `pickup` | scriptable item |
| `trigger` | invisible volume, fires action when player enters |
| `prop` | decorative static (no collision) |

### Script API
Scripts live in `scripts/` and are attached to objects via `"script"` in the scene JSON.
Props from the scene JSON are set as attributes before `on_ready()` is called.

```python
# scripts/enemy.py
from synth.api import Script, Vec3

class Enemy(Script):
    health: float = 100.0
    speed:  float = 3.0
    damage: float = 15.0

    def on_ready(self):
        self.node.play_sound("assets/sounds/enemy_idle.wav", loop=True)
        self._attack_timer = 0.0

    def on_update(self, delta: float):
        player = self.node.find_type("player")
        if not player:
            return
        dist = (player.position - self.node.position).length()
        if dist < 12.0:
            direction = (player.position - self.node.position).normalized()
            direction.y = 0
            self.node.position += direction * self.speed * delta

        self._attack_timer += delta
        if self._attack_timer > 1.5 and dist < 2.0:
            self._attack_timer = 0.0
            # Damage player via game_manager autoload
            self.node.play_sound("assets/sounds/enemy_attack.wav")

    def on_hit(self, damage: float, source=None):
        self.health -= damage
        self.node.play_sound("assets/sounds/enemy_hurt.wav")
        if self.health <= 0:
            self.node.play_sound("assets/sounds/enemy_death.wav")
            self.node.destroy()
```

SceneNode methods available inside scripts:
- `self.node.position` — Vec3, read/write
- `self.node.rotation` — Vec3 (euler degrees), read/write
- `self.node.scale`    — Vec3, read/write
- `self.node.play_sound(path, loop=False)`
- `self.node.find(id)` — returns SceneNode or None
- `self.node.find_type(type_str)` — first node of that type or None
- `self.node.destroy()` — removes object from scene
- `self.node.props`    — dict of scene JSON props

---

## Pipeline — follow these steps exactly

### Step 0 — Get parameters

If the user did not provide them as arguments, ask:
1. **Game directory** — path containing the raw assets (models, sounds, textures, VFX)
2. **Game request** — what game to build (e.g. "fps survival horror", "sci-fi shooter")
3. **Output directory** — where to write the game project (default: `./synth-output`)

### Step 1 — Asset Scanner

Run:
```bash
find <game-dir> -type f | sort
```
Categorize every file:
- **models**: `.glb .gltf .obj .fbx .dae .blend .ply`
- **textures**: `.png .jpg .jpeg .webp .tga .bmp .exr .hdr`
- **sounds**: `.wav .mp3 .ogg .flac .aac .opus`
- **vfx**: `.vfx .particle .pcf`
- **scripts**: `.py .lua .gd`

Print a short summary. Save the manifest to `<output>/artifacts/01_manifest.json`.

### Step 2 — Architect Agent

**Role:** Senior game designer. Read the asset list and user request. Design a complete game.

Think through:
- Genre, title, premise
- Player perspective (first-person for FPS)
- Weapons (what models can serve as weapons?)
- Enemy types
- Level count and themes
- Win/lose condition
- Art style that fits available assets

Save to `<output>/artifacts/02_game_design.json`:
```json
{
  "title": string,
  "genre": string,
  "premise": string,
  "player": { "perspective": "first_person", "health": 100, "speed": 5 },
  "weapons": [{ "name": string, "model": string|null, "damage": number, "fire_rate": number, "ammo": number }],
  "enemies": [{ "name": string, "model": string|null, "health": number, "speed": number, "damage": number }],
  "levels":  [{ "name": string, "theme": string, "enemy_count": number, "objective": string }],
  "win_condition": string,
  "lose_condition": string
}
```

### Step 3 — Asset Curator Agent

**Role:** Art director. Map every available asset to a game role. Be creative — a
sci-fi crate model works as a wall prop, a dragon model is an enemy, etc.

Save to `<output>/artifacts/03_curated_assets.json`:
```json
{
  "player_model":     string|null,
  "weapon_models":    { "<weapon-name>": string|null },
  "enemy_models":     { "<enemy-name>": string|null },
  "environment":      { "floor": string|null, "walls": [string], "props": [string] },
  "sounds": {
    "music":          string|null,
    "ambient":        string|null,
    "footstep":       string|null,
    "shoot":          string|null,
    "enemy_idle":     string|null,
    "enemy_hurt":     string|null,
    "enemy_death":    string|null,
    "enemy_attack":   string|null,
    "pickup":         string|null
  },
  "missing_critical": [string]
}
```

### Step 4 — World Builder Agent

**Role:** Level designer. For each level in the game design, create a complete scene.
Design fun layouts: corridors, open areas, cover objects, good sightlines.

Rules:
- Y is up. Player eye height is 1.8.
- Floor `scale.y` = 0.2. Wall `scale.y` = 4.
- Enemies go on the floor (position.y = 0.9 for a scale-1 enemy).
- Every level needs: floor, walls (4 sides minimum), at least one enemy spawn, one exit trigger.
- Put weapon pickups and health pickups between enemies.

Write each scene to `<output>/game/scenes/<name>.scene.json`.

### Step 5 — Scripter Agent

**Role:** Game programmer. Write complete, working Python scripts using the SynthEngine
Script API shown above. No placeholders, no TODOs.

Required scripts:
- `scripts/enemy.py` — patrol/chase AI, on_hit handler
- `scripts/pickup.py` — weapon/health/ammo pickup logic
- `scripts/boss.py` — boss enemy if any (harder AI, more health)

Write each to `<output>/game/scripts/<name>.py`.
Save script list to `<output>/artifacts/04_scripts.json`.

### Step 6 — Debugger Agent

**Role:** QA engineer. Re-read every script you wrote. Check for:
- `Vec3` used as numpy array (they're different — Vec3 has .x/.y/.z, use Vec3 arithmetic)
- Calling methods that don't exist on SceneNode
- `on_update` missing `delta` parameter
- Unclosed files or resources
- Logic bugs (enemy never reaches player, health never depletes, etc.)

Fix all issues in place. Update the files on disk.
Save report to `<output>/artifacts/05_debug.json`.

### Step 7 — Builder Agent

**Role:** Project assembler. Write the `game.json` manifest, finalize all scene files,
and copy assets to the right locations.

Create `<output>/game/game.json`:
```json
{
  "title": "<game title>",
  "version": "1.0.0",
  "start_scene": "scenes/<first-level>.scene.json"
}
```

For each curated asset, copy it from `<game-dir>/<original-path>` to
`<output>/game/assets/<category>/<filename>` using Bash:
```bash
cp <src> <dst>
```

Update all scene JSON files to use the new `assets/...` paths.

### Step 8 — Done

Print a summary:
```
SynthEngine build complete
  Game: <title>
  Levels: <N>   Enemies: <types>   Weapons: <types>
  Output: <output>/game/

To run:
  pip install moderngl pygame numpy trimesh pillow
  python -m synth <output>/game
```
