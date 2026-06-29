"""python -m synth <game-dir>"""
import sys
from pathlib import Path

if len(sys.argv) < 2:
    print("Usage: python -m synth <game-dir>")
    print("  <game-dir> must contain a game.json or scenes/*.scene.json")
    sys.exit(1)

from synth.engine import Engine
Engine(sys.argv[1]).run()
