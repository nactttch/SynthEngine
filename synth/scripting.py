"""Dynamic script loader and runner."""
import importlib.util
import inspect
from pathlib import Path

from .api.script import Script
from .api.node   import SceneNode


class ScriptRunner:
    def __init__(self):
        self.nodes:   dict[str, SceneNode]  = {}
        self._scripts: list[tuple[SceneNode, Script]] = []
        self._engine  = None

    def load_scene(self, scene: dict, engine):
        self.nodes.clear()
        self._scripts.clear()
        self._engine = engine

        game_dir = Path(scene.get("_dir", "."))

        # Create a node for the player (camera is always the player)
        player_node = SceneNode({"id": "player", "type": "player",
                                 "position": scene.get("spawn", [0, 1.5, 0])}, engine)
        self.nodes["player"] = player_node

        for obj in scene.get("objects", []):
            node = SceneNode(obj, engine)
            self.nodes[node.id] = node

            script_rel = obj.get("script")
            if not script_rel:
                continue

            script_path = game_dir / script_rel
            if not script_path.exists():
                print(f"[scripts] not found: {script_path}")
                continue

            script_cls = self._load_class(script_path)
            if script_cls is None:
                continue

            instance = script_cls()
            instance.node = node
            # Inject props as attributes
            for k, v in obj.get("props", {}).items():
                setattr(instance, k, v)

            self._scripts.append((node, instance))
            try:
                instance.on_ready()
            except Exception as e:
                print(f"[scripts] on_ready error in {script_path.name}: {e}")

    def update(self, delta: float):
        for node, script in list(self._scripts):
            if not node.is_alive:
                continue
            try:
                script.on_update(delta)
                # Sync position back to renderer
                p = node.position
                self._engine.renderer.set_position(node.id, p)
            except Exception as e:
                print(f"[scripts] on_update error ({node.id}): {e}")

    def hit(self, node_id: str, damage: float, source=None):
        node = self.nodes.get(node_id)
        if node is None:
            return
        for n, s in self._scripts:
            if n is node:
                try:
                    s.on_hit(damage, source)
                except Exception as e:
                    print(f"[scripts] on_hit error ({node_id}): {e}")

    @staticmethod
    def _load_class(path: Path):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)
        except Exception as e:
            print(f"[scripts] load error in {path.name}: {e}")
            return None
        for _, obj in inspect.getmembers(mod, inspect.isclass):
            if issubclass(obj, Script) and obj is not Script:
                return obj
        print(f"[scripts] no Script subclass found in {path.name}")
        return None
