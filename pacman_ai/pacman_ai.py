import pygame
import os
import math

# Initialize Pygame
pygame.init()

# Initialize font
pygame.font.init()

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
    "#......##....##....##......#",
    "#.####.##.########.##.####.#",
    "#..........................#",
    "#.####.#####.##.#####.####.#",
    "#o...........##...........o#",
    "#.####.#####.##.#####.####.#",
    "############################"
]
ROWS = len(maze)  # Now 16
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
        # Add bump state
        self.bumped = False
        self.bump_timer = 0
        self.bump_direction = pygame.math.Vector2(0, 0)
        self.bump_duration = 10  # Frames for bump effect

    def update(self):
        # Handle bump effect
        if self.bumped:
            self.bump_timer -= 1
            if self.bump_timer <= 0:
                self.bumped = False
            else:
                # Move in bump direction
                self.position += self.bump_direction
                return  # Skip regular movement during bump

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
            maze[i] = maze[i][:j] + ' ' + maze[i][j+1:]  # Remove pellet

    def bump(self, ghost_position):
        if not self.bumped:  # Only bump if not already bumped
            self.bumped = True
            self.bump_timer = self.bump_duration
            # Calculate direction away from ghost
            bump_vector = self.position - ghost_position
            if bump_vector.length() > 0:
                self.bump_direction = bump_vector.normalize() * 3  # Bump distance

    def draw(self):
        # Flash when bumped
        color = YELLOW
        if self.bumped and self.bump_timer % 2 == 0:  # Flash every other frame
            color = RED  # Flash red when bumped

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
        self.current_tile = [i, j]
        self.position = pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE)
        self.direction = (0, 1)
        self.speed = SPEED * 0.9
        self.radius = TILE_SIZE * SCALE // 2
        self.color = color

    def update(self):
        i, j = self.current_tile
        di, dj = self.direction
        if self.position == pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE):
            import random
            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            possible = [(di, dj) for di, dj in directions if 0 <= i + di < ROWS and 0 <= j + dj < COLS and maze[i + di][j + dj] != '#']
            if possible:
                self.direction = random.choice(possible)
                di, dj = self.direction
                self.current_tile = [i + di, j + dj]
        # Move towards current tile center
        target = pygame.math.Vector2((self.current_tile[1] + 0.5) * TILE_SIZE * SCALE, (self.current_tile[0] + 0.5) * TILE_SIZE * SCALE)
        vec = target - self.position
        if vec.length() > self.speed:
            self.position += vec.normalize() * self.speed
        else:
            self.position = target

    def draw(self):
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
        pygame.draw.polygon(screen, self.color, body_points)

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
congratulations_timer = 0
congratulations_duration = 180  # 3 seconds at 60 FPS

# Function to check if all food has been eaten
def check_all_food_eaten():
    for row in maze:
        if '.' in row or 'o' in row:
            return False
    return True

# Initialize game objects
pacman = Pacman(1, 1)
ghosts = [
    Ghost(3, 3, RED),
    Ghost(3, 4, PINK),
    Ghost(4, 3, CYAN),
    Ghost(4, 4, ORANGE)
]

# Initialize font
congratulations_font = pygame.font.SysFont('Arial', 48)

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

    # Update game state
    pacman.update()
    for ghost in ghosts:
        ghost.update()

    # Check for collisions between Pacman and ghosts
    for ghost in ghosts:
        distance = (pacman.position - ghost.position).length()
        if distance < pacman.radius + ghost.radius:
            pacman.bump(ghost.position)
            
    # Check if all food has been eaten
    if not game_completed and check_all_food_eaten():
        game_completed = True
        congratulations_timer = congratulations_duration

    # Draw everything
    screen.blit(background, (0, 0))

    # Draw pellets based on current maze state
    for i in range(ROWS):
        for j in range(COLS):
            if maze[i][j] == '.':
                x = j * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                y = i * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                pygame.draw.circle(screen, WHITE, (x, y), 2 * SCALE)
            elif maze[i][j] == 'o':
                x = j * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                y = i * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                pygame.draw.circle(screen, WHITE, (x, y), 4 * SCALE)

    pacman.draw()
    for ghost in ghosts:
        ghost.draw()

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