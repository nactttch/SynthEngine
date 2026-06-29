"""SynthEngine pipeline orchestrator."""
import json
import shutil
from pathlib import Path

from .scanner import scan
from .agents.architect import ArchitectAgent
from .agents.asset_curator import AssetCuratorAgent
from .agents.world_builder import WorldBuilderAgent
from .agents.scripter import ScriptingAgent
from .agents.debugger import DebuggerAgent
from .agents.builder import BuilderAgent


class SynthEngine:
    def __init__(self, model: str = "claude-sonnet-4-6", skip_debug: bool = False):
        self.skip_debug = skip_debug
        kwargs = {"model": model}
        self.architect    = ArchitectAgent(**kwargs)
        self.curator      = AssetCuratorAgent(**kwargs)
        self.world_builder = WorldBuilderAgent(**kwargs)
        self.scripter     = ScriptingAgent(**kwargs)
        self.debugger     = DebuggerAgent(**kwargs)
        self.builder      = BuilderAgent(**kwargs)

    def build(self, game_dir: str, request: str, output_dir: str = "./output"):
        art_dir = Path(output_dir) / "artifacts"
        art_dir.mkdir(parents=True, exist_ok=True)

        # --- 1. Scan ---
        print(f"\n[SynthEngine] Scanning assets in: {game_dir}")
        manifest = scan(game_dir)
        print(f"  Models:{len(manifest.models)}  Textures:{len(manifest.textures)}  "
              f"Sounds:{len(manifest.sounds)}  VFX:{len(manifest.vfx)}  Scripts:{len(manifest.scripts)}")

        # --- 2. Architect ---
        print("\n[Architect] Designing game...")
        game_design = self.architect.run(request, manifest.to_dict())
        _save(art_dir / "01_game_design.json", game_design)
        print(f'  "{game_design.get("title")}" — {game_design.get("genre")}')
        if game_design.get("missing_assets"):
            print(f"  Missing assets noted: {game_design['missing_assets']}")

        # --- 3. Asset Curator ---
        print("\n[Asset Curator] Mapping assets to roles...")
        curated = self.curator.run(game_design, manifest.to_dict())
        _save(art_dir / "02_curated_assets.json", curated)
        missing = curated.get("missing_critical", [])
        if missing:
            print(f"  Critical assets missing: {missing}")

        # --- 4. World Builder ---
        print("\n[World Builder] Designing levels...")
        world_map = self.world_builder.run(game_design, curated)
        _save(art_dir / "03_world_map.json", world_map)
        scenes = world_map.get("scenes", [])
        print(f"  {len(scenes)} scene(s): {[s.get('name') for s in scenes]}")

        # --- 5. Scripter ---
        print("\n[Scripter] Writing GDScript code...")
        scripting = self.scripter.run(game_design, world_map, curated)
        _save(art_dir / "04_scripts.json", scripting)
        scripts = scripting.get("scripts", [])
        print(f"  {len(scripts)} script(s): {[s.get('filename') for s in scripts]}")

        # --- 6. Debugger ---
        if not self.skip_debug:
            print("\n[Debugger] Reviewing and fixing code...")
            debug = self.debugger.run(scripts)
            _save(art_dir / "05_debug_report.json", debug)
            issues  = debug.get("issues", [])
            scripts = debug.get("fixed_scripts", scripts)
            errors   = sum(1 for i in issues if i.get("severity") == "error")
            warnings = sum(1 for i in issues if i.get("severity") == "warning")
            print(f"  {errors} error(s) fixed, {warnings} warning(s)")

        # --- 7. Builder ---
        print("\n[Builder] Assembling Godot 4 project...")
        project = self.builder.run(game_design, world_map, curated, scripts)
        _save(art_dir / "06_builder_output.json", project)

        # Write to disk
        game_out = Path(output_dir) / "game"
        self._write_project(game_out, game_dir, project, scripting)

        print(f"\n[SynthEngine] Done! Godot project at: {game_out}/")
        print("  Open project.godot in Godot 4, then: Project → Export")
        if project.get("setup_notes"):
            print(f"\n  Notes: {project['setup_notes']}")

    def _write_project(self, game_out: Path, game_dir: str, project: dict, scripting: dict):
        game_out.mkdir(parents=True, exist_ok=True)
        (game_out / "scenes").mkdir(exist_ok=True)
        (game_out / "scripts").mkdir(exist_ok=True)
        (game_out / "assets").mkdir(exist_ok=True)

        (game_out / "project.godot").write_text(project.get("project_godot", ""))
        (game_out / "export_presets.cfg").write_text(project.get("export_presets", ""))

        for scene in project.get("scenes", []):
            (game_out / "scenes" / scene["filename"]).write_text(scene["content"])

        for script in scripting.get("scripts", []):
            (game_out / "scripts" / script["filename"]).write_text(script["content"])

        src_root = Path(game_dir).resolve()
        for copy in project.get("asset_copies", []):
            src = src_root / copy["from"]
            dst = game_out / copy["to"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if src.exists():
                shutil.copy2(src, dst)

        notes = project.get("setup_notes", "Generated by SynthEngine.")
        (game_out / "SETUP.md").write_text(f"# Setup Notes\n\n{notes}\n")


def _save(path: Path, data: dict):
    path.write_text(json.dumps(data, indent=2))
