"""Boss enemy — high health, enrages below 30% HP."""
from synth.api    import Script, Vec3
from synth.enemy_ai import EnemyAI


class Boss(Script):
    health = 500.0
    speed  = 2.5
    damage = 35.0
    sight  = 20.0
    score  = 1000

    def on_ready(self):
        self._ai = EnemyAI(
            speed        = self.speed,
            chase_speed  = self.speed * 1.4,
            sight_range  = self.sight,
            attack_range = 3.0,
            attack_damage= self.damage,
            attack_rate  = 0.7,
        )
        self._max_health = self.health
        self._enraged    = False
        self._dead       = False

    def on_update(self, delta: float):
        if self._dead:
            return

        # Enrage at 30% HP
        if not self._enraged and self.health < self._max_health * 0.3:
            self._enraged = True
            self._ai.chase_speed  *= 2.0
            self._ai.attack_rate  *= 2.0
            self._ai.attack_damage *= 1.5
            engine = self.node._engine
            engine.hud.show_message("BOSS ENRAGED!", (255, 60, 60), duration=3.0)

        attacked = self._ai.update(delta, self.node)
        if attacked:
            engine = self.node._engine
            dead   = engine.combat.take_damage(self._ai.attack_damage)
            if dead:
                engine.state = "dead"

        # Pulse scale while enraged
        if self._enraged:
            import math
            t = self.node._engine._timer
            s = 1.4 + math.sin(t * 6) * 0.08
            self.node.scale = Vec3(s, 3.0, s)

    def on_hit(self, damage: float, source=None):
        if self._dead:
            return
        self.health -= damage
        engine = self.node._engine
        # Shrug off some damage when enraged
        if self._enraged:
            damage *= 0.6

        if self.health <= 0:
            self._dead = True
            self._ai.die()
            engine.combat.on_enemy_killed(self.score)
            engine.particles.explosion(self.node.position)
            engine.particles.explosion(Vec3(
                self.node.position.x + 1,
                self.node.position.y + 1,
                self.node.position.z,
            ))
            self.node.destroy()
            engine.state = "win"
