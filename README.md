# SynthEngine

**A 3D game engine built from scratch for AI agents.**

No Godot. No Unity. No existing engine underneath. SynthEngine is a custom OpenGL renderer, physics system, audio engine, and scripting runtime — designed to be driven entirely by AI without a visual editor.

> **This plugin is self-improving.** AI agents like [Claude Code](https://claude.ai/code) and [Codex](https://openai.com/codex) actively fix bugs, add features, and extend the engine as they use it — then push the changes back here. You don't need to wait for manual updates: every agent session that hits a bug or adds a feature makes the plugin better for everyone. The engine you pull today will be more capable than the one from last week, because AI agents have been using it in real projects and patching it in place.

## Install as a skill (Claude Code / compatible agents)

```
pi install github:nactttch/SynthEngine
```
Then invoke with `/synthengine` — the agent scans your assets and builds a complete game.

## Manual install (copy skill file)

```bash
git clone https://github.com/nactttch/SynthEngine
cp -r SynthEngine/skills/synthengine ~/.claude/skills/
```

## Run the engine directly

```bash
pip install moderngl pygame numpy trimesh pillow
python -m synth <your-game-dir>
```

## How it works

When `/synthengine` is invoked, a 6-agent pipeline runs:

```
Asset Scanner  →  finds all models, textures, sounds, VFX
     │
     ▼
Architect      →  designs the game (genre, mechanics, levels, enemies)
     │
     ▼
Asset Curator  →  maps your assets to game roles
     │
     ▼
World Builder  →  designs 3D level layouts as scene JSON
     │
     ▼
Scripter       →  writes Python scripts using the SynthEngine API
     │
     ▼
Debugger       →  reviews and fixes all generated scripts
     │
     ▼
Builder        →  finalises project structure, copies assets
     │
     ▼
python -m synth ./output/game   ←  runs the finished game
```

## Engine architecture

| Module | What it does |
|--------|-------------|
| `synth/engine.py` | Game loop, scene transitions, input dispatch |
| `synth/renderer.py` | ModernGL OpenGL renderer — loads GLB/OBJ, Blinn-Phong lighting |
| `synth/physics.py` | FPS capsule physics — gravity, ground snap, AABB wall collision |
| `synth/audio.py` | Music + SFX via pygame.mixer |
| `synth/scene.py` | Loads `.scene.json` files |
| `synth/scripting.py` | Dynamically loads Python scripts, runs lifecycle hooks |
| `synth/api/` | `Vec3`, `Mat4`, `SceneNode`, `Script` base class |
| `synth/shaders/` | Vertex + fragment GLSL shaders (Blinn-Phong + fog) |

## Game format

A SynthEngine game is a directory:
```
my-game/
├── game.json                ← { "title": "...", "start_scene": "scenes/level1.scene.json" }
├── scenes/
│   ├── level1.scene.json    ← objects, lighting, audio, fog config
│   └── level2.scene.json
├── scripts/
│   ├── enemy.py             ← extends Script from synth.api
│   └── pickup.py
└── assets/
    ├── models/              ← .glb, .obj, .fbx
    ├── sounds/              ← .wav, .mp3, .ogg
    └── textures/            ← .png, .jpg
```

## Script API

```python
from synth.api import Script, Vec3

class Enemy(Script):
    health: float = 100.0
    speed:  float = 3.0

    def on_ready(self):
        self.node.play_sound("assets/sounds/growl.wav", loop=True)

    def on_update(self, delta: float):
        player = self.node.find_type("player")
        if player:
            self.node.position += (player.position - self.node.position).normalized() * self.speed * delta

    def on_hit(self, damage: float, source=None):
        self.health -= damage
        if self.health <= 0:
            self.node.destroy()
```

## Export to EXE / APK

```bash
# Windows EXE (requires PyInstaller)
python build.py ./my-game --target exe

# Android APK (requires Buildozer, Linux/Mac)
python build.py ./my-game --target apk
```

## Requirements

- Python 3.11+
- `pip install moderngl pygame numpy trimesh pillow`
- For EXE: `pip install pyinstaller`
- For APK: [Buildozer](https://buildozer.readthedocs.io/)

## License

MIT
