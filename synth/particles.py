"""CPU particle system with GPU billboard rendering."""
import random
import math
import numpy as np
import moderngl
from .api.math3d import Mat4, Vec3


class ParticleSystem:
    MAX = 8192

    def __init__(self, ctx: moderngl.Context):
        self.ctx = ctx
        self._pool: list[list] = []   # [x,y,z, vx,vy,vz, r,g,b,a, size, life, max_life, gravity]
        self._prog = self._build()
        self._vbo  = ctx.buffer(reserve=self.MAX * 9 * 4)
        self._vao  = ctx.vertex_array(
            self._prog,
            [(self._vbo, "3f 4f 1f 1f", "in_pos", "in_color", "in_size", "in_life")],
        )

    # ── emitters ──────────────────────────────────────────────────────────

    def emit(self, pos: Vec3, count: int = 20, **kw):
        speed    = kw.get("speed",    4.0)
        spread   = kw.get("spread",   0.6)
        life     = kw.get("lifetime", 1.0)
        color    = kw.get("color",    [1.0, 0.5, 0.1, 1.0])
        size     = kw.get("size",     0.08)
        gravity  = kw.get("gravity",  True)
        emit_dir = kw.get("direction", None)

        for _ in range(min(count, self.MAX - len(self._pool))):
            s = speed * (0.5 + random.random())
            if emit_dir:
                vx = emit_dir.x + (random.random()-0.5)*spread
                vy = emit_dir.y + (random.random()-0.5)*spread
                vz = emit_dir.z + (random.random()-0.5)*spread
            else:
                vx = (random.random()-0.5)*spread*s
                vy = random.random()*s*0.7
                vz = (random.random()-0.5)*spread*s
            l  = life * (0.5 + random.random())
            self._pool.append([
                pos.x, pos.y, pos.z,
                vx, vy, vz,
                *color[:4],
                size * (0.7 + random.random()*0.6),
                l, l, 1.0 if gravity else 0.0,
            ])

    def explosion(self, pos: Vec3):
        self.emit(pos, 60, speed=9, spread=1.2, lifetime=0.9,
                  color=[1.0, 0.4, 0.0, 1.0], size=0.14)
        self.emit(pos, 40, speed=5, spread=1.0, lifetime=1.4,
                  color=[0.15, 0.15, 0.15, 0.8], size=0.20)
        self.emit(pos, 20, speed=3, spread=0.5, lifetime=0.6,
                  color=[1.0, 0.9, 0.3, 1.0], size=0.08)

    def blood(self, pos: Vec3):
        self.emit(pos, 30, speed=5, spread=0.9, lifetime=0.7,
                  color=[0.85, 0.05, 0.05, 1.0], size=0.07)

    def magic(self, pos: Vec3, color=None):
        c = color or [0.3, 0.5, 1.0, 0.9]
        self.emit(pos, 40, speed=3, spread=0.7, lifetime=1.0,
                  color=c, size=0.10, gravity=False)

    def muzzle_flash(self, pos: Vec3):
        self.emit(pos, 8, speed=2, spread=0.3, lifetime=0.08,
                  color=[1.0, 0.85, 0.4, 1.0], size=0.06, gravity=False)

    def sparks(self, pos: Vec3, normal: Vec3 = None):
        d = normal or Vec3(0, 1, 0)
        self.emit(pos, 15, speed=4, spread=0.8, lifetime=0.5,
                  color=[1.0, 0.8, 0.2, 1.0], size=0.04,
                  direction=d)

    def smoke(self, pos: Vec3):
        self.emit(pos, 5, speed=1, spread=0.3, lifetime=2.5,
                  color=[0.4, 0.4, 0.4, 0.5], size=0.25, gravity=False)

    # ── update / render ───────────────────────────────────────────────────

    def update(self, delta: float):
        alive = []
        for p in self._pool:
            p[11] -= delta
            if p[11] <= 0:
                continue
            p[0] += p[3] * delta
            p[1] += p[4] * delta
            p[2] += p[5] * delta
            if p[13] > 0:
                p[4] -= 12.0 * delta
            p[9] = p[11] / p[12]   # alpha fades with life
            alive.append(p)
        self._pool = alive

    def render(self, view: np.ndarray, proj: np.ndarray):
        if not self._pool:
            return
        data = []
        for p in self._pool:
            data.extend(p[0:3])           # pos
            data.extend(p[6:10])          # color rgba
            data.append(p[10])            # size
            data.append(p[11] / p[12])    # life ratio
        arr = np.array(data, dtype=np.float32)
        self._vbo.write(arr.tobytes())

        self.ctx.enable(moderngl.BLEND)
        self.ctx.disable(moderngl.DEPTH_TEST)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE

        self._prog["m_view"].write(Mat4.gl_bytes(view))
        self._prog["m_proj"].write(Mat4.gl_bytes(proj))
        self._vao.render(moderngl.POINTS, vertices=len(self._pool))

        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.disable(moderngl.BLEND)

    def _build(self) -> moderngl.Program:
        return self.ctx.program(
            vertex_shader="""
#version 330
in vec3 in_pos;
in vec4 in_color;
in float in_size;
in float in_life;
uniform mat4 m_view;
uniform mat4 m_proj;
out vec4 v_color;
void main() {
    v_color = in_color;
    vec4 clip = m_proj * m_view * vec4(in_pos, 1.0);
    gl_Position  = clip;
    gl_PointSize = in_size * 350.0 / max(clip.w, 0.1);
}
""",
            fragment_shader="""
#version 330
in vec4 v_color;
out vec4 f_color;
void main() {
    vec2 c = gl_PointCoord - 0.5;
    float d = dot(c, c);
    if (d > 0.25) discard;
    float a = v_color.a * (1.0 - d * 4.0);
    f_color = vec4(v_color.rgb, a);
}
""",
        )
