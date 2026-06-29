# SynthEngine

**AI-driven game engine for Claude Code, Codex, and similar agents.**

Point SynthEngine at a folder of game assets, describe the game you want in plain English, and a 6-agent AI pipeline produces a complete, openable **Godot 4** project — exportable to **Windows EXE** and **Android APK**.

## How It Works

```
[Asset Folder] + [Plain-English Request]
          ↓
     Asset Scanner
          ↓
 ┌─────────────────────────────────────┐
 │           6-Agent Pipeline          │
 │                                     │
 │  1. Architect    → Game Design Doc  │
 │  2. Asset Curator → Asset Map       │
 │  3. World Builder → Level Layout    │
 │  4. Scripter      → GDScript Code   │
 │  5. Debugger      → Bug Fixes       │
 │  6. Builder       → Godot Project   │
 └─────────────────────────────────────┘
          ↓
   output/game/  (open in Godot 4)
          ↓
   Export → Windows EXE / Android APK
```

## Quick Start

```bash
git clone https://github.com/nactttch/SynthEngine
cd SynthEngine
pip install -r requirements.txt
cp .env.example .env          # add your ANTHROPIC_API_KEY

python main.py \
  --game-dir ./my_game_assets \
  --request  "build an fps survival game"
```

The generated Godot 4 project lands in `./output/game/`.

## Requirements

- Python 3.11+
- `ANTHROPIC_API_KEY` environment variable
- [Godot 4.3+](https://godotengine.org/download/) to open and export the project

## CLI Options

```
--game-dir   PATH    Folder containing your game assets (models, sounds, textures, VFX)
--request    TEXT    What kind of game to build (plain English)
--output     PATH    Output directory (default: ./output)
--model      NAME    Claude model (default: claude-sonnet-4-6)
--skip-debug         Skip the Debugger agent pass
```

## Agents

| # | Agent | Role |
|---|-------|------|
| 1 | **Architect** | Reads assets + request → full Game Design Document |
| 2 | **Asset Curator** | Maps available assets to game roles (player, enemies, env) |
| 3 | **World Builder** | Designs scene layouts with 3D object placement |
| 4 | **Scripter** | Writes complete GDScript 4 for every game system |
| 5 | **Debugger** | Reviews and fixes all generated code |
| 6 | **Builder** | Assembles the final Godot 4 project structure |

## Output Structure

```
output/
├── artifacts/              # Per-agent JSON outputs (for inspection/debugging)
│   ├── 01_game_design.json
│   ├── 02_curated_assets.json
│   ├── 03_world_map.json
│   ├── 04_scripts.json
│   ├── 05_debug_report.json
│   └── 06_builder_output.json
└── game/                   # The generated Godot 4 project
    ├── project.godot       ← open this in Godot 4
    ├── export_presets.cfg
    ├── scenes/*.tscn
    ├── scripts/*.gd
    ├── assets/
    └── SETUP.md
```

## Exporting the Game

1. Install [Godot 4](https://godotengine.org/download/) and open `output/game/project.godot`
2. Install export templates: **Editor → Manage Export Templates**
3. **Project → Export**
   - **Windows Desktop** → Export Project → `.exe`
   - **Android** → configure keystore → Export Project → `.apk`

## Supported Asset Types

| Type | Extensions |
|------|-----------|
| 3D Models | `.glb .gltf .obj .fbx .dae .blend .3ds .ply` |
| Textures | `.png .jpg .webp .tga .bmp .exr .hdr .dds` |
| Sounds | `.wav .mp3 .ogg .flac .aac .opus` |
| VFX | `.vfx .particle .pcf .ptc` |
| Shaders | `.gdshader .shader .glsl .hlsl` |

## License

MIT
