"""2D HUD overlay — drawn as a transparent pygame surface on top of the 3D scene."""
import pygame
import numpy as np
import moderngl


class HUD:
    def __init__(self, ctx: moderngl.Context, w: int, h: int):
        self.ctx = ctx
        self.w, self.h = w, h
        pygame.font.init()
        self._f_lg  = pygame.font.SysFont("monospace", 34, bold=True)
        self._f_md  = pygame.font.SysFont("monospace", 20)
        self._f_sm  = pygame.font.SysFont("monospace", 14)
        self._surf  = pygame.Surface((w, h), pygame.SRCALPHA)
        self._tex   = ctx.texture((w, h), 4)
        self._prog, self._vao = self._build()
        self._msg: tuple | None = None  # (text, color, ttl)

    # ── public draw calls (call between begin/flush) ───────────────────────

    def begin(self):
        self._surf.fill((0, 0, 0, 0))

    def crosshair(self, style: str = "cross"):
        cx, cy = self.w // 2, self.h // 2
        col = (255, 255, 255, 190)
        g, sz = 5, 12
        if style == "cross":
            pygame.draw.line(self._surf, col, (cx-sz, cy), (cx-g, cy), 2)
            pygame.draw.line(self._surf, col, (cx+g,  cy), (cx+sz, cy), 2)
            pygame.draw.line(self._surf, col, (cx, cy-sz), (cx, cy-g),  2)
            pygame.draw.line(self._surf, col, (cx, cy+g),  (cx, cy+sz), 2)
        elif style == "dot":
            pygame.draw.circle(self._surf, col, (cx, cy), 3)
        elif style == "circle":
            pygame.draw.circle(self._surf, col, (cx, cy), g, 2)

    def health_bar(self, current: float, maximum: float, label="HP",
                   x=20, y=None):
        if y is None:
            y = self.h - 62
        w, h = 210, 22
        ratio = max(0.0, current / maximum)
        r = int(255 * (1.0 - ratio))
        g = int(200 * ratio)
        pygame.draw.rect(self._surf, (40, 0, 0, 180),  (x, y, w, h), border_radius=5)
        if ratio > 0:
            pygame.draw.rect(self._surf, (r, g, 0, 220), (x, y, int(w * ratio), h), border_radius=5)
        pygame.draw.rect(self._surf, (180, 180, 180, 100), (x, y, w, h), 1, border_radius=5)
        txt = self._f_md.render(f"{label}  {int(current)}/{int(maximum)}", True, (255,255,255))
        self._surf.blit(txt, (x + 5, y + 2))

    def ammo_counter(self, ammo: int, reserve: int, weapon_name=""):
        x, y = self.w - 170, self.h - 58
        big = self._f_lg.render(str(ammo), True, (255, 240, 195))
        sub = self._f_md.render(f"/ {reserve}  {weapon_name}", True, (150, 150, 150))
        self._surf.blit(big, (x, y))
        self._surf.blit(sub, (x + 52, y + 12))

    def mana_bar(self, current: float, maximum: float, x=20, y=None):
        if y is None:
            y = self.h - 92
        w, h = 210, 12
        ratio = max(0.0, current / maximum)
        pygame.draw.rect(self._surf, (0, 0, 40, 180),  (x, y, w, h), border_radius=4)
        if ratio > 0:
            pygame.draw.rect(self._surf, (30, 80, 255, 220), (x, y, int(w * ratio), h), border_radius=4)

    def score_display(self, kills: int, score: int, timer: float = None):
        txt = self._f_md.render(f"Kills: {kills}   Score: {score}", True, (220, 220, 220))
        self._surf.blit(txt, (10, 10))
        if timer is not None:
            t = self._f_md.render(f"{int(timer)}s", True, (200, 200, 100))
            self._surf.blit(t, (self.w - 60, 10))

    def speed_display(self, speed_kmh: float):
        txt = self._f_md.render(f"{int(speed_kmh)} km/h", True, (200, 230, 255))
        self._surf.blit(txt, (self.w // 2 - 40, self.h - 40))

    def minimap(self, scene: dict, player_pos, size: int = 130):
        x, y = self.w - size - 10, 10
        px, pz = player_pos[0], player_pos[2]
        scale  = size / 44.0

        pygame.draw.rect(self._surf, (0, 0, 0, 110), (x, y, size, size), border_radius=5)

        for obj in scene.get("objects", []):
            t = obj.get("type")
            if t not in ("static", "floor", "enemy", "pickup"):
                continue
            p = obj.get("position", [0, 0, 0])
            s = obj.get("scale",    [1, 1, 1])
            mx = int(x + size/2 + (p[0]-px) * scale)
            my = int(y + size/2 + (p[2]-pz) * scale)
            if not (x < mx < x+size and y < my < y+size):
                continue
            color = {
                "static":  (100, 100, 100, 200),
                "floor":   (70,  70,  70,  150),
                "enemy":   (220, 40,  40,  220),
                "pickup":  (50,  220, 80,  220),
            }.get(t, (150, 150, 150, 180))
            w2 = max(2, int(s[0]*scale)); h2 = max(2, int(s[2]*scale))
            pygame.draw.rect(self._surf, color, (mx-w2//2, my-h2//2, w2, h2))

        pygame.draw.circle(self._surf, (80, 140, 255, 255),
                           (x + size//2, y + size//2), 4)
        pygame.draw.rect(self._surf, (180, 180, 180, 90),
                         (x, y, size, size), 1, border_radius=5)

    def message(self, text: str, color=(255, 255, 80), y_offset=80):
        txt = self._f_lg.render(text, True, color)
        self._surf.blit(txt, (self.w//2 - txt.get_width()//2, y_offset))

    def show_message(self, text: str, color=(255, 255, 80), duration: float = 3.0):
        """Flash a timed message (call once, shown automatically in flush)."""
        self._msg = [text, color, duration]

    def flush(self, delta: float = 0.016):
        """Handle timed message timeout, upload surface, draw overlay quad."""
        if self._msg:
            self.message(self._msg[0], self._msg[1])
            self._msg[2] -= delta
            if self._msg[2] <= 0:
                self._msg = None

        raw = pygame.image.tostring(self._surf, "RGBA", True)
        self._tex.write(raw)

        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        self._tex.use(0)
        self._prog["u_tex"].value = 0
        self._vao.render(moderngl.TRIANGLE_STRIP)
        self.ctx.disable(moderngl.BLEND)

    def resize(self, w: int, h: int):
        self.w, self.h = w, h
        self._surf = pygame.Surface((w, h), pygame.SRCALPHA)
        self._tex.release()
        self._tex = self.ctx.texture((w, h), 4)

    # ── internals ─────────────────────────────────────────────────────────

    def _build(self):
        prog = self.ctx.program(
            vertex_shader="""
#version 330
in vec2 in_pos; in vec2 in_uv;
out vec2 v_uv;
void main() { v_uv = in_uv; gl_Position = vec4(in_pos, 0.0, 1.0); }
""",
            fragment_shader="""
#version 330
in vec2 v_uv;
uniform sampler2D u_tex;
out vec4 f_color;
void main() { f_color = texture(u_tex, v_uv); }
""",
        )
        vbo = self.ctx.buffer(np.array([
            -1,-1, 0,0,  1,-1, 1,0,  -1,1, 0,1,  1,1, 1,1,
        ], dtype=np.float32).tobytes())
        vao = self.ctx.vertex_array(prog, [(vbo, "2f 2f", "in_pos", "in_uv")])
        return prog, vao
