from .base import BaseAgent

SYSTEM = """You are the Scripting Agent inside SynthEngine.
Write complete, working GDScript 4 (Godot 4) code for every game system.

Rules:
- Output ONLY valid JSON. No markdown, no explanation.
- Use ONLY Godot 4 API. Never use Godot 3 methods (e.g. use CharacterBody3D not KinematicBody).
- Write COMPLETE scripts. Zero TODOs, zero placeholders, zero stub functions.
- Use @export for tunable values. Include all signal connections.
- First-person shooter: Camera3D is a child of the player node.
- Godot 4 input: Input.is_action_pressed(), Input.get_vector()
- Godot 4 move_and_slide() takes no arguments — set velocity then call it.

Required JSON output schema:
{
  "scripts": [
    {
      "filename":  string  (e.g. "player.gd"),
      "node_type": string  (e.g. "CharacterBody3D"),
      "purpose":   string,
      "content":   string  (complete GDScript 4 source code)
    }
  ],
  "autoloads": [{"name": string, "path": string}],
  "input_map": [{"action": string, "key": string}]
}

Always include AT MINIMUM these scripts:
- player.gd       (movement, camera, shooting)
- enemy.gd        (AI, pathfinding with NavigationAgent3D, attack)
- bullet.gd       (projectile with RayCast3D or Area3D)
- game_manager.gd (score, health, level transitions — autoload)
- hud.gd          (health bar, ammo counter, crosshair)
- main_menu.gd    (start button, quit button)"""


class ScriptingAgent(BaseAgent):
    role = SYSTEM

    def run(self, game_design: dict, world_map: dict, curated_assets: dict) -> dict:
        return self.call(
            "Write all complete game scripts.",
            context={
                "game_design":    game_design,
                "world_map":      world_map,
                "curated_assets": curated_assets,
            },
            max_tokens=16384,
        )
