"""Main game loop."""
import pygame
import moderngl

from .renderer      import Renderer
from .scene         import SceneLoader
from .physics       import Physics
from .audio         import AudioSystem
from .input_handler import InputHandler
from .scripting     import ScriptRunner


class Engine:
    W, H           = 1280, 720
    FPS_CAP        = 144
    MOUSE_SENS     = 0.12
    PLAYER_SPEED   = 5.0

    def __init__(self, game_dir):
        from pathlib import Path
        self.game_dir = Path(game_dir).resolve()
        self.current_scene: dict = {}
        self.running = False

        # Window + OpenGL
        pygame.init()
        pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        pygame.display.set_mode((self.W, self.H), flags)
        pygame.display.set_caption("SynthEngine")
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        self.ctx = moderngl.create_context()
        self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)

        self.renderer  = Renderer(self.ctx)
        self.audio     = AudioSystem(self.game_dir)
        self.physics   = Physics()
        self.input     = InputHandler()
        self.scripting = ScriptRunner()
        self.loader    = SceneLoader(self.game_dir)
        self.clock     = pygame.time.Clock()

    def run(self):
        manifest = self.loader.load_manifest()
        self._load_scene(manifest.get("start_scene"))
        self.running = True
        while self.running:
            dt = min(self.clock.tick(self.FPS_CAP) / 1000.0, 0.05)
            self._events()
            self._update(dt)
            self._render()
            pygame.display.flip()
            fps = self.clock.get_fps()
            pygame.display.set_caption(f"SynthEngine  {fps:.0f} fps")
        pygame.quit()

    # ── lifecycle ──────────────────────────────────────────────────────────

    def _load_scene(self, scene_path: str):
        if self.current_scene:
            self.audio.stop_music()
            self.renderer.clear_scene()
            self.physics.clear()

        self.current_scene = self.loader.load(scene_path)
        self.renderer.load_scene(self.current_scene)
        self.physics.load_scene(self.current_scene)
        self.scripting.load_scene(self.current_scene, self)

        music = self.current_scene.get("audio", {}).get("music")
        if music:
            self.audio.play_music(music)

        spawn = self.current_scene.get("spawn", [0, 1.5, 0])
        self.renderer.camera.set_position(spawn)

    def load_scene(self, path: str):
        """Public: called by scripts or triggers to transition scenes."""
        self._load_scene(path)

    # ── frame ─────────────────────────────────────────────────────────────

    def _events(self):
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                self.running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    self.running = False
                self.input.on_keydown(ev.key)
            elif ev.type == pygame.KEYUP:
                self.input.on_keyup(ev.key)
            elif ev.type == pygame.MOUSEMOTION:
                cam = self.renderer.camera
                cam.rotate(ev.rel[0] * self.MOUSE_SENS, ev.rel[1] * self.MOUSE_SENS)
            elif ev.type == pygame.MOUSEBUTTONDOWN:
                self.input.on_mousedown(ev.button)
            elif ev.type == pygame.MOUSEBUTTONUP:
                self.input.on_mouseup(ev.button)
            elif ev.type == pygame.VIDEORESIZE:
                w, h = ev.size
                self.ctx.viewport = (0, 0, w, h)
                self.renderer.camera.aspect = w / h

    def _update(self, dt: float):
        keys = pygame.key.get_pressed()
        cam  = self.renderer.camera
        dx   = (1 if keys[pygame.K_d] else 0) - (1 if keys[pygame.K_a] else 0)
        dz   = (1 if keys[pygame.K_s] else 0) - (1 if keys[pygame.K_w] else 0)
        if dx or dz:
            cam.move([dx, 0, dz], self.PLAYER_SPEED * dt)

        if keys[pygame.K_SPACE]:
            self.physics.jump(cam)

        self.physics.update(cam, dt)
        self.scripting.update(dt)
        self._check_triggers()

    def _render(self):
        surf = pygame.display.get_surface()
        w, h = surf.get_size()
        self.ctx.viewport = (0, 0, w, h)
        sky = self.current_scene.get("sky_color", [0.4, 0.6, 0.9])
        self.ctx.clear(*sky, 1.0)
        self.renderer.render()

    def _check_triggers(self):
        cam_p = self.renderer.camera.position
        for obj in self.current_scene.get("objects", []):
            if obj.get("type") != "trigger":
                continue
            pos   = obj.get("position", [0, 0, 0])
            scale = obj.get("scale",    [2, 2, 2])
            if (abs(cam_p[0]-pos[0]) < scale[0]/2 and
                abs(cam_p[1]-pos[1]) < scale[1]/2 and
                abs(cam_p[2]-pos[2]) < scale[2]/2):
                action = obj.get("props", {}).get("action")
                if action == "next_scene":
                    nxt = self.current_scene.get("next_scene")
                    if nxt:
                        self._load_scene(nxt)
                        return
                elif action == "win":
                    print("[SynthEngine] You Win!")
                    self.running = False
