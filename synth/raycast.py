"""Ray-AABB intersection against scene objects."""
from .api.math3d import Vec3

_INF = float("inf")


def raycast(origin: Vec3, direction: Vec3, scene: dict, max_dist: float = 100.0,
            ignore_types: tuple = ("trigger", "pickup", "prop")):
    """
    Shoot a ray through the scene. Returns (hit, distance, node_id, normal).
    If no hit: (False, None, None, None).
    """
    d = direction.normalized()
    best_t, best_id, best_normal = max_dist, None, None

    for obj in scene.get("objects", []):
        if obj.get("type") in ignore_types:
            continue
        pos   = obj.get("position", [0, 0, 0])
        scale = obj.get("scale",    [1, 1, 1])
        min_b = [pos[i] - scale[i] * 0.5 for i in range(3)]
        max_b = [pos[i] + scale[i] * 0.5 for i in range(3)]

        t, normal = _slab(origin, d, min_b, max_b)
        if t is not None and 0.01 < t < best_t:
            best_t, best_id, best_normal = t, obj.get("id", ""), normal

    if best_id is not None:
        return True, best_t, best_id, best_normal
    return False, None, None, None


def _slab(o: Vec3, d: Vec3, mn: list, mx: list):
    ox, oy, oz = o.x, o.y, o.z
    dx, dy, dz = d.x, d.y, d.z

    def _t(a, b, c):
        return (a - b) / c if abs(c) > 1e-12 else (_INF if a > b else -_INF)

    t1x, t2x = sorted([_t(mn[0], ox, dx), _t(mx[0], ox, dx)])
    t1y, t2y = sorted([_t(mn[1], oy, dy), _t(mx[1], oy, dy)])
    t1z, t2z = sorted([_t(mn[2], oz, dz), _t(mx[2], oz, dz)])

    tmin = max(t1x, t1y, t1z)
    tmax = min(t2x, t2y, t2z)

    if tmax < max(0.0, tmin):
        return None, None

    t = tmin if tmin > 0.01 else tmax
    if t <= 0.01:
        return None, None

    # Hit normal: which face?
    hit = [o.x + d.x*t, o.y + d.y*t, o.z + d.z*t]
    eps = 1e-3
    if   abs(hit[0] - mn[0]) < eps: normal = Vec3(-1,  0,  0)
    elif abs(hit[0] - mx[0]) < eps: normal = Vec3( 1,  0,  0)
    elif abs(hit[1] - mn[1]) < eps: normal = Vec3( 0, -1,  0)
    elif abs(hit[1] - mx[1]) < eps: normal = Vec3( 0,  1,  0)
    elif abs(hit[2] - mn[2]) < eps: normal = Vec3( 0,  0, -1)
    else:                            normal = Vec3( 0,  0,  1)

    return t, normal
