"""Loads .scene.json files and the game.json manifest."""
import json
from pathlib import Path


class SceneLoader:
    def __init__(self, game_dir: Path):
        self.game_dir = game_dir

    def load(self, scene_path: str) -> dict:
        """Load a scene file relative to game_dir. Returns the scene dict."""
        path = self.game_dir / scene_path
        if not path.exists():
            raise FileNotFoundError(f"Scene not found: {path}")
        data = json.loads(path.read_text())
        # Resolve asset paths to be absolute
        data["_dir"] = str(self.game_dir)
        return data

    def load_manifest(self) -> dict:
        p = self.game_dir / "game.json"
        if p.exists():
            return json.loads(p.read_text())
        # Auto-discover first scene
        scenes = sorted(self.game_dir.glob("scenes/*.scene.json"))
        if not scenes:
            scenes = sorted(self.game_dir.glob("**/*.scene.json"))
        if not scenes:
            raise FileNotFoundError(f"No .scene.json files in {self.game_dir}")
        return {"start_scene": str(scenes[0].relative_to(self.game_dir))}

    def asset_path(self, scene: dict, rel_path: str) -> Path:
        return Path(scene["_dir"]) / rel_path
