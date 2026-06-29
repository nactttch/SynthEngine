"""Reusable enemy AI state machine. Use inside any Script."""
import math
from enum import Enum
from .api.math3d import Vec3


class State(Enum):
    IDLE    = "idle"
    PATROL  = "patrol"
    ALERT   = "alert"
    CHASE   = "chase"
    ATTACK  = "attack"
    DEAD    = "dead"


class EnemyAI:
    """
    Drop-in AI component for any enemy Script.

    Example:
        from synth.api import Script
        from synth.enemy_ai import EnemyAI

        class Soldier(Script):
            health     = 100.0
            speed      = 3.0
            sight      = 14.0
            damage     = 10.0
            attack_rate= 1.0

            def on_ready(self):
                self._ai = EnemyAI(
                    speed=self.speed, chase_speed=self.speed*1.5,
                    sight_range=self.sight, attack_damage=self.damage,
                    attack_rate=self.attack_rate,
                    patrol_path=[Vec3(-5,0.9,0), Vec3(5,0.9,0)],
                )
                self.node.play_sound("assets/sounds/idle.wav", loop=True)

            def on_update(self, delta):
                attacked = self._ai.update(delta, self.node)
                if attacked:
                    pass  # deal damage to player via game_manager

            def on_hit(self, damage, source=None):
                self.health -= damage
                self.node.play_sound("assets/sounds/hurt.wav")
                if self.health <= 0:
                    self._ai.die()
                    self.node.play_sound("assets/sounds/death.wav")
                    self.node.destroy()
    """

    def __init__(self, speed=3.0, chase_speed=5.0, sight_range=12.0,
                 attack_range=2.0, attack_damage=15.0, attack_rate=1.0,
                 patrol_path: list = None):
        self.speed         = speed
        self.chase_speed   = chase_speed
        self.sight_range   = sight_range
        self.attack_range  = attack_range
        self.attack_damage = attack_damage
        self.attack_rate   = attack_rate
        self.patrol_path   = patrol_path or []

        self.state         = State.IDLE
        self._patrol_idx   = 0
        self._attack_t     = 0.0
        self._alert_t      = 0.0

    # ── called every frame ─────────────────────────────────────────────────

    def update(self, delta: float, node) -> bool:
        """Returns True the moment an attack lands (caller should deal damage)."""
        if self.state == State.DEAD:
            return False

        player = node.find_type("player")
        if player is None:
            return False

        dist = (player.position - node.position).length()
        sees = dist < self.sight_range

        if self.state == State.IDLE:
            self.state = State.PATROL if self.patrol_path else (State.CHASE if sees else State.IDLE)

        elif self.state == State.PATROL:
            if sees:
                self.state = State.CHASE
            elif self.patrol_path:
                target = self.patrol_path[self._patrol_idx]
                self._step(node, target, self.speed, delta)
                if (target - node.position).length() < 0.6:
                    self._patrol_idx = (self._patrol_idx + 1) % len(self.patrol_path)

        elif self.state == State.CHASE:
            if not sees:
                self._alert_t += delta
                if self._alert_t > 3.0:
                    self._alert_t = 0.0
                    self.state = State.PATROL if self.patrol_path else State.IDLE
            else:
                self._alert_t = 0.0
                if dist <= self.attack_range:
                    self.state = State.ATTACK
                else:
                    self._step(node, player.position, self.chase_speed, delta)

        elif self.state == State.ATTACK:
            if dist > self.attack_range * 1.6:
                self.state = State.CHASE
            else:
                self._attack_t += delta
                if self._attack_t >= 1.0 / max(0.1, self.attack_rate):
                    self._attack_t = 0.0
                    return True  # attack landed

        # Face player when aggressive
        if self.state in (State.CHASE, State.ATTACK) and player:
            dx = player.position.x - node.position.x
            dz = player.position.z - node.position.z
            if abs(dx) > 0.01 or abs(dz) > 0.01:
                node.rotation.y = math.degrees(math.atan2(dx, dz))

        return False

    def die(self):
        self.state = State.DEAD

    @property
    def is_dead(self) -> bool:
        return self.state == State.DEAD

    # ── helpers ───────────────────────────────────────────────────────────

    def _step(self, node, target: Vec3, speed: float, delta: float):
        direction = target - node.position
        direction.y = 0
        if direction.length() > 0.1:
            node.position += direction.normalized() * speed * delta
