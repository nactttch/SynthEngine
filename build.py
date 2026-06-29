#!/usr/bin/env python3
"""
Package a SynthEngine game into a standalone EXE or APK.

Usage:
  python build.py <game-dir> --target exe       # Windows EXE (needs PyInstaller)
  python build.py <game-dir> --target apk       # Android APK (needs Buildozer on Linux/Mac)
"""
import sys
import subprocess
import shutil
import argparse
from pathlib import Path


def build_exe(game_dir: Path):
    entry = game_dir / "_run_game.py"
    entry.write_text(
        f"import sys; sys.argv = ['']; "
        f"from synth.engine import Engine; Engine(r'{game_dir}').run()\n"
    )
    title = _read_title(game_dir)
    cmd = [
        "pyinstaller", "--onefile", "--noconsole",
        "--name", title.replace(" ", "_"),
        "--add-data", f"{game_dir}{':' if sys.platform != 'win32' else ';'}game_data",
        str(entry),
    ]
    subprocess.run(cmd, check=True)
    print(f"\nEXE written to dist/{title.replace(' ', '_')}.exe")


def build_apk(game_dir: Path):
    buildozer_spec = game_dir.parent / "buildozer.spec"
    if not buildozer_spec.exists():
        _write_buildozer_spec(game_dir, buildozer_spec)
    subprocess.run(["buildozer", "android", "debug"], cwd=game_dir.parent, check=True)
    print("\nAPK written to bin/ directory")


def _read_title(game_dir: Path) -> str:
    import json
    manifest = game_dir / "game.json"
    if manifest.exists():
        return json.loads(manifest.read_text()).get("title", "SynthGame")
    return "SynthGame"


def _write_buildozer_spec(game_dir: Path, out: Path):
    title = _read_title(game_dir)
    out.write_text(f"""[app]
title = {title}
package.name = {title.lower().replace(" ", "")}
package.domain = org.synthengine
source.dir = .
source.include_exts = py,json,glb,gltf,obj,fbx,png,jpg,wav,mp3,ogg,vert,frag
version = 1.0
requirements = python3,pygame,moderngl,numpy,trimesh,pillow
orientation = landscape
android.permissions = INTERNET
[buildozer]
log_level = 2
""")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("game_dir")
    p.add_argument("--target", choices=["exe", "apk"], required=True)
    args = p.parse_args()

    gd = Path(args.game_dir).resolve()
    if not gd.exists():
        print(f"Error: {gd} not found")
        sys.exit(1)

    if args.target == "exe":
        build_exe(gd)
    else:
        build_apk(gd)
