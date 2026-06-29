"""Scans a game project directory and catalogs all assets."""
from pathlib import Path
from .protocols import AssetManifest

MODEL_EXTS    = {'.glb', '.gltf', '.obj', '.fbx', '.dae', '.blend', '.3ds', '.ply', '.usd', '.usdz'}
TEXTURE_EXTS  = {'.png', '.jpg', '.jpeg', '.webp', '.tga', '.bmp', '.exr', '.hdr', '.svg', '.dds'}
SOUND_EXTS    = {'.wav', '.mp3', '.ogg', '.flac', '.aac', '.m4a', '.opus'}
VFX_EXTS      = {'.vfx', '.particle', '.pcf', '.ptc', '.niagara'}
SCRIPT_EXTS   = {'.gd', '.py', '.cs', '.lua', '.gdshader', '.shader', '.glsl', '.hlsl'}
IGNORED_DIRS  = {'.git', '__pycache__', '.godot', 'node_modules', '.venv', 'venv'}


def scan(game_dir: str) -> AssetManifest:
    root = Path(game_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Game directory not found: {game_dir}")

    manifest = AssetManifest()

    for p in root.rglob("*"):
        if any(ig in p.parts for ig in IGNORED_DIRS):
            continue
        if not p.is_file():
            continue

        suffix = p.suffix.lower()
        rel    = str(p.relative_to(root))
        size   = round(p.stat().st_size / 1_048_576, 3)
        entry  = {"name": p.stem, "path": rel, "ext": suffix, "size_mb": size}

        if suffix in MODEL_EXTS:
            manifest.models.append(entry)
        elif suffix in TEXTURE_EXTS:
            manifest.textures.append(entry)
        elif suffix in SOUND_EXTS:
            manifest.sounds.append(entry)
        elif suffix in VFX_EXTS:
            manifest.vfx.append(entry)
        elif suffix in SCRIPT_EXTS:
            manifest.scripts.append(entry)
        else:
            manifest.misc.append(entry)

    return manifest
