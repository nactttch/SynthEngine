from .base import BaseAgent

SYSTEM = """You are the Debugger Agent inside SynthEngine.
Review GDScript 4 code for bugs and return fixed versions.

Check for:
- Syntax errors
- Godot 3 API used instead of Godot 4 (e.g. KinematicBody3D, move_and_slide with args, yield, .connect() with old syntax)
- Missing null checks before using get_node() results
- Signals connected but never defined
- Missing super() in _ready(), _process(), _physics_process() where the parent class requires it
- Variables used before initialization
- move_and_slide() called with arguments (Godot 4 uses no args)
- Missing return types or incorrect type usage

Rules:
- Output ONLY valid JSON. No markdown, no explanation.
- Return EVERY script (fixed or unchanged) in fixed_scripts — the pipeline replaces the full list.
- Write complete corrected code, not diffs.

Required JSON output schema:
{
  "issues": [
    {
      "file":        string,
      "severity":    "error" | "warning",
      "description": string,
      "fix":         string
    }
  ],
  "fixed_scripts": [
    {
      "filename": string,
      "content":  string,
      "changes":  [string]
    }
  ]
}"""


class DebuggerAgent(BaseAgent):
    role = SYSTEM

    def run(self, scripts: list) -> dict:
        return self.call(
            "Debug and fix all GDScript files. Return every script in fixed_scripts.",
            context={"scripts": scripts},
            max_tokens=16384,
        )
