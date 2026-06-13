from __future__ import annotations

import math
import os
import random
import sys
from array import array
from dataclasses import dataclass

import pygame


SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700
FPS = 60
SAMPLE_RATE = 44100
DEFAULT_WINDOW_SCALE = 1.35
WINDOW_WIDTH = int(SCREEN_WIDTH * DEFAULT_WINDOW_SCALE)
WINDOW_HEIGHT = int(SCREEN_HEIGHT * DEFAULT_WINDOW_SCALE)
MIN_WINDOW_WIDTH = SCREEN_WIDTH
MIN_WINDOW_HEIGHT = SCREEN_HEIGHT
LINUX_AUDIO_DRIVERS = ("pulseaudio", "pipewire", "alsa")
WINDOWS_AUDIO_DRIVERS = ("directsound", "wasapi")
MAC_AUDIO_DRIVERS = ("coreaudio",)

LANE_COUNT = 4
ROAD_WIDTH = 520
ROAD_LEFT = (SCREEN_WIDTH - ROAD_WIDTH) // 2
ROAD_RIGHT = ROAD_LEFT + ROAD_WIDTH
ROAD_TOP = 42
ROAD_BOTTOM = SCREEN_HEIGHT - 24
ROAD_HEIGHT = ROAD_BOTTOM - ROAD_TOP
LANE_WIDTH = ROAD_WIDTH // LANE_COUNT

PLAYER_SPEED = 365.0
DIVIDER_NUDGE_SPEED = 72.0
DIVIDER_NUDGE_ZONE = 9
HAZARD_LANE_CHANGE_SPEED = 185.0
CAR_LANE_CHANGE_CHANCE = 0.28
CAR_LANE_CHANGE_COOLDOWN = 1.15
SCROLL_SPEED_START = 240.0
SCROLL_SPEED_MAX = 520.0
SCROLL_ACCELERATION = 8.0

WHITE = (255, 255, 255)
BLACK = (20, 26, 32)
SEA_BLUE = (99, 200, 224)
SEA_DARK = (58, 162, 196)
ROAD_BLUE = (40, 153, 215)
ROAD_BLUE_DARK = (30, 119, 183)
LANE_WHITE = (225, 246, 255)
RAIL_RED = (218, 48, 40)
YELLOW = (250, 217, 77)
ORANGE = (246, 132, 45)
GREEN = (53, 182, 109)
PINK = (239, 93, 142)
PURPLE = (133, 86, 212)
TEXT_NAVY = (26, 51, 78)


@dataclass
class PlayerCar:
    rect: pygame.Rect
    lane: int
    speed: float
    x: float
    y: float


@dataclass
class Hazard:
    rect: pygame.Rect
    kind: str
    lane: int
    speed: float
    surface: pygame.Surface
    x: float
    y: float
    target_lane: int | None = None
    lane_change_cooldown: float = 0.0
    points: int = 10
    scored: bool = False


@dataclass
class ScorePopup:
    text: str
    x: float
    y: float
    timer: float


class Assets:
    def __init__(self) -> None:
        self.player_car = create_player_car_surface()
        self.enemy_cars = [
            create_car_surface((236, 82, 66), (157, 41, 34)),
            create_car_surface((247, 199, 62), (187, 132, 18)),
            create_car_surface((248, 248, 240), (120, 125, 130)),
            create_car_surface((128, 90, 214), (74, 53, 143)),
        ]
        self.hazards = {
            "car": self.enemy_cars,
            "cone": [create_cone_surface()],
            "work_sign": [create_work_sign_surface()],
            "barrel": [create_barrel_surface()],
            "crate": [create_crate_surface()],
        }


class SoundBank:
    def __init__(self) -> None:
        self.enabled = False
        self.status_message = "Audio ready"
        self.driver_name = "unknown"
        self.failure_details: list[str] = []
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.engine_channel: pygame.mixer.Channel | None = None

        if not self.initialize_mixer():
            self.status_message = self.create_failure_message()
            print(self.status_message)
            return

        try:
            self.enabled = True
            pygame.mixer.set_num_channels(12)
            self.sounds = {
                "start": create_note_sound([(392, 0.08), (523, 0.1), (784, 0.14)], 0.24),
                "score": create_note_sound([(659, 0.06), (880, 0.1)], 0.2),
                "swerve": create_note_sound([(260, 0.035), (390, 0.045)], 0.13),
                "crash": create_crash_sound(),
                "engine": create_engine_sound(),
            }
            self.sounds["engine"].set_volume(0.28)
            self.sounds["crash"].set_volume(0.7)
            self.status_message = f"Audio ready: {self.driver_name}"
        except pygame.error as error:
            self.enabled = False
            self.sounds = {}
            self.status_message = f"Audio setup failed: {error}"
            print(self.status_message)

    def initialize_mixer(self) -> bool:
        if pygame.mixer.get_init() is not None:
            self.driver_name = os.environ.get("SDL_AUDIODRIVER", "default")
            return True

        original_driver = os.environ.get("SDL_AUDIODRIVER")
        drivers: list[str | None] = []
        if original_driver:
            drivers.append(original_driver)
        drivers.extend(driver for driver in audio_drivers_for_platform() if driver != original_driver)

        for driver in drivers:
            if driver is None:
                os.environ.pop("SDL_AUDIODRIVER", None)
            else:
                os.environ["SDL_AUDIODRIVER"] = driver

            try:
                pygame.mixer.quit()
                pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
                self.driver_name = driver or "default"
                return True
            except pygame.error as error:
                label = driver or "default"
                self.failure_details.append(f"{label}: {error}")

        if original_driver is None:
            os.environ.pop("SDL_AUDIODRIVER", None)
        else:
            os.environ["SDL_AUDIODRIVER"] = original_driver

        return False

    def create_failure_message(self) -> str:
        if not self.failure_details:
            return "Audio unavailable: no SDL audio driver worked"

        driver_names = ", ".join(detail.split(":", 1)[0] for detail in self.failure_details)
        last_error = self.failure_details[-1].split(": ", 1)[-1]
        return f"Audio unavailable: tried {driver_names}. Last error: {last_error}"

    def play(self, name: str) -> None:
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def start_engine(self) -> None:
        if not self.enabled or self.engine_channel is not None:
            return

        self.engine_channel = self.sounds["engine"].play(loops=-1)

    def stop_engine(self) -> None:
        if self.engine_channel is not None:
            self.engine_channel.fadeout(180)
            self.engine_channel = None

    def test(self) -> None:
        if self.enabled:
            self.play("start")
        else:
            print(self.status_message)


class Game:
    def __init__(self) -> None:
        pygame.mixer.pre_init(SAMPLE_RATE, -16, 1, 512)
        pygame.init()
        pygame.font.init()

        self.window = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        self.window_size = (WINDOW_WIDTH, WINDOW_HEIGHT)
        self.screen = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)).convert()
        pygame.display.set_caption("Ahoy Adventures")
        self.clock = pygame.time.Clock()

        self.road_rect = pygame.Rect(ROAD_LEFT, ROAD_TOP, ROAD_WIDTH, ROAD_HEIGHT)
        self.drive_rect = pygame.Rect(
            ROAD_LEFT + 42,
            ROAD_TOP + 10,
            ROAD_WIDTH - 84,
            ROAD_HEIGHT - 20,
        )
        self.lane_centers = [
            ROAD_LEFT + LANE_WIDTH * lane + LANE_WIDTH // 2
            for lane in range(LANE_COUNT)
        ]

        self.title_font = pygame.font.SysFont(None, 74)
        self.large_font = pygame.font.SysFont(None, 54)
        self.medium_font = pygame.font.SysFont(None, 36)
        self.small_font = pygame.font.SysFont(None, 28)

        self.assets = Assets()
        self.sounds = SoundBank()
        self.high_score = 0
        self.state = "start"
        self.running = True

        self.player = self.create_player()
        self.hazards: list[Hazard] = []
        self.popups: list[ScorePopup] = []
        self.score = 0
        self.passed_score = 0
        self.elapsed = 0.0
        self.road_scroll = 0.0
        self.spawn_timer = 0.0
        self.spawn_interval = 1.15
        self.scroll_speed = SCROLL_SPEED_START
        self.crash_timer = 0.0
        self.last_player_lane = self.player.lane
        self.audio_message_timer = 5.0 if not self.sounds.enabled else 0.0

    def create_player(self) -> PlayerCar:
        image = self.assets.player_car if hasattr(self, "assets") else create_player_car_surface()
        rect = image.get_rect()
        rect.centerx = self.lane_centers[1]
        rect.bottom = ROAD_BOTTOM - 34
        return PlayerCar(rect=rect, lane=1, speed=PLAYER_SPEED, x=float(rect.x), y=float(rect.y))

    def reset_round(self) -> None:
        self.player = self.create_player()
        self.hazards.clear()
        self.popups.clear()
        self.score = 0
        self.passed_score = 0
        self.elapsed = 0.0
        self.road_scroll = 0.0
        self.spawn_timer = 0.45
        self.spawn_interval = 1.15
        self.scroll_speed = SCROLL_SPEED_START
        self.crash_timer = 0.0
        self.last_player_lane = self.player.lane

    def start_game(self) -> None:
        self.reset_round()
        self.state = "playing"
        self.sounds.play("start")
        self.sounds.start_engine()

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.draw()
            self.present()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.VIDEORESIZE:
                width = max(MIN_WINDOW_WIDTH, event.w)
                height = max(MIN_WINDOW_HEIGHT, event.h)
                self.window_size = (width, height)
                self.window = pygame.display.set_mode(self.window_size, pygame.RESIZABLE)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.sounds.stop_engine()
                    self.running = False
                elif event.key == pygame.K_SPACE and self.state != "playing":
                    self.start_game()
                elif event.key == pygame.K_m:
                    self.sounds.test()
                    self.audio_message_timer = 2.5 if self.sounds.enabled else 5.0

    def update(self, dt: float) -> None:
        self.road_scroll = (self.road_scroll + self.scroll_speed * dt) % 80
        self.update_popups(dt)
        if self.audio_message_timer > 0:
            self.audio_message_timer -= dt

        if self.state == "playing":
            self.update_playing(dt)
        elif self.state == "game_over":
            self.crash_timer += dt
        else:
            self.scroll_speed = SCROLL_SPEED_START * 0.45

    def update_playing(self, dt: float) -> None:
        self.elapsed += dt
        self.scroll_speed = min(
            SCROLL_SPEED_MAX,
            SCROLL_SPEED_START + self.elapsed * SCROLL_ACCELERATION,
        )
        self.spawn_interval = max(0.62, 1.15 - self.elapsed * 0.012)
        self.score = int(self.elapsed * 12) + self.passed_score

        self.update_player(dt)
        self.spawn_timer -= dt
        if self.spawn_timer <= 0:
            self.spawn_hazard_wave()
            jitter = random.uniform(-0.16, 0.14)
            self.spawn_timer = max(0.54, self.spawn_interval + jitter)

        self.update_hazards(dt)
        self.check_collisions()

    def update_player(self, dt: float) -> None:
        keys = pygame.key.get_pressed()
        dx = 0.0
        dy = 0.0
        steering_horizontally = (
            keys[pygame.K_LEFT]
            or keys[pygame.K_a]
            or keys[pygame.K_RIGHT]
            or keys[pygame.K_d]
        )

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= self.player.speed * dt
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += self.player.speed * dt
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= self.player.speed * dt
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += self.player.speed * dt

        if not steering_horizontally:
            dx += self.divider_nudge_dx(dt)

        self.player.x += dx
        self.player.y += dy
        self.player.rect.x = round(self.player.x)
        self.player.rect.y = round(self.player.y)
        self.player.rect.clamp_ip(self.drive_rect)
        self.player.x = float(self.player.rect.x)
        self.player.y = float(self.player.rect.y)

        self.player.lane = min(
            range(LANE_COUNT),
            key=lambda lane: abs(self.player.rect.centerx - self.lane_centers[lane]),
        )
        if self.player.lane != self.last_player_lane:
            self.sounds.play("swerve")
            self.last_player_lane = self.player.lane

    def divider_nudge_dx(self, dt: float) -> float:
        center_x = self.player.rect.centerx
        for lane in range(1, LANE_COUNT):
            divider_x = ROAD_LEFT + lane * LANE_WIDTH
            distance = center_x - divider_x
            if abs(distance) <= DIVIDER_NUDGE_ZONE:
                direction = -1 if distance < 0 else 1
                return direction * DIVIDER_NUDGE_SPEED * dt
        return 0.0

    def spawn_hazard_wave(self) -> None:
        if self.elapsed < 18:
            hazard_count = 1
        elif self.elapsed < 45:
            hazard_count = 2 if random.random() < 0.55 else 1
        else:
            hazard_count = random.choices([1, 2, 3], weights=[2, 6, 1], k=1)[0]

        hazard_count = min(hazard_count, LANE_COUNT - 1)
        lanes = random.sample(range(LANE_COUNT), hazard_count)
        for lane in lanes:
            kind = random.choices(
                ["car", "cone", "work_sign", "barrel", "crate"],
                weights=[5, 3, 2, 2, 2],
                k=1,
            )[0]
            surface = random.choice(self.assets.hazards[kind])
            rect = surface.get_rect()
            rect.centerx = self.lane_centers[lane]
            start_y = -rect.height - random.randint(0, 80)
            rect.y = start_y
            speed = self.scroll_speed * random.uniform(0.88, 1.14)
            self.hazards.append(
                Hazard(
                    rect=rect,
                    kind=kind,
                    lane=lane,
                    speed=speed,
                    surface=surface,
                    x=float(rect.x),
                    y=float(start_y),
                    lane_change_cooldown=random.uniform(0.45, 1.4),
                    points=12 if kind == "car" else 9,
                )
            )

    def update_hazards(self, dt: float) -> None:
        for hazard in self.hazards:
            self.update_hazard_lane_change(hazard, dt)
            hazard.y += hazard.speed * dt
            hazard.rect.x = round(hazard.x)
            hazard.rect.y = round(hazard.y)
            if not hazard.scored and hazard.rect.top > self.player.rect.bottom:
                hazard.scored = True
                self.passed_score += hazard.points
                self.popups.append(
                    ScorePopup(
                        text=f"+{hazard.points}",
                        x=float(hazard.rect.centerx),
                        y=float(hazard.rect.centery),
                        timer=0.75,
                    )
                )
                self.sounds.play("score")

        self.hazards = [
            hazard for hazard in self.hazards
            if hazard.rect.top <= SCREEN_HEIGHT + 80
        ]

    def update_hazard_lane_change(self, hazard: Hazard, dt: float) -> None:
        if hazard.kind != "car" or hazard.scored:
            return

        if hazard.target_lane is not None:
            target_x = self.lane_centers[hazard.target_lane] - hazard.rect.width / 2
            hazard.x = move_toward(hazard.x, target_x, HAZARD_LANE_CHANGE_SPEED * dt)
            if hazard.x == target_x:
                hazard.lane = hazard.target_lane
                hazard.target_lane = None
                hazard.lane_change_cooldown = CAR_LANE_CHANGE_COOLDOWN
            return

        if hazard.rect.top > ROAD_TOP + ROAD_HEIGHT * 0.58:
            return

        hazard.lane_change_cooldown -= dt
        if hazard.lane_change_cooldown > 0:
            return
        hazard.lane_change_cooldown = CAR_LANE_CHANGE_COOLDOWN

        if random.random() > CAR_LANE_CHANGE_CHANCE:
            return

        options = []
        for direction in (-1, 1):
            lane = hazard.lane + direction
            if 0 <= lane < LANE_COUNT and self.lane_is_open_for_hazard(hazard, lane):
                options.append(lane)

        if options:
            hazard.target_lane = random.choice(options)

    def lane_is_open_for_hazard(self, moving_hazard: Hazard, target_lane: int) -> bool:
        target_center = self.lane_centers[target_lane]
        for hazard in self.hazards:
            if hazard is moving_hazard:
                continue
            if hazard.target_lane == target_lane or hazard.lane == target_lane:
                if abs(hazard.rect.centery - moving_hazard.rect.centery) < 126:
                    return False
            if abs(hazard.rect.centerx - target_center) < 46:
                if abs(hazard.rect.centery - moving_hazard.rect.centery) < 126:
                    return False
        return True

    def update_popups(self, dt: float) -> None:
        for popup in self.popups:
            popup.timer -= dt
            popup.y -= 38 * dt
        self.popups = [popup for popup in self.popups if popup.timer > 0]

    def check_collisions(self) -> None:
        player_hitbox = self.player.rect.inflate(-18, -22)
        for hazard in self.hazards:
            hazard_hitbox = hazard.rect.inflate(-12, -12)
            if player_hitbox.colliderect(hazard_hitbox):
                self.high_score = max(self.high_score, self.score)
                self.state = "game_over"
                self.crash_timer = 0.0
                self.sounds.stop_engine()
                self.sounds.play("crash")
                self.popups.append(
                    ScorePopup(
                        text="BONK!",
                        x=float(self.player.rect.centerx),
                        y=float(self.player.rect.top),
                        timer=1.0,
                    )
                )
                return

    def draw(self) -> None:
        self.draw_sea_background()
        self.draw_road()
        self.draw_hazards()
        self.draw_player()
        self.draw_popups()
        self.draw_ui()

        if self.state == "start":
            self.draw_start_overlay()
        elif self.state == "game_over":
            self.draw_game_over_overlay()

        self.draw_audio_status()

    def present(self) -> None:
        window_width, window_height = self.window_size
        scale = min(window_width / SCREEN_WIDTH, window_height / SCREEN_HEIGHT)
        scaled_width = round(SCREEN_WIDTH * scale)
        scaled_height = round(SCREEN_HEIGHT * scale)
        x = (window_width - scaled_width) // 2
        y = (window_height - scaled_height) // 2

        self.window.fill(SEA_BLUE)
        scaled_screen = pygame.transform.smoothscale(
            self.screen,
            (scaled_width, scaled_height),
        )
        self.window.blit(scaled_screen, (x, y))

    def draw_sea_background(self) -> None:
        self.screen.fill(SEA_BLUE)
        for y in range(0, SCREEN_HEIGHT, 48):
            wave_offset = int((self.road_scroll * 0.3 + y) % 32)
            pygame.draw.arc(
                self.screen,
                SEA_DARK,
                (26 - wave_offset, y + 8, 58, 24),
                0,
                3.14,
                3,
            )
            pygame.draw.arc(
                self.screen,
                SEA_DARK,
                (SCREEN_WIDTH - 82 + wave_offset, y + 22, 58, 24),
                0,
                3.14,
                3,
            )

        self.draw_side_decorations()

    def draw_side_decorations(self) -> None:
        draw_fish(self.screen, 78, 128, ORANGE, flip=False)
        draw_fish(self.screen, 704, 172, PINK, flip=True)
        draw_fish(self.screen, 92, 452, RAIL_RED, flip=False)
        draw_fish(self.screen, 728, 556, ORANGE, flip=True)
        draw_bubbles(self.screen, 94, 248)
        draw_bubbles(self.screen, 706, 344)
        draw_pirate_flag(self.screen, 64, SCREEN_HEIGHT - 156)
        draw_lighthouse(self.screen, SCREEN_WIDTH - 96, SCREEN_HEIGHT - 154)
        draw_crab(self.screen, 106, SCREEN_HEIGHT - 84)
        draw_ship_wheel(self.screen, SCREEN_WIDTH - 84, SCREEN_HEIGHT - 228)

    def draw_road(self) -> None:
        pygame.draw.rect(self.screen, ROAD_BLUE_DARK, self.road_rect, border_radius=16)
        inner = self.road_rect.inflate(-18, -16)
        pygame.draw.rect(self.screen, ROAD_BLUE, inner, border_radius=12)

        self.draw_side_rails()
        self.draw_lane_markings()

        pygame.draw.rect(self.screen, (34, 91, 126), self.road_rect, width=4, border_radius=16)

    def draw_side_rails(self) -> None:
        rail_width = 24
        for x in (ROAD_LEFT + 10, ROAD_RIGHT - rail_width - 10):
            rail = pygame.Rect(x, ROAD_TOP + 8, rail_width, ROAD_HEIGHT - 16)
            pygame.draw.rect(self.screen, WHITE, rail)
            stripe_height = 58
            start = ROAD_TOP - stripe_height + int(self.road_scroll % stripe_height)
            for y in range(start, ROAD_BOTTOM, stripe_height):
                points = [
                    (x, y + 8),
                    (x + rail_width, y + 30),
                    (x + rail_width, y + 54),
                    (x, y + 32),
                ]
                pygame.draw.polygon(self.screen, RAIL_RED, points)

    def draw_lane_markings(self) -> None:
        dash_height = 34
        gap = 36
        pattern = dash_height + gap
        start_y = ROAD_TOP - pattern + int(self.road_scroll % pattern)

        for lane in range(1, LANE_COUNT):
            x = ROAD_LEFT + lane * LANE_WIDTH
            for y in range(start_y, ROAD_BOTTOM, pattern):
                pygame.draw.rect(
                    self.screen,
                    LANE_WHITE,
                    (x - 3, y, 6, dash_height),
                    border_radius=3,
                )

    def draw_hazards(self) -> None:
        for hazard in self.hazards:
            self.screen.blit(hazard.surface, hazard.rect)

    def draw_player(self) -> None:
        shadow = self.player.rect.move(0, 6)
        pygame.draw.ellipse(self.screen, (18, 80, 112), shadow.inflate(-8, -22))
        self.screen.blit(self.assets.player_car, self.player.rect)

    def draw_popups(self) -> None:
        for popup in self.popups:
            alpha = max(0, min(255, int(255 * (popup.timer / 0.9))))
            color = YELLOW if popup.text != "BONK!" else RAIL_RED
            text = self.medium_font.render(popup.text, True, color)
            text.set_alpha(alpha)
            shadow = self.medium_font.render(popup.text, True, BLACK)
            shadow.set_alpha(alpha)
            rect = text.get_rect(center=(round(popup.x), round(popup.y)))
            self.screen.blit(shadow, rect.move(2, 2))
            self.screen.blit(text, rect)

    def draw_ui(self) -> None:
        score_text = self.small_font.render(f"Score: {self.score}", True, WHITE)
        score_shadow = self.small_font.render(f"Score: {self.score}", True, TEXT_NAVY)
        self.screen.blit(score_shadow, (24, 16))
        self.screen.blit(score_text, (22, 14))

        best_text = self.small_font.render(f"Best: {self.high_score}", True, WHITE)
        best_shadow = self.small_font.render(f"Best: {self.high_score}", True, TEXT_NAVY)
        x = SCREEN_WIDTH - best_text.get_width() - 22
        self.screen.blit(best_shadow, (x + 2, 16))
        self.screen.blit(best_text, (x, 14))

    def draw_audio_status(self) -> None:
        if self.audio_message_timer <= 0 or self.sounds.enabled:
            return

        message = self.sounds.status_message
        if len(message) > 52:
            message = message[:49] + "..."

        text = self.small_font.render(message, True, RAIL_RED)
        shadow = self.small_font.render(message, True, WHITE)
        rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self.screen.blit(shadow, rect.move(2, 2))
        self.screen.blit(text, rect)

    def draw_start_overlay(self) -> None:
        title = self.title_font.render("Ahoy Adventures", True, WHITE)
        title_shadow = self.title_font.render("Ahoy Adventures", True, TEXT_NAVY)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 132))
        self.screen.blit(title_shadow, title_rect.move(3, 4))
        self.screen.blit(title, title_rect)

        subtitle = self.medium_font.render("Dodge the toy traffic!", True, TEXT_NAVY)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 192))
        self.screen.blit(subtitle, subtitle_rect)

        prompt = self.large_font.render("Press SPACE", True, YELLOW)
        prompt_shadow = self.large_font.render("Press SPACE", True, TEXT_NAVY)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 188))
        self.screen.blit(prompt_shadow, prompt_rect.move(3, 3))
        self.screen.blit(prompt, prompt_rect)

        controls = self.small_font.render("Arrow keys or WASD", True, WHITE)
        controls_rect = controls.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 146))
        self.screen.blit(controls, controls_rect)

        sound_test = self.small_font.render("M tests sound", True, WHITE)
        sound_test_rect = sound_test.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 112))
        self.screen.blit(sound_test, sound_test_rect)

    def draw_game_over_overlay(self) -> None:
        pulse = 1.0 + min(self.crash_timer, 0.25) * 0.8
        title = self.large_font.render("Nice drive!", True, WHITE)
        title = pygame.transform.rotozoom(title, 0, pulse)
        title_shadow = self.large_font.render("Nice drive!", True, TEXT_NAVY)
        title_shadow = pygame.transform.rotozoom(title_shadow, 0, pulse)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 182))
        self.screen.blit(title_shadow, title_rect.move(3, 4))
        self.screen.blit(title, title_rect)

        score = self.medium_font.render(f"Score: {self.score}", True, YELLOW)
        score_rect = score.get_rect(center=(SCREEN_WIDTH // 2, 246))
        self.screen.blit(score, score_rect)

        prompt = self.medium_font.render("Press SPACE to race again", True, WHITE)
        prompt_rect = prompt.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 146))
        self.screen.blit(prompt, prompt_rect)


def create_note_sound(
    notes: list[tuple[float, float]],
    volume: float,
) -> pygame.mixer.Sound:
    samples = array("h")
    gap_samples = int(SAMPLE_RATE * 0.008)

    for frequency, duration in notes:
        note_samples = max(1, int(SAMPLE_RATE * duration))
        attack_samples = max(1, int(SAMPLE_RATE * 0.006))
        release_samples = max(1, int(SAMPLE_RATE * 0.026))

        for index in range(note_samples):
            time = index / SAMPLE_RATE
            attack = min(1.0, index / attack_samples)
            release = min(1.0, (note_samples - index) / release_samples)
            envelope = max(0.0, min(attack, release))
            wave = math.sin(2 * math.pi * frequency * time)
            wave += 0.28 * math.sin(2 * math.pi * frequency * 2 * time)
            samples.append(to_int16(wave * envelope * volume))

        samples.extend([0] * gap_samples)

    return pygame.mixer.Sound(buffer=samples.tobytes())


def move_toward(value: float, target: float, step: float) -> float:
    if value < target:
        return min(value + step, target)
    if value > target:
        return max(value - step, target)
    return value


def audio_drivers_for_platform() -> tuple[str, ...]:
    if sys.platform.startswith("linux"):
        return LINUX_AUDIO_DRIVERS
    if sys.platform.startswith("win"):
        return WINDOWS_AUDIO_DRIVERS
    if sys.platform == "darwin":
        return MAC_AUDIO_DRIVERS
    return LINUX_AUDIO_DRIVERS + WINDOWS_AUDIO_DRIVERS + MAC_AUDIO_DRIVERS


def create_crash_sound() -> pygame.mixer.Sound:
    samples = array("h")
    sample_count = int(SAMPLE_RATE * 0.34)
    rng = random.Random(14)

    for index in range(sample_count):
        time = index / SAMPLE_RATE
        progress = index / sample_count
        envelope = (1.0 - progress) ** 2.2
        thump = math.sin(2 * math.pi * 72 * time) * max(0.0, 1.0 - time / 0.18)
        scrape = math.sin(2 * math.pi * (190 + 220 * progress) * time) * 0.22
        noise = rng.uniform(-1.0, 1.0) * 0.56
        samples.append(to_int16((thump * 0.9 + scrape + noise) * envelope * 0.72))

    return pygame.mixer.Sound(buffer=samples.tobytes())


def create_engine_sound() -> pygame.mixer.Sound:
    samples = array("h")
    sample_count = int(SAMPLE_RATE * 0.3)

    for index in range(sample_count):
        time = index / SAMPLE_RATE
        wobble = 0.72 + 0.28 * math.sin(2 * math.pi * 8 * time)
        wave = math.sin(2 * math.pi * 74 * time)
        wave += 0.48 * math.sin(2 * math.pi * 148 * time)
        wave += 0.18 * math.sin(2 * math.pi * 38 * time)
        samples.append(to_int16(wave * wobble * 0.18))

    return pygame.mixer.Sound(buffer=samples.tobytes())


def to_int16(value: float) -> int:
    return max(-32768, min(32767, int(value * 32767)))


def create_player_car_surface() -> pygame.Surface:
    surface = pygame.Surface((52, 86), pygame.SRCALPHA)
    yellow = (252, 207, 39)
    yellow_dark = (214, 148, 22)
    black = (22, 28, 34)
    glass = (117, 221, 244)
    glow_blue = (78, 180, 238)

    pygame.draw.ellipse(surface, (20, 32, 42, 95), (5, 70, 42, 12))

    pygame.draw.rect(surface, black, (4, 18, 8, 19), border_radius=3)
    pygame.draw.rect(surface, black, (40, 18, 8, 19), border_radius=3)
    pygame.draw.rect(surface, black, (4, 54, 8, 19), border_radius=3)
    pygame.draw.rect(surface, black, (40, 54, 8, 19), border_radius=3)

    pygame.draw.polygon(
        surface,
        yellow_dark,
        [(13, 9), (20, 3), (32, 3), (39, 9), (43, 74), (34, 82), (18, 82), (9, 74)],
    )
    pygame.draw.polygon(
        surface,
        yellow,
        [(16, 8), (23, 5), (29, 5), (36, 8), (40, 72), (32, 78), (20, 78), (12, 72)],
    )

    pygame.draw.polygon(surface, black, [(17, 11), (23, 8), (29, 8), (35, 11), (32, 19), (20, 19)])
    pygame.draw.polygon(surface, glass, [(16, 25), (22, 20), (30, 20), (36, 25), (34, 39), (18, 39)])
    pygame.draw.line(surface, WHITE, (20, 24), (28, 24), 2)

    pygame.draw.polygon(surface, black, [(13, 43), (20, 48), (20, 66), (13, 70)])
    pygame.draw.polygon(surface, black, [(39, 43), (32, 48), (32, 66), (39, 70)])
    pygame.draw.rect(surface, black, (20, 49, 12, 17), border_radius=4)

    pygame.draw.line(surface, black, (17, 10), (17, 72), 3)
    pygame.draw.line(surface, black, (35, 10), (35, 72), 3)
    pygame.draw.line(surface, yellow_dark, (22, 43), (30, 43), 2)

    pygame.draw.polygon(surface, glow_blue, [(17, 76), (23, 72), (29, 72), (35, 76), (32, 80), (20, 80)])
    pygame.draw.circle(surface, (255, 244, 168), (15, 11), 3)
    pygame.draw.circle(surface, (255, 244, 168), (37, 11), 3)
    pygame.draw.circle(surface, glow_blue, (21, 15), 2)
    pygame.draw.circle(surface, glow_blue, (31, 15), 2)
    return surface


def create_car_surface(body_color: tuple[int, int, int], accent: tuple[int, int, int]) -> pygame.Surface:
    surface = pygame.Surface((52, 86), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (20, 32, 42, 95), (6, 70, 40, 12))

    pygame.draw.rect(surface, BLACK, (5, 18, 8, 18), border_radius=3)
    pygame.draw.rect(surface, BLACK, (39, 18, 8, 18), border_radius=3)
    pygame.draw.rect(surface, BLACK, (5, 54, 8, 18), border_radius=3)
    pygame.draw.rect(surface, BLACK, (39, 54, 8, 18), border_radius=3)

    pygame.draw.rect(surface, body_color, (10, 5, 32, 76), border_radius=10)
    pygame.draw.rect(surface, accent, (15, 10, 22, 9), border_radius=4)
    pygame.draw.rect(surface, (134, 220, 242), (15, 25, 22, 16), border_radius=5)
    pygame.draw.rect(surface, (22, 37, 47), (15, 51, 22, 18), border_radius=5)
    pygame.draw.line(surface, WHITE, (18, 28), (25, 28), 2)
    pygame.draw.rect(surface, (245, 246, 232), (14, 75, 24, 4), border_radius=2)
    pygame.draw.circle(surface, YELLOW, (14, 11), 3)
    pygame.draw.circle(surface, YELLOW, (38, 11), 3)
    return surface


def create_cone_surface() -> pygame.Surface:
    surface = pygame.Surface((56, 64), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (20, 32, 42, 80), (8, 52, 40, 10))
    pygame.draw.polygon(surface, ORANGE, [(28, 4), (10, 54), (46, 54)])
    pygame.draw.polygon(surface, WHITE, [(21, 24), (35, 24), (39, 34), (17, 34)])
    pygame.draw.rect(surface, RAIL_RED, (7, 50, 42, 8), border_radius=4)
    return surface


def create_work_sign_surface() -> pygame.Surface:
    surface = pygame.Surface((64, 64), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (20, 32, 42, 80), (8, 52, 48, 10))
    pygame.draw.polygon(surface, (255, 243, 199), [(32, 4), (5, 56), (59, 56)])
    pygame.draw.polygon(surface, RAIL_RED, [(32, 4), (5, 56), (59, 56)], width=5)
    pygame.draw.circle(surface, BLACK, (31, 25), 4)
    pygame.draw.line(surface, BLACK, (31, 29), (28, 43), 4)
    pygame.draw.line(surface, BLACK, (29, 34), (19, 40), 3)
    pygame.draw.line(surface, BLACK, (29, 35), (39, 40), 3)
    pygame.draw.line(surface, BLACK, (28, 43), (21, 52), 3)
    pygame.draw.line(surface, BLACK, (28, 43), (38, 51), 3)
    return surface


def create_barrel_surface() -> pygame.Surface:
    surface = pygame.Surface((48, 60), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (20, 32, 42, 80), (6, 48, 36, 10))
    pygame.draw.rect(surface, (197, 53, 48), (9, 7, 30, 46), border_radius=8)
    pygame.draw.ellipse(surface, (230, 83, 71), (9, 4, 30, 12))
    pygame.draw.ellipse(surface, (138, 38, 40), (9, 43, 30, 12))
    pygame.draw.rect(surface, (245, 226, 184), (10, 18, 28, 5), border_radius=2)
    pygame.draw.rect(surface, (245, 226, 184), (10, 36, 28, 5), border_radius=2)
    return surface


def create_crate_surface() -> pygame.Surface:
    surface = pygame.Surface((58, 58), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, (20, 32, 42, 80), (8, 48, 42, 9))
    pygame.draw.rect(surface, (172, 103, 54), (8, 8, 42, 42), border_radius=4)
    pygame.draw.rect(surface, (116, 71, 43), (8, 8, 42, 42), width=4, border_radius=4)
    pygame.draw.line(surface, (116, 71, 43), (12, 12), (46, 46), 4)
    pygame.draw.line(surface, (116, 71, 43), (46, 12), (12, 46), 4)
    return surface


def draw_fish(
    surface: pygame.Surface,
    x: int,
    y: int,
    color: tuple[int, int, int],
    *,
    flip: bool,
) -> None:
    direction = -1 if flip else 1
    pygame.draw.ellipse(surface, color, (x - 13, y - 7, 26, 14))
    pygame.draw.polygon(
        surface,
        color,
        [(x - direction * 13, y), (x - direction * 25, y - 8), (x - direction * 25, y + 8)],
    )
    pygame.draw.circle(surface, BLACK, (x + direction * 7, y - 2), 2)


def draw_bubbles(surface: pygame.Surface, x: int, y: int) -> None:
    for offset_x, offset_y, radius in [(0, 0, 8), (15, -20, 5), (-10, -36, 4)]:
        pygame.draw.circle(surface, (205, 246, 255), (x + offset_x, y + offset_y), radius, 2)


def draw_pirate_flag(surface: pygame.Surface, x: int, y: int) -> None:
    pygame.draw.line(surface, TEXT_NAVY, (x, y), (x, y + 70), 4)
    pygame.draw.polygon(surface, RAIL_RED, [(x + 4, y + 4), (x + 62, y + 16), (x + 4, y + 31)])
    pygame.draw.circle(surface, WHITE, (x + 28, y + 17), 5)
    pygame.draw.line(surface, WHITE, (x + 21, y + 24), (x + 35, y + 10), 2)
    pygame.draw.line(surface, WHITE, (x + 21, y + 10), (x + 35, y + 24), 2)


def draw_lighthouse(surface: pygame.Surface, x: int, y: int) -> None:
    pygame.draw.rect(surface, WHITE, (x + 14, y + 14, 32, 74), border_radius=4)
    pygame.draw.rect(surface, RAIL_RED, (x + 14, y + 27, 32, 12))
    pygame.draw.rect(surface, RAIL_RED, (x + 14, y + 56, 32, 12))
    pygame.draw.rect(surface, TEXT_NAVY, (x + 23, y + 2, 14, 14), border_radius=3)
    pygame.draw.polygon(surface, RAIL_RED, [(x + 16, y + 2), (x + 44, y + 2), (x + 30, y - 12)])
    pygame.draw.rect(surface, (238, 238, 213), (x + 25, y + 76, 10, 12))


def draw_crab(surface: pygame.Surface, x: int, y: int) -> None:
    pygame.draw.ellipse(surface, RAIL_RED, (x - 18, y - 10, 36, 20))
    pygame.draw.circle(surface, BLACK, (x - 6, y - 8), 2)
    pygame.draw.circle(surface, BLACK, (x + 6, y - 8), 2)
    for direction in (-1, 1):
        pygame.draw.line(surface, RAIL_RED, (x + direction * 15, y - 1), (x + direction * 28, y - 12), 3)
        pygame.draw.circle(surface, RAIL_RED, (x + direction * 31, y - 15), 5, 2)
        for leg in range(3):
            pygame.draw.line(
                surface,
                RAIL_RED,
                (x + direction * (6 + leg * 4), y + 8),
                (x + direction * (12 + leg * 8), y + 18),
                2,
            )


def draw_ship_wheel(surface: pygame.Surface, x: int, y: int) -> None:
    pygame.draw.circle(surface, (105, 70, 43), (x, y), 22, 5)
    pygame.draw.circle(surface, (105, 70, 43), (x, y), 6)
    for angle_index in range(8):
        if angle_index % 2 == 0:
            dx = 0
            dy = 26 if angle_index == 0 else -26
            if angle_index == 2:
                dx, dy = 26, 0
            elif angle_index == 6:
                dx, dy = -26, 0
        else:
            dx = 18 if angle_index in (1, 3) else -18
            dy = 18 if angle_index in (1, 7) else -18
        pygame.draw.line(surface, (105, 70, 43), (x, y), (x + dx, y + dy), 4)


if __name__ == "__main__":
    Game().run()
