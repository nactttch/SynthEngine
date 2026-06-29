"""OpenGL renderer — camera, mesh loading, draw loop."""
from __future__ import annotations
import math
from pathlib import Path

import numpy as np
import moderngl

from .api.math3d import Vec3, Mat4


# ── Camera ─────────────────────────────────────────────────────────────────

class Camera:
    FOV    = 75.0
    NEAR   = 0.05
    FAR    = 600.0

    def __init__(self, aspect: float = 16/9):
        self.position = np.array([0.0, 1.5, 0.0], dtype=np.float32)
        self.yaw      = 0.0    # degrees, horizontal
        self.pitch    = 0.0    # degrees, vertical
        self.aspect   = aspect

    def set_position(self, pos: list | np.ndarray):
        self.position = np.array(pos, dtype=np.float32)

    def rotate(self, dx: float, dy: float):
        self.yaw  = (self.yaw + dx) % 360.0
        self.pitch = max(-89.0, min(89.0, self.pitch - dy))

    @property
    def front(self) -> np.ndarray:
        yr, pr = math.radians(self.yaw), math.radians(self.pitch)
        return np.array([
            math.cos(pr) * math.sin(yr),
            math.sin(pr),
           -math.cos(pr) * math.cos(yr),
        ], dtype=np.float32)

    @property
    def right(self) -> np.ndarray:
        r = np.cross(self.front, np.array([0, 1, 0], dtype=np.float32))
        n = np.linalg.norm(r)
        return r / n if n > 1e-9 else np.array([1, 0, 0], dtype=np.float32)

    def move(self, direction: list[int], speed: float):
        f = self.front.copy(); f[1] = 0
        n = np.linalg.norm(f)
        if n > 1e-9: f /= n
        self.position += (f * -direction[2] + self.right * direction[0]) * speed

    def view_matrix(self) -> np.ndarray:
        eye    = self.position
        target = eye + self.front
        up     = np.array([0, 1, 0], dtype=np.float32)
        f = (target - eye); f /= np.linalg.norm(f)
        r = np.cross(f, up); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        return np.array([
            [ r[0],  r[1],  r[2], -np.dot(r, eye)],
            [ u[0],  u[1],  u[2], -np.dot(u, eye)],
            [-f[0], -f[1], -f[2],  np.dot(f, eye)],
            [    0,     0,     0,               1 ],
        ], dtype=np.float32)

    def proj_matrix(self) -> np.ndarray:
        return Mat4.perspective(self.FOV, self.aspect, self.NEAR, self.FAR)


# ── Mesh handle ─────────────────────────────────────────────────────────────

class MeshHandle:
    def __init__(self, vao: moderngl.VertexArray, index_count: int,
                 position: Vec3, rotation: Vec3, scale: Vec3,
                 color: list[float], texture=None):
        self.vao         = vao
        self.index_count = index_count
        self.position    = position
        self.rotation    = rotation
        self.scale       = scale
        self.color       = color
        self.texture     = texture
        self.visible     = True

    def model_matrix(self) -> np.ndarray:
        T  = Mat4.translate(self.position)
        Ry = Mat4.rotate_y(self.rotation.y)
        Rx = Mat4.rotate_x(self.rotation.x)
        Rz = Mat4.rotate_z(self.rotation.z)
        S  = Mat4.scale(self.scale)
        return T @ Ry @ Rx @ Rz @ S


# ── Renderer ────────────────────────────────────────────────────────────────

class Renderer:
    def __init__(self, ctx: moderngl.Context):
        self.ctx      = ctx
        self.camera   = Camera()
        self._meshes: dict[str, MeshHandle] = {}
        self._program = self._build_program()
        self._scene: dict = {}

    # ── scene lifecycle ────────────────────────────────────────────────────

    def load_scene(self, scene: dict):
        self._scene = scene
        game_dir = Path(scene.get("_dir", "."))
        w, h = 1280, 720
        self.camera.aspect = w / h

        for obj in scene.get("objects", []):
            oid   = obj.get("id", "")
            color = obj.get("color", [0.7, 0.7, 0.7])
            pos   = Vec3(*obj.get("position", [0, 0, 0]))
            rot   = Vec3(*obj.get("rotation", [0, 0, 0]))
            scl   = Vec3(*obj.get("scale",    [1, 1, 1]))

            mesh_rel = obj.get("mesh")
            if mesh_rel:
                mesh_path = game_dir / mesh_rel
                vao, cnt, tex = self._load_mesh(mesh_path, game_dir)
            else:
                # Default primitive box
                vao, cnt = self._box_vao()
                tex = None

            self._meshes[oid] = MeshHandle(vao, cnt, pos, rot, scl, color, tex)

    def clear_scene(self):
        for h in self._meshes.values():
            h.vao.release()
        self._meshes.clear()

    def remove_mesh(self, oid: str):
        h = self._meshes.pop(oid, None)
        if h:
            h.vao.release()

    def set_position(self, oid: str, pos: Vec3):
        if oid in self._meshes:
            self._meshes[oid].position = pos

    # ── render ────────────────────────────────────────────────────────────

    def render(self):
        prog = self._program
        cam  = self.camera

        view = cam.view_matrix()
        proj = cam.proj_matrix()
        prog["m_view"].write(Mat4.gl_bytes(view))
        prog["m_proj"].write(Mat4.gl_bytes(proj))
        prog["u_cam_pos"].value = tuple(cam.position)

        lighting = self._scene.get("lighting", {})
        ld = lighting.get("directional", {})
        raw_dir = ld.get("direction", [0.5, -1.0, 0.3])
        prog["u_light_dir"].value   = tuple(raw_dir)
        prog["u_light_color"].value = tuple(ld.get("color", [1.0, 0.95, 0.8]))
        prog["u_ambient"].value     = tuple(lighting.get("ambient", [0.25, 0.25, 0.3]))

        fog_cfg = self._scene.get("fog", {})
        fog_on  = self._scene.get("fog_enabled", False) or fog_cfg.get("enabled", False)
        prog["u_fog"].value       = fog_on
        prog["u_fog_start"].value = float(fog_cfg.get("start", 20))
        prog["u_fog_end"].value   = float(fog_cfg.get("end",   80))
        fc = fog_cfg.get("color", self._scene.get("sky_color", [0.5, 0.6, 0.7]))
        prog["u_fog_color"].value = tuple(fc)

        for handle in self._meshes.values():
            if not handle.visible:
                continue
            prog["m_model"].write(Mat4.gl_bytes(handle.model_matrix()))
            prog["u_color"].value = tuple(handle.color[:3])
            if handle.texture:
                handle.texture.use(0)
                prog["u_has_texture"].value = True
                prog["u_texture"].value     = 0
            else:
                prog["u_has_texture"].value = False
            handle.vao.render(moderngl.TRIANGLES)

    # ── internals ─────────────────────────────────────────────────────────

    def _build_program(self) -> moderngl.Program:
        shader_dir = Path(__file__).parent / "shaders"
        vert = (shader_dir / "mesh.vert").read_text()
        frag = (shader_dir / "mesh.frag").read_text()
        return self.ctx.program(vertex_shader=vert, fragment_shader=frag)

    def _load_mesh(self, path: Path, game_dir: Path):
        try:
            import trimesh
            raw = trimesh.load(str(path), force="mesh")
            if isinstance(raw, trimesh.Scene):
                meshes = [g for g in raw.geometry.values()]
                raw = trimesh.util.concatenate(meshes) if len(meshes) > 1 else meshes[0]

            verts   = np.array(raw.vertices,       dtype=np.float32)
            norms   = np.array(raw.vertex_normals,  dtype=np.float32)
            indices = np.array(raw.faces,           dtype=np.uint32)

            # UVs
            if hasattr(raw.visual, "uv") and raw.visual.uv is not None:
                uvs = np.array(raw.visual.uv, dtype=np.float32)
            else:
                uvs = np.zeros((len(verts), 2), dtype=np.float32)

            # Texture
            texture = None
            if hasattr(raw.visual, "material"):
                mat = raw.visual.material
                img = getattr(mat, "baseColorTexture", None) or getattr(mat, "image", None)
                if img is not None:
                    texture = self._upload_texture(img)

            vao, cnt = self._upload_mesh(verts, norms, uvs, indices)
            return vao, cnt, texture

        except Exception as e:
            print(f"[renderer] mesh load failed: {path.name} — {e}")
            vao, cnt = self._box_vao()
            return vao, cnt, None

    def _upload_mesh(self, verts, norms, uvs, indices):
        data = np.hstack([verts, norms, uvs]).astype(np.float32)
        vbo  = self.ctx.buffer(data.tobytes())
        ibo  = self.ctx.buffer(indices.tobytes())
        vao  = self.ctx.vertex_array(
            self._program,
            [(vbo, "3f 3f 2f", "in_position", "in_normal", "in_texcoord")],
            ibo,
        )
        return vao, len(indices) * 3

    def _upload_texture(self, img) -> moderngl.Texture | None:
        try:
            import PIL.Image
            if not isinstance(img, PIL.Image.Image):
                return None
            img = img.convert("RGBA")
            tex = self.ctx.texture(img.size, 4, img.tobytes())
            tex.filter = (moderngl.LINEAR_MIPMAP_LINEAR, moderngl.LINEAR)
            tex.build_mipmaps()
            return tex
        except Exception:
            return None

    def _box_vao(self):
        """Unit box used when no mesh file is present."""
        v = np.array([
            # pos              normal          uv
            -0.5,-0.5,-0.5,  0, 0,-1,  0,0,
             0.5,-0.5,-0.5,  0, 0,-1,  1,0,
             0.5, 0.5,-0.5,  0, 0,-1,  1,1,
            -0.5, 0.5,-0.5,  0, 0,-1,  0,1,

            -0.5,-0.5, 0.5,  0, 0, 1,  0,0,
             0.5,-0.5, 0.5,  0, 0, 1,  1,0,
             0.5, 0.5, 0.5,  0, 0, 1,  1,1,
            -0.5, 0.5, 0.5,  0, 0, 1,  0,1,

            -0.5,-0.5,-0.5, -1, 0, 0,  0,0,
            -0.5, 0.5,-0.5, -1, 0, 0,  1,0,
            -0.5, 0.5, 0.5, -1, 0, 0,  1,1,
            -0.5,-0.5, 0.5, -1, 0, 0,  0,1,

             0.5,-0.5,-0.5,  1, 0, 0,  0,0,
             0.5, 0.5,-0.5,  1, 0, 0,  1,0,
             0.5, 0.5, 0.5,  1, 0, 0,  1,1,
             0.5,-0.5, 0.5,  1, 0, 0,  0,1,

            -0.5,-0.5,-0.5,  0,-1, 0,  0,0,
             0.5,-0.5,-0.5,  0,-1, 0,  1,0,
             0.5,-0.5, 0.5,  0,-1, 0,  1,1,
            -0.5,-0.5, 0.5,  0,-1, 0,  0,1,

            -0.5, 0.5,-0.5,  0, 1, 0,  0,0,
             0.5, 0.5,-0.5,  0, 1, 0,  1,0,
             0.5, 0.5, 0.5,  0, 1, 0,  1,1,
            -0.5, 0.5, 0.5,  0, 1, 0,  0,1,
        ], dtype=np.float32)
        i = np.array([
            0,1,2, 2,3,0, 4,5,6, 6,7,4, 8,9,10, 10,11,8,
            12,13,14, 14,15,12, 16,17,18, 18,19,16, 20,21,22, 22,23,20,
        ], dtype=np.uint32)
        vbo = self.ctx.buffer(v.tobytes())
        ibo = self.ctx.buffer(i.tobytes())
        vao = self.ctx.vertex_array(
            self._program,
            [(vbo, "3f 3f 2f", "in_position", "in_normal", "in_texcoord")],
            ibo,
        )
        return vao, len(i)
