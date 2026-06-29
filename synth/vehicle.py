"""Arcade vehicle physics for racing / driving games."""
import math


class Vehicle:
    """
    Arcade car physics. Attach to a Script and call update() each frame.

    Example:
        from synth.api import Script
        from synth.vehicle import Vehicle

        class Car(Script):
            max_speed    = 30.0
            acceleration = 20.0

            def on_ready(self):
                self._car = Vehicle(
                    max_speed    = self.max_speed,
                    acceleration = self.acceleration,
                )

            def on_update(self, delta):
                self._car.update(delta, self.node)
                # Sync camera behind car
                engine = self.node._engine
                engine.renderer.camera.follow(
                    self.node.position, self.node.rotation.y, dist=6, height=2.5
                )
    """

    def __init__(self, max_speed=25.0, acceleration=18.0, brake_force=35.0,
                 turn_speed=80.0, drift=0.88, gravity=18.0):
        self.max_speed    = max_speed
        self.acceleration = acceleration
        self.brake_force  = brake_force
        self.turn_speed   = turn_speed
        self.drift        = drift
        self.gravity      = gravity

        self.speed   = 0.0
        self.heading = 0.0    # degrees around Y
        self._vel_x  = 0.0
        self._vel_z  = 0.0
        self._vy     = 0.0
        self._grounded = True

    def update(self, delta: float, node):
        import pygame
        keys = pygame.key.get_pressed()

        throttle = (
            (1  if keys[pygame.K_w] or keys[pygame.K_UP]    else 0) -
            (1  if keys[pygame.K_s] or keys[pygame.K_DOWN]  else 0)
        )
        steer = (
            (1  if keys[pygame.K_d] or keys[pygame.K_RIGHT] else 0) -
            (1  if keys[pygame.K_a] or keys[pygame.K_LEFT]  else 0)
        )
        handbrake = keys[pygame.K_SPACE]

        # ── longitudinal ───────────────────────────────────────────────────
        if throttle != 0:
            self.speed += throttle * self.acceleration * delta
        else:
            drag = self.brake_force * 0.35
            self.speed = _drag(self.speed, drag, delta)

        if handbrake:
            self.speed = _drag(self.speed, self.brake_force, delta)

        self.speed = max(-self.max_speed * 0.5, min(self.max_speed, self.speed))

        # ── steering (proportional to speed) ──────────────────────────────
        speed_ratio = abs(self.speed) / max(1.0, self.max_speed)
        if abs(self.speed) > 0.3:
            self.heading += steer * self.turn_speed * speed_ratio * delta * (
                1.0 if self.speed > 0 else -1.0
            )

        # ── drift interpolation ───────────────────────────────────────────
        rad = math.radians(self.heading)
        target_vx =  math.sin(rad) * self.speed
        target_vz =  math.cos(rad) * self.speed

        slip = self.drift if not handbrake else self.drift * 0.5
        self._vel_x = self._vel_x * slip + target_vx * (1.0 - slip)
        self._vel_z = self._vel_z * slip + target_vz * (1.0 - slip)

        node.position.x += self._vel_x * delta
        node.position.z += self._vel_z * delta

        # ── gravity + ground snap ─────────────────────────────────────────
        self._vy -= self.gravity * delta
        node.position.y += self._vy * delta
        if node.position.y <= 0.5:
            node.position.y = 0.5
            self._vy = 0.0
            self._grounded = True

        node.rotation.y = self.heading

    @property
    def speed_kmh(self) -> float:
        return abs(self.speed) * 3.6

    @property
    def is_drifting(self) -> bool:
        intended_x = math.sin(math.radians(self.heading)) * self.speed
        return abs(self._vel_x - intended_x) > 2.0


def _drag(v: float, force: float, dt: float) -> float:
    if abs(v) < force * dt:
        return 0.0
    return v - math.copysign(force * dt, v)
