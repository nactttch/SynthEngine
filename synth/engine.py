"""SynthEngine main loop — wires all systems together."""
import pygame
import moderngl

from .renderer      import Renderer
from .scene         import SceneLoader
from .physics       import Physics
from .audio         import AudioSystem
from .input_handler import InputHandler
from .scripting     import ScriptRunner
from .combat        import CombatSystem
from .particles     import ParticleSystem
from .hud           import HUD
from .api.math3d    import Vec3


class GameState:
    PLAYING  = "playing"
    DEAD     = "dead"
    WIN      = "win"
    MENU     = "menu"


class Engine:
    W, H        = 1280, 720
    FPS_CAP     = 144
    MOUSE_SENS  = 0.12
    PLAYER_SPD  = 5.0

    def __init__(self, game_dir):
        from pathlib import Path
        self.game_dir      = Path(game_dir).resolve()
        self.current_scene: dict = {}
        self.state         = GameState.PLAYING
        self.running       = False

        # ── window + context ──────────────────────────────────────────────
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        pygame.display.set_mode((self.W, self.H), flags)
        pygame.display.set_caption("SynthEngine")
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)

        # ── systems ───────────────────────────────────────────────────────
        self.renderer  = Renderer(self.ctx)
        self.audio     = AudioSystem(self.game_dir)
        self.physics   = Physics()
        self.input     = InputHandler()
        self.scripting = ScriptRunner()
        self.combat    = CombatSystem(self)
        self.particles = ParticleSystem(self.ctx)
        self.hud       = HUD(self.ctx, self.W, self.H)
        self.loader    = SceneLoader(self.game_dir)
        self.clock     = pygame.time.Clock()
        self._timer    = 0.0

    # ── entry point ───────────────────────────────────────────────────────

    def run(self):
        manifest = self.loader.load_manifest()
        title    = manifest.get("title", "SynthEngine Game")
        pygame.display.set_caption(title)

        # Auto-equip weapons from manifest
        for w in manifest.get("weapons", ["pistol"]):
            self.combat.add_weapon(w)

        self._load_scene(manifest.get("start_scene"))
        self.running = True

        while self.running:
            dt = min(self.clock.tick(self.FPS_CAP) / 1000.0, 0.05)
            self._events(dt)
            if self.state == GameState.PLAYING:
                self._update(dt)
            self._render(dt)
            pygame.display.flip()
            fps = self.clock.get_fps()
            pygame.display.set_caption(f"{title}  — {fps:.0f} fps")

        pygame.quit()

    # ── scene lifecycle ───────────────────────────────────────────────────

    def _load_scene(self, scene_path: str):
        if self.current_scene:
            self.audio.stop_music()
            self.renderer.clear_scene()
            self.physics.clear()

        self.current_scene = self.loader.load(scene_path)
        self.renderer.load_scene(self.current_scene)
        self.physics.load_scene(self.current_scene)
        self.scripting.load_scene(self.current_scene, self)
        self._timer = 0.0

        music = self.current_scene.get("audio", {}).get("music")
        if music:
            self.audio.play_music(music)

        self.renderer.camera.set_position(
            self.current_scene.get("spawn", [0, 1.8, 0])
        )

    def load_scene(self, path: str):
        """Public API — called by scripts or triggers."""
        self._load_scene(path)

    # ── event handling ────────────────────────────────────────────────────

    def _events(self, dt: float):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                elif ev.key == pygame.K_r and self.state == GameState.DEAD:
                    self._respawn()
                elif ev.key == pygame.K_q:
                    # weapon cycle
                    self.combat.switch_weapon(1)
                self.input.on_keydown(ev.key)
            elif ev.type == pygame.KEYUP:
                self.input.on_keyup(ev.key)
            elif ev.type == pygame.MOUSEMOTION:
                if self.state == GameState.PLAYING:
                    cam = self.renderer.camera
                    cam.rotate(ev.rel[0] * self.MOUSE_SENS,
                               ev.rel[1] * self.MOUSE_SENS)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                self.input.on_mousedown(ev.button)
                if ev.button == 1 and self.state == GameState.PLAYING:
                    self._shoot()
                elif ev.button == 4:
                    self.combat.switch_weapon(-1)
                elif ev.button == 5:
                    self.combat.switch_weapon(1)
            elif ev.type == pygame.MOUSEBUTTONUP:
                self.input.on_mouseup(ev.button)
            elif ev.type == pygame.VIDEORESIZE:
                w, h = ev.size
                self.ctx.viewport     = (0, 0, w, h)
                self.renderer.camera.aspect = w / h
                self.hud.resize(w, h)

    # ── update ────────────────────────────────────────────────────────────

    def _update(self, dt: float):
        self._timer += dt
        keys = pygame.key.get_pressed()
        cam  = self.renderer.camera

        # Player movement
        dx = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
        dz = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
        if dx or dz:
            cam.move([dx, 0, dz], self.PLAYER_SPD * dt)

        # Reload
        if keys[pygame.K_r]:
            self.combat.reload()

        # Jump
        if keys[pygame.K_SPACE]:
            self.physics.jump(cam)

        self.physics.update(cam, dt)
        self.combat.update(dt)
        self.particles.update(dt)
        self.scripting.update(dt)
        self._check_triggers()
        self._check_pickups()

    def _shoot(self):
        hits = self.combat.try_shoot()
        if hits:
            cam = self.renderer.camera
            fwd = Vec3(*cam.front)
            mf_pos = Vec3(
                cam.position[0] + fwd.x * 0.5,
                cam.position[1] + fwd.y * 0.5,
                cam.position[2] + fwd.z * 0.5,
            )
            self.particles.muzzle_flash(mf_pos)
            for node_id, dmg, hit_pos in hits:
                if hit_pos:
                    self.particles.blood(hit_pos)
        else:
            # No hit — still show muzzle flash if we fired
            if self.combat.current and self.combat._cooldown < 0.05:
                cam = self.renderer.camera
                fwd = Vec3(*cam.front)
                self.particles.muzzle_flash(Vec3(
                    cam.position[0] + fwd.x * 0.5,
                    cam.position[1] + fwd.y * 0.5 - 0.1,
                    cam.position[2] + fwd.z * 0.5,
                ))

    def _respawn(self):
        self.combat.player_health = self.combat.player_max_health
        self.state = GameState.PLAYING
        spawn = self.current_scene.get("spawn", [0, 1.8, 0])
        self.renderer.camera.set_position(spawn)

    # ── triggers / pickups ────────────────────────────────────────────────

    def _check_triggers(self):
        cam_p = self.renderer.camera.position
        for obj in self.current_scene.get("objects", []):
            if obj.get("type") != "trigger":
                continue
            pos   = obj.get("position", [0, 0, 0])
            scale = obj.get("scale",    [2, 2, 2])
            if (abs(cam_p[0]-pos[0]) < scale[0]*0.5 and
                abs(cam_p[1]-pos[1]) < scale[1]*0.5 and
                abs(cam_p[2]-pos[2]) < scale[2]*0.5):
                action = obj.get("props", {}).get("action", "")
                if action == "next_scene":
                    nxt = self.current_scene.get("next_scene")
                    if nxt:
                        self._load_scene(nxt)
                        return
                elif action == "win":
                    self.state = GameState.WIN
                elif action == "kill":
                    self._take_damage(999)

    def _check_pickups(self):
        cam_p = self.renderer.camera.position
        to_remove = []
        for obj in self.current_scene.get("objects", []):
            if obj.get("type") != "pickup":
                continue
            pos = obj.get("position", [0, 0, 0])
            if (abs(cam_p[0]-pos[0]) < 1.2 and
                abs(cam_p[1]-pos[1]) < 1.8 and
                abs(cam_p[2]-pos[2]) < 1.2):
                props = obj.get("props", {})
                if "weapon" in props:
                    self.combat.pickup_weapon(props["weapon"], props.get("ammo"))
                    self.hud.show_message(f"Picked up {props['weapon'].title()}!")
                if "ammo" in props and "weapon" not in props:
                    self.combat.pickup_ammo(props["ammo"])
                if "health" in props:
                    self.combat.heal(props["health"])
                    self.hud.show_message(f"+{props['health']} HP")
                pos_v = Vec3(*pos)
                self.particles.magic(pos_v, [0.3, 1.0, 0.4, 0.8])
                self.audio.play_sfx(props.get("sound", ""))
                to_remove.append(obj.get("id"))

        for oid in to_remove:
            self.renderer.remove_mesh(oid)
            self.current_scene["objects"] = [
                o for o in self.current_scene["objects"] if o.get("id") != oid
            ]

    def _take_damage(self, amount: float):
        dead = self.combat.take_damage(amount)
        if dead:
            self.state = GameState.DEAD

    # ── render ────────────────────────────────────────────────────────────

    def _render(self, dt: float):
        surf = pygame.display.get_surface()
        w, h = surf.get_size()
        self.ctx.viewport = (0, 0, w, h)

        sky = self.current_scene.get("sky_color", [0.4, 0.6, 0.9])
        self.ctx.clear(*sky, 1.0)

        cam  = self.renderer.camera
        view = cam.view_matrix()
        proj = cam.proj_matrix()

        self.renderer.render()
        self.particles.render(view, proj)
        self._render_hud(dt)

    def _render_hud(self, dt: float):
        hud = self.hud
        hud.begin()

        if self.state == GameState.PLAYING:
            hud.crosshair("cross")
            hud.health_bar(self.combat.player_health, self.combat.player_max_health)
            ammo, reserve = self.combat.ammo_display
            weapon_name = self.combat.current.name if self.combat.current else ""
            hud.ammo_counter(ammo, reserve, weapon_name)
            hud.score_display(self.combat.kills, self.combat.score)
            hud.minimap(self.current_scene, self.renderer.camera.position)
            if self.combat.is_reloading:
                hud.message("RELOADING...", (200, 200, 100), y_offset=self.hud.h // 2 - 30)

        elif self.state == GameState.DEAD:
            hud.message("YOU DIED", (255, 40, 40), y_offset=self.hud.h // 2 - 40)
            hud.message("Press R to respawn", (200, 200, 200),
                        y_offset=self.hud.h // 2 + 20)

        elif self.state == GameState.WIN:
            hud.message("MISSION COMPLETE!", (80, 255, 120), y_offset=self.hud.h // 2 - 40)
            hud.message(f"Kills: {self.combat.kills}   Score: {self.combat.score}",
                        (220, 220, 220), y_offset=self.hud.h // 2 + 20)

        hud.flush(dt)
