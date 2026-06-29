from .base import BaseAgent

SYSTEM = """You are the Builder Agent inside SynthEngine.
Assemble a complete, openable Godot 4 project from scripts, world data, and asset mappings.

Godot 4 .tscn format reference:
[gd_scene load_steps=3 format=3 uid="uid://b0"]

[ext_resource type="Script" path="res://scripts/player.gd" id="1_player"]
[ext_resource type="PackedScene" path="res://assets/models/player.glb" id="2_model"]

[node name="Level1" type="Node3D"]

[node name="Player" type="CharacterBody3D" parent="."]
script = ExtResource("1_player")
position = Vector3(0, 1, 0)

[node name="Mesh" type="MeshInstance3D" parent="Player"]
mesh = ExtResource("2_model")

Godot 4 project.godot format reference:
config_version=5

[application]
config/name="MyGame"
run/main_scene="res://scenes/main_menu.tscn"
config/features=PackedStringArray("4.3", "Forward Plus")

[display]
window/size/viewport_width=1920
window/size/viewport_height=1080

Rules:
- Output ONLY valid JSON. No markdown, no explanation.
- All scene file paths use res:// prefix (e.g. res://scripts/player.gd).
- Scripts live at res://scripts/, scenes at res://scenes/, assets at res://assets/.
- ext_resource ids must be unique strings like "1_player", "2_enemy" etc.
- asset_copies maps source paths (relative to game-dir) to dest paths (relative to project root).

Required JSON output schema:
{
  "project_godot":  string  (full content of project.godot),
  "scenes": [
    {"filename": string, "content": string}
  ],
  "export_presets": string  (full content of export_presets.cfg),
  "asset_copies":  [{"from": string, "to": string}],
  "setup_notes":   string
}"""


class BuilderAgent(BaseAgent):
    role = SYSTEM

    def run(self, game_design: dict, world_map: dict, curated_assets: dict, scripts: list) -> dict:
        return self.call(
            "Assemble the complete Godot 4 project.",
            context={
                "game_design":    game_design,
                "world_map":      world_map,
                "curated_assets": curated_assets,
                "scripts":        scripts,
            },
            max_tokens=16384,
        )
