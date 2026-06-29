"""Minimal 3D math — Vec3 and Mat4 in numpy float32."""
import math
import numpy as np


class Vec3:
    __slots__ = ("x", "y", "z")

    def __init__(self, x=0.0, y=0.0, z=0.0):
        self.x, self.y, self.z = float(x), float(y), float(z)

    def __add__(self, o): return Vec3(self.x+o.x, self.y+o.y, self.z+o.z)
    def __sub__(self, o): return Vec3(self.x-o.x, self.y-o.y, self.z-o.z)
    def __mul__(self, s): return Vec3(self.x*s, self.y*s, self.z*s)
    def __rmul__(self, s): return self.__mul__(s)
    def __neg__(self):    return Vec3(-self.x, -self.y, -self.z)
    def __repr__(self):   return f"Vec3({self.x:.3f},{self.y:.3f},{self.z:.3f})"

    def length(self): return math.sqrt(self.x**2 + self.y**2 + self.z**2)

    def normalized(self):
        l = self.length()
        return Vec3(self.x/l, self.y/l, self.z/l) if l > 1e-9 else Vec3()

    def dot(self, o): return self.x*o.x + self.y*o.y + self.z*o.z

    def cross(self, o):
        return Vec3(
            self.y*o.z - self.z*o.y,
            self.z*o.x - self.x*o.z,
            self.x*o.y - self.y*o.x,
        )

    def np(self): return np.array([self.x, self.y, self.z], dtype=np.float32)

    @staticmethod
    def from_list(lst): return Vec3(*lst)


class Mat4:
    """Row-major 4x4 float32 matrix. Transposed before passing to OpenGL."""

    @staticmethod
    def identity() -> np.ndarray:
        return np.eye(4, dtype=np.float32)

    @staticmethod
    def perspective(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
        f = 1.0 / math.tan(math.radians(fov_deg) / 2)
        return np.array([
            [f/aspect, 0,  0,                             0],
            [0,        f,  0,                             0],
            [0,        0,  (far+near)/(near-far),  (2*far*near)/(near-far)],
            [0,        0, -1,                             0],
        ], dtype=np.float32)

    @staticmethod
    def look_at(eye: Vec3, target: Vec3, up: Vec3) -> np.ndarray:
        e = eye.np()
        f = (target - eye).normalized().np()
        r = np.cross(f, up.np()); r /= np.linalg.norm(r)
        u = np.cross(r, f)
        return np.array([
            [ r[0],  r[1],  r[2], -np.dot(r, e)],
            [ u[0],  u[1],  u[2], -np.dot(u, e)],
            [-f[0], -f[1], -f[2],  np.dot(f, e)],
            [    0,     0,     0,             1 ],
        ], dtype=np.float32)

    @staticmethod
    def translate(v: Vec3) -> np.ndarray:
        m = np.eye(4, dtype=np.float32)
        m[0, 3] = v.x; m[1, 3] = v.y; m[2, 3] = v.z
        return m

    @staticmethod
    def scale(v: Vec3) -> np.ndarray:
        return np.diag([v.x, v.y, v.z, 1.0]).astype(np.float32)

    @staticmethod
    def rotate_y(deg: float) -> np.ndarray:
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return np.array([
            [ c, 0, s, 0],
            [ 0, 1, 0, 0],
            [-s, 0, c, 0],
            [ 0, 0, 0, 1],
        ], dtype=np.float32)

    @staticmethod
    def rotate_x(deg: float) -> np.ndarray:
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return np.array([
            [1, 0,  0, 0],
            [0, c, -s, 0],
            [0, s,  c, 0],
            [0, 0,  0, 1],
        ], dtype=np.float32)

    @staticmethod
    def rotate_z(deg: float) -> np.ndarray:
        r = math.radians(deg)
        c, s = math.cos(r), math.sin(r)
        return np.array([
            [c, -s, 0, 0],
            [s,  c, 0, 0],
            [0,  0, 1, 0],
            [0,  0, 0, 1],
        ], dtype=np.float32)

    @staticmethod
    def gl_bytes(m: np.ndarray) -> bytes:
        """Column-major bytes for OpenGL uniforms."""
        return m.T.astype(np.float32).tobytes()
