import pygame
import os
import math
import random

# Initialize Pygame
pygame.init()

# Initialize font
pygame.font.init()

# Initialize sound mixer
pygame.mixer.init()

# Constants
TILE_SIZE = 16
SCALE = 2
SPEED = 1.2 * SCALE
FPS = 60

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PINK = (255, 105, 180)
CYAN = (0, 255, 255)
ORANGE = (255, 165, 0)
GREEN = (0, 255, 0)

# Maze layout with 14 rows (twice as tall as the original 7 rows)
maze = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.#####.##.#####.######",
    "######.#####.##.#####.######",
    "######.#####.##.#####.######",
    "######.#####.##.#####.######",
    "######.#####.##.#####.######",
    "#......##....##....##......#",
    "#.####.##.########.##.####.#",
    "#..........................#",
    "#.####.#####.##.#####.####.#",
    "#o####.......##.......####o#",
    "############################"
]
ROWS = len(maze)  # Now 19
COLS = len(maze[0])  # Still 28

# Screen dimensions based on maze size
SCREEN_WIDTH = COLS * TILE_SIZE * SCALE  # 896 pixels for 28 columns
SCREEN_HEIGHT = ROWS * TILE_SIZE * SCALE  # 512 pixels for 16 rows
LINE_WIDTH = 4 * SCALE

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pacman - Pygame Edition")
clock = pygame.time.Clock()

# Create background surface with walls only
background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
background.fill(BLACK)

for i in range(ROWS):
    for j in range(COLS):
        if maze[i][j] == '#':
            x = j * TILE_SIZE * SCALE
            y = i * TILE_SIZE * SCALE
            # Draw wall lines based on adjacent tiles
            if i == 0 or maze[i-1][j] != '#':
                pygame.draw.line(background, BLUE, (x, y), (x + TILE_SIZE * SCALE, y), LINE_WIDTH)
            if j == 0 or maze[i][j-1] != '#':
                pygame.draw.line(background, BLUE, (x, y), (x, y + TILE_SIZE * SCALE), LINE_WIDTH)
            if i == ROWS-1 or maze[i+1][j] != '#':
                pygame.draw.line(background, BLUE, (x, y + TILE_SIZE * SCALE), (x + TILE_SIZE * SCALE, y + TILE_SIZE * SCALE), LINE_WIDTH)
            if j == COLS-1 or maze[i][j+1] != '#':
                pygame.draw.line(background, BLUE, (x + TILE_SIZE * SCALE, y), (x + TILE_SIZE * SCALE, y + TILE_SIZE * SCALE), LINE_WIDTH)

# Pacman class
class Pacman:
    def __init__(self, i, j):
        self.start_i = i
        self.start_j = j
        self.current_tile = [i, j]
        self.position = pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE)
        self.direction = (0, 1)  # Start moving right
        self.intended_direction = self.direction
        self.target_tile = self.current_tile[:]
        self.target_position = self.position
        self.speed = SPEED
        self.radius = TILE_SIZE * SCALE // 2
        self.mouth_angle = 45  # Degrees for mouth opening
        self.mouth_speed = 5  # Animation speed
        self.lives = 3
        self.dying = False
        self.death_timer = 0
        self.death_duration = 60  # 1 second death animation at 60 FPS
        self.powered_up = False
        self.power_timer = 0
        self.power_duration = 660  # 11 seconds at 60 FPS

    def update(self):
        if self.dying:
            self.death_timer -= 1
            if self.death_timer <= 0:
                self.dying = False
                self.lives -= 1
                return 'reset'  # Signal to reset positions
            return None

        # Count down power-up timer
        if self.powered_up:
            self.power_timer -= 1
            if self.power_timer <= 0:
                self.powered_up = False

        # Animate mouth
        self.mouth_angle += self.mouth_speed
        if self.mouth_angle >= 45 or self.mouth_angle <= 0:
            self.mouth_speed = -self.mouth_speed

        # If at tile center, decide next move
        if self.position == self.target_position:
            self.current_tile = self.target_tile[:]
            i, j = self.current_tile
            di, dj = self.intended_direction
            # Check if intended direction is possible
            if 0 <= i + di < ROWS and 0 <= j + dj < COLS and maze[i + di][j + dj] != '#':
                self.direction = self.intended_direction
            # Move in current direction if possible
            di, dj = self.direction
            if 0 <= i + di < ROWS and 0 <= j + dj < COLS and maze[i + di][j + dj] != '#':
                self.target_tile = [i + di, j + dj]
                self.target_position = pygame.math.Vector2((j + dj + 0.5) * TILE_SIZE * SCALE, (i + di + 0.5) * TILE_SIZE * SCALE)
            else:
                self.target_tile = self.current_tile[:]
                self.target_position = self.position

        # Move towards target
        if self.position != self.target_position:
            vec_to_target = self.target_position - self.position
            distance = vec_to_target.length()
            if distance <= self.speed:
                self.position = self.target_position
            else:
                self.position += vec_to_target.normalize() * self.speed

        # Eat pellets
        i, j = int(self.position.y // (TILE_SIZE * SCALE)), int(self.position.x // (TILE_SIZE * SCALE))
        if 0 <= i < ROWS and 0 <= j < COLS and maze[i][j] in '.o':
            was_power = maze[i][j] == 'o'
            maze[i] = maze[i][:j] + ' ' + maze[i][j+1:]  # Remove pellet
            eat_dot_sound.play()
            if was_power:
                self.powered_up = True
                self.power_timer = self.power_duration
                return 'power'

    def die(self):
        if not self.dying:
            self.dying = True
            self.death_timer = self.death_duration

    def reset(self):
        i, j = self.start_i, self.start_j
        self.current_tile = [i, j]
        self.position = pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE)
        self.direction = (0, 1)
        self.intended_direction = self.direction
        self.target_tile = self.current_tile[:]
        self.target_position = self.position
        self.mouth_angle = 45
        self.mouth_speed = 5
        self.powered_up = False
        self.power_timer = 0

    def draw(self):
        # Death animation: shrinking pacman
        if self.dying:
            progress = self.death_timer / self.death_duration  # 1.0 -> 0.0
            shrink_radius = int(self.radius * progress)
            if shrink_radius > 0:
                pygame.draw.circle(screen, YELLOW,
                                   (int(self.position.x), int(self.position.y)), shrink_radius)
            return

        color = YELLOW

        # Determine angle based on direction
        if self.direction == (0, 1):  # Right
            start_angle = math.radians(self.mouth_angle)
            end_angle = math.radians(360 - self.mouth_angle)
        elif self.direction == (0, -1):  # Left
            start_angle = math.radians(180 + self.mouth_angle)
            end_angle = math.radians(180 - self.mouth_angle)
        elif self.direction == (-1, 0):  # Up
            start_angle = math.radians(90 + self.mouth_angle)
            end_angle = math.radians(90 - self.mouth_angle)
        else:  # Down
            start_angle = math.radians(270 + self.mouth_angle)
            end_angle = math.radians(270 - self.mouth_angle)

        # Draw Pacman with mouth
        pygame.draw.arc(screen, color, 
                       (int(self.position.x - self.radius), int(self.position.y - self.radius), 
                        self.radius * 2, self.radius * 2),
                       start_angle, end_angle, self.radius)

# Ghost class
class Ghost:
    def __init__(self, i, j, color):
        self.start_i = i
        self.start_j = j
        self.current_tile = [i, j]
        self.position = pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE)
        self.direction = (0, 1)
        self.speed = SPEED * 0.9
        self.radius = TILE_SIZE * SCALE // 2
        self.color = color
        self.eaten = False
        self.respawn_timer = 0
        self.respawn_delay = 300  # 5 seconds at 60 FPS

    def reset(self):
        i, j = self.start_i, self.start_j
        self.current_tile = [i, j]
        self.position = pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE)
        self.direction = (0, 1)
        self.eaten = False
        self.respawn_timer = 0

    def eat(self):
        self.eaten = True
        self.respawn_timer = self.respawn_delay
        i, j = self.start_i, self.start_j
        self.current_tile = [i, j]
        self.position = pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE)
        self.direction = (0, 1)

    def update(self):
        if self.eaten:
            self.respawn_timer -= 1
            if self.respawn_timer <= 0:
                self.eaten = False
            return
        i, j = self.current_tile
        di, dj = self.direction
        if self.position == pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE):
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            reverse = (-di, -dj)
            possible = [(d, e) for d, e in directions if 0 <= i + d < ROWS and 0 <= j + e < COLS and maze[i + d][j + e] != '#']
            # Classic Pacman rule: never reverse unless it's the only option
            non_reverse = [d for d in possible if d != reverse]
            choices = non_reverse if non_reverse else possible
            if choices:
                self.direction = random.choice(choices)
                di, dj = self.direction
                self.current_tile = [i + di, j + dj]
        # Move towards current tile center (slower when Pacman is powered up)
        speed = self.speed * 0.5 if pacman.powered_up else self.speed
        target = pygame.math.Vector2((self.current_tile[1] + 0.5) * TILE_SIZE * SCALE, (self.current_tile[0] + 0.5) * TILE_SIZE * SCALE)
        vec = target - self.position
        if vec.length() > speed:
            self.position += vec.normalize() * speed
        else:
            self.position = target

    def draw(self):
        if self.eaten:
            return  # Invisible while waiting to respawn

        # Determine body color
        if pacman.powered_up:
            # Flash blue/white when power-up is ending soon
            if pacman.power_timer < 120 and (pygame.time.get_ticks() // 150) % 2 == 0:
                body_color = WHITE
            else:
                body_color = (30, 30, 200)  # Dark blue
        else:
            body_color = self.color

        # Draw ghost body (semicircle top, wavy bottom)
        body_points = []
        # Top semicircle
        for angle in range(0, 181, 10):
            x = int(self.position.x + self.radius * math.cos(math.radians(angle - 90)))
            y = int(self.position.y + self.radius * math.sin(math.radians(angle - 90)))
            body_points.append((x, y))
        # Wavy bottom
        for x in range(int(self.position.x - self.radius), int(self.position.x + self.radius) + 1, 4):
            y = int(self.position.y + self.radius * (0.2 * math.sin(x * 0.5) + 0.8))
            body_points.append((x, y))
        pygame.draw.polygon(screen, body_color, body_points)

        # Draw eyes
        eye_radius = self.radius // 4
        eye_offset = self.radius // 2
        # Left eye
        pygame.draw.circle(screen, WHITE, 
                          (int(self.position.x - eye_offset), int(self.position.y - eye_offset)), 
                          eye_radius)
        pygame.draw.circle(screen, BLACK, 
                          (int(self.position.x - eye_offset), int(self.position.y - eye_offset)), 
                          eye_radius // 2)
        # Right eye
        pygame.draw.circle(screen, WHITE, 
                          (int(self.position.x + eye_offset), int(self.position.y - eye_offset)), 
                          eye_radius)
        pygame.draw.circle(screen, BLACK, 
                          (int(self.position.x + eye_offset), int(self.position.y - eye_offset)), 
                          eye_radius // 2)

# Game state variables
game_completed = False
game_over = False
congratulations_timer = 0
congratulations_duration = 180  # 3 seconds at 60 FPS
score = 0
ghost_combo = 0  # Escalates: 200, 400, 800, 1600
freeze_timer = 0
FREEZE_DURATION = 18
screen_shake = 0
score_popups = []  # [{text, x, y, timer, color}]

# Function to check if all food has been eaten
def check_all_food_eaten():
    for row in maze:
        if '.' in row or 'o' in row:
            return False
    return True

# Initialize game objects
pacman = Pacman(1, 1)
ghosts = [
    Ghost(6, 1, RED),
    Ghost(6, 26, PINK),
    Ghost(14, 1, CYAN),
    Ghost(14, 26, ORANGE)
]

# Initialize fonts
congratulations_font = pygame.font.SysFont('Arial', 48)
score_font = pygame.font.SysFont('Arial', 28, bold=True)
popup_font = pygame.font.SysFont('Arial', 24, bold=True)

# Load sounds
try:
    eat_dot_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), 'sounds', 'eat_dot.wav'))
    eat_dot_sound.set_volume(0.5)  # Set a lower volume to make it subtle
except:
    # Create a silent sound if file not found
    eat_dot_sound = pygame.mixer.Sound(buffer=bytearray([0]*44))
    print("Warning: Could not load eat_dot sound file")

# Game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                pacman.intended_direction = (0, -1)
            elif event.key == pygame.K_RIGHT:
                pacman.intended_direction = (0, 1)
            elif event.key == pygame.K_UP:
                pacman.intended_direction = (-1, 0)
            elif event.key == pygame.K_DOWN:
                pacman.intended_direction = (1, 0)

    # Track power-up transition to reset combo
    was_powered = pacman.powered_up

    # Freeze frame countdown (everything pauses except popups)
    if freeze_timer > 0:
        freeze_timer -= 1
        screen_shake = max(screen_shake - 1, 0)
    elif not game_over and not game_completed:
        # Update game state
        result = pacman.update()
        if result == 'reset':
            if pacman.lives <= 0:
                game_over = True
            else:
                pacman.reset()
                for ghost in ghosts:
                    ghost.reset()
        if not pacman.dying:
            for ghost in ghosts:
                ghost.update()

            # Check for collisions between Pacman and ghosts
            for ghost in ghosts:
                if ghost.eaten:
                    continue
                distance = (pacman.position - ghost.position).length()
                if distance < pacman.radius + ghost.radius:
                    if pacman.powered_up:
                        # Exciting ghost eating!
                        ghost_combo += 1
                        points = 200 * (2 ** (ghost_combo - 1))
                        score += points
                        # Score popup at ghost's position
                        score_popups.append({
                            'text': str(points),
                            'x': ghost.position.x,
                            'y': ghost.position.y,
                            'timer': 50,
                        })
                        ghost.eat()
                        freeze_timer = FREEZE_DURATION
                        screen_shake = 10
                    else:
                        pacman.die()
                    break

        # Reset combo when power-up ends
        if was_powered and not pacman.powered_up:
            ghost_combo = 0

        # Check if all food has been eaten
        if not game_completed and check_all_food_eaten():
            game_completed = True
            congratulations_timer = congratulations_duration

    # Update score popups
    for popup in score_popups:
        popup['timer'] -= 1
        popup['y'] -= 1.5  # Float upward
    score_popups = [p for p in score_popups if p['timer'] > 0]

    # Screen shake offset
    shake_x = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0
    shake_y = random.randint(-screen_shake, screen_shake) if screen_shake > 0 else 0

    # Draw everything
    screen.fill(BLACK)
    screen.blit(background, (shake_x, shake_y))

    # Draw pellets based on current maze state
    for i in range(ROWS):
        for j in range(COLS):
            if maze[i][j] == '.':
                x = j * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2 + shake_x
                y = i * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2 + shake_y
                pygame.draw.circle(screen, WHITE, (x, y), 2 * SCALE)
            elif maze[i][j] == 'o':
                x = j * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2 + shake_x
                y = i * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2 + shake_y
                pygame.draw.circle(screen, WHITE, (x, y), 4 * SCALE)

    pacman.draw()
    for ghost in ghosts:
        ghost.draw()

    # Draw score popups (floating text)
    for popup in score_popups:
        alpha = min(255, popup['timer'] * 6)
        popup_text = popup_font.render(popup['text'], True, CYAN)
        popup_text.set_alpha(alpha)
        rect = popup_text.get_rect(center=(int(popup['x']), int(popup['y'])))
        screen.blit(popup_text, rect)

    # Draw score and lives
    score_text = score_font.render(f"Score: {score}", True, WHITE)
    screen.blit(score_text, (SCREEN_WIDTH - score_text.get_width() - 10, SCREEN_HEIGHT - 34))
    lives_text = score_font.render(f"Lives:", True, WHITE)
    screen.blit(lives_text, (10, SCREEN_HEIGHT - 34))
    for lf in range(pacman.lives):
        lx = 90 + lf * 25
        ly = SCREEN_HEIGHT - 20
        pygame.draw.arc(screen, YELLOW,
                        (lx - 8, ly - 8, 16, 16),
                        math.radians(30), math.radians(330), 8)

    # Display game over
    if game_over:
        text = congratulations_font.render("GAME OVER", True, RED)
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        shadow = congratulations_font.render("GAME OVER", True, BLACK)
        shadow_rect = shadow.get_rect(center=(SCREEN_WIDTH // 2 + 4, SCREEN_HEIGHT // 2 + 4))
        screen.blit(shadow, shadow_rect)
        screen.blit(text, text_rect)

    # Display congratulations message when game is completed
    if game_completed:
        if congratulations_timer > 0:
            congratulations_timer -= 1
            # Create pulsating effect based on timer
            scale_factor = 1.0 + 0.2 * abs(math.sin(congratulations_timer * 0.05))

            # Render and center the text
            text = congratulations_font.render("Congratulations!", True, GREEN)
            scaled_width = int(text.get_width() * scale_factor)
            scaled_height = int(text.get_height() * scale_factor)
            scaled_text = pygame.transform.scale(text, (scaled_width, scaled_height))

            text_rect = scaled_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            screen.blit(scaled_text, text_rect)

            # Add a shadow effect
            shadow_text = congratulations_font.render("Congratulations!", True, BLACK)
            shadow_scaled = pygame.transform.scale(shadow_text, (scaled_width, scaled_height))
            shadow_rect = shadow_scaled.get_rect(center=(SCREEN_WIDTH // 2 + 4, SCREEN_HEIGHT // 2 + 4))
            screen.blit(shadow_scaled, shadow_rect)
            screen.blit(scaled_text, text_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()