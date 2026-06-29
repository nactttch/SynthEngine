"""Standard soldier enemy — uses EnemyAI state machine."""
from synth.api    import Script, Vec3
from synth.enemy_ai import EnemyAI


class Soldier(Script):
    health = 100.0
    speed  = 3.0
    damage = 12.0
    sight  = 14.0
    score  = 100

    def on_ready(self):
        self._ai = EnemyAI(
            speed        = self.speed,
            chase_speed  = self.speed * 1.6,
            sight_range  = self.sight,
            attack_range = 2.2,
            attack_damage= self.damage,
            attack_rate  = 0.9,
        )
        self._dead = False

    def on_update(self, delta: float):
        if self._dead:
            return
        attacked = self._ai.update(delta, self.node)
        if attacked:
            engine = self.node._engine
            dead   = engine.combat.take_damage(self.damage)
            if dead:
                engine.state = "dead"

    def on_hit(self, damage: float, source=None):
        if self._dead:
            return
        self.health -= damage
        if self.health <= 0:
            self._dead = True
            self._ai.die()
            engine = self.node._engine
            engine.combat.on_enemy_killed(self.score)
            engine.particles.explosion(self.node.position)
            self.node.destroy()
