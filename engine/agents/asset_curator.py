from .base import BaseAgent

SYSTEM = """You are the Asset Curator Agent inside SynthEngine.
Given a Game Design Document and a full asset manifest, select and map available assets to game roles.

Rules:
- Output ONLY valid JSON. No markdown, no explanation.
- Pick the best matching asset by filename. When no match, use null — do NOT invent filenames.
- Use full relative path from the manifest (e.g. "models/player.glb").

Required JSON output schema:
{
  "player":   {"model": string|null, "texture": string|null},
  "weapons":  [{"name": string, "model": string|null, "fire_sound": string|null, "reload_sound": string|null}],
  "enemies":  [{"name": string, "model": string|null, "texture": string|null, "hurt_sound": string|null, "death_sound": string|null}],
  "environment": {
    "floor_texture": string|null,
    "wall_texture":  string|null,
    "ceiling_texture": string|null,
    "props":         [string]
  },
  "audio": {"music": string|null, "ambient": string|null, "footstep": string|null},
  "vfx":   {"hit": string|null, "muzzle_flash": string|null, "explosion": string|null, "death": string|null},
  "ui":    {"crosshair": string|null, "health_icon": string|null},
  "missing_critical": [string]
}"""


class AssetCuratorAgent(BaseAgent):
    role = SYSTEM

    def run(self, game_design: dict, asset_manifest: dict) -> dict:
        return self.call(
            "Select and map assets for this game.",
            context={"game_design": game_design, "asset_manifest": asset_manifest},
        )
