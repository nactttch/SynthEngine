"""Shared data structures passed between SynthEngine agents."""
from dataclasses import dataclass, field


@dataclass
class AssetManifest:
    models: list = field(default_factory=list)
    textures: list = field(default_factory=list)
    sounds: list = field(default_factory=list)
    vfx: list = field(default_factory=list)
    scripts: list = field(default_factory=list)
    misc: list = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "models": [f"{m['name']}{m['ext']}" for m in self.models],
            "textures": [f"{t['name']}{t['ext']}" for t in self.textures],
            "sounds": [f"{s['name']}{s['ext']}" for s in self.sounds],
            "vfx": [f"{v['name']}{v['ext']}" for v in self.vfx],
            "scripts": [f"{sc['name']}{sc['ext']}" for sc in self.scripts],
        }

    def to_dict(self) -> dict:
        return {
            "models": self.models,
            "textures": self.textures,
            "sounds": self.sounds,
            "vfx": self.vfx,
            "scripts": self.scripts,
            "misc": self.misc,
        }
