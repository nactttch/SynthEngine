#!/usr/bin/env python3
"""SynthEngine — AI-driven game engine for Claude, Codex, and similar agents."""
import argparse
import os
import sys
from engine.core import SynthEngine


def main():
    p = argparse.ArgumentParser(
        description="SynthEngine: build games from assets using AI agents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --game-dir ./my_game --request "build an fps survival game"
  python main.py --game-dir ./my_game --request "horror shooter" --output ./out --skip-debug
        """,
    )
    p.add_argument("--game-dir",   required=True, help="Folder containing game assets")
    p.add_argument("--request",    required=True, help="Plain-English description of the game to build")
    p.add_argument("--output",     default="./output", help="Output directory (default: ./output)")
    p.add_argument("--model",      default=os.environ.get("SYNTH_MODEL", "claude-sonnet-4-6"),
                   help="Claude model to use (default: claude-sonnet-4-6)")
    p.add_argument("--skip-debug", action="store_true", help="Skip the Debugger agent pass")
    args = p.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Error: ANTHROPIC_API_KEY environment variable is not set.", file=sys.stderr)
        print("  export ANTHROPIC_API_KEY=your_key_here", file=sys.stderr)
        sys.exit(1)

    engine = SynthEngine(model=args.model, skip_debug=args.skip_debug)
    engine.build(
        game_dir=args.game_dir,
        request=args.request,
        output_dir=args.output,
    )


if __name__ == "__main__":
    main()
