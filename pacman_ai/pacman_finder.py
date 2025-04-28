"""
Pacman - Maze Escape

This is a modified version of the classic Pacman game, built using Pygame.
In this version, the objective is to navigate Pacman from the starting position
to the exit of the maze, which is marked by a trophy. The maze contains walls 
and static ghosts that block certain paths. The ghosts are stationary but have 
a gentle shaking animation.

Controls:
- Use the arrow keys (Left, Right, Up, Down) to move Pacman through the maze.

Features:
- Static ghosts block paths, replacing the traditional moving ghosts.
- A trophy marks the exit, providing a clear goal.
- Pellets are still present and can be eaten, but are not required to win.
- Upon reaching the exit, a congratulatory message is displayed.
"""

import pygame
import os
import math

# Initialize Pygame
pygame.init()
pygame.font.init()
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

maze = [
    "########################################",  # 40 cols
    "#..............##......................#",
    "#.######.#####.##.#####.######.....#...#", # Adjusted path
    "#.#....#.#...#....#...#.#....#.#.#.#.#.#",
    "#.#.##.#.#.#.#.##.#.#.#.#.##.#.#.#.#.#.#",
    "#.#.#..#...#.#....#.#...#..#.#...#...#.#",
    "#.#.#.######.#.##.#.######.#.#####.###.#",
    "#.#.#........#....#........#.#...#...#.#",
    "#.#.##########.##.##########.#.#.#####.#",
    "#.#............##............#.#.....#.#",
    "#.############################.#######.#",
    "#..............................#.....#.#",
    "#.#####.######################.#.#####.#",
    "#.#...#........##............#.#.....#.#",
    "#.#.###.######.##.##########.#.#.#####.#",
    "#.#.#..........#....#........#.#.#...#.#",
    "#.#.#.########.#.##.#.######.#.#.#.###.#",
    "#.#.#..#.....#.#....#.#...#..#.#.#...#.#",
    "#.#.##.#.#.#.#.#.##.#.#.#.#.##.#.#####.#",
    "#.#....#.#...#....#...#.#....#.#.....#.#",
    "#.######.#####.##.#####.######.#######.#",
    "#..............##..............#.....#.#",
    "#.######.######################.#.#####.#",
    "#.#....#.......................#.#...#.#",
    "#.######.#####.##.#####.######.#.#.###.#",
    "#..............##..............#.....#.#",
    "#.##########.####.##########.########.#", # Added row
    "#............#....#............#.......#", # Added row
    "########################################"   # 29 rows
]

maze2 = [
    "################################",
    "#..............................#",
    "#.#####.#####.##.#####.#####.#.#",
    "#.#...#.#...#.#..#...#.#...#.#.#",
    "#.#.#.#.#.#.#.##.#.#.#.#.#.#.#.#",
    "#.#.#...#.#.#....#.#.#.#.#...#.#",
    "#.#.#####.#.######.#.#####.#.#.#",
    "#.#.......#........#.......#.#.#",
    "#.########.########.########.#.#",
    "#..........#........#..........#",
    "#.########.#.######.#.########.#",
    "#.#........#........#........#.#",
    "#.#.######.########.######.#.#.#",
    "#.#.#......#........#......#.#.#",
    "#.#.#.####.#.######.#.####.#.#.#",
    "#.#.#.#..#.#.#....#.#.#..#.#.#.#",
    "#.#.#.#.#.#.#.#.##.#.#.#.#.#.#.#",
    "#.#.#...#.#.#.#..#.#.#.#...#.#.#",
    "#.#.#####.#.#.######.#.#####.#.#",
    "#.#.......#.#........#.......#.#",
    "#.#########.#########.########.#",
    "#..............................#",
    "################################"
]

ROWS = len(maze)
COLS = len(maze[0])

# Convert maze to list of lists for mutability and ensure consistent row lengths
COLS = 40  # Set the desired column count
maze = [list(row[:COLS].ljust(COLS, '#')) for row in maze]  # Limit to COLS chars and pad if needed

# Define positions
start_pos = (1, 1)  # Pacman starts here
exit_pos = (16, 26)  # Exit with trophy

# Define static ghost positions (replacing red dots)
ghost_positions = [(4,13), (4,15), (8,13), (8,15), (12,13), (12,15)]

# Mark ghost positions in the maze
for i, j in ghost_positions:
    maze[i][j] = 'G'

# Screen setup
SCREEN_WIDTH = COLS * TILE_SIZE * SCALE
SCREEN_HEIGHT = ROWS * TILE_SIZE * SCALE
LINE_WIDTH = 4 * SCALE
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pacman - Maze Escape")
clock = pygame.time.Clock()

# Background with walls
background = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
background.fill(BLACK)

# For debugging
row_lengths = [len(row) for row in maze]
print(f"ROWS={ROWS}, COLS={COLS}")
print(f"Row lengths after normalization: {row_lengths}")

# Safer wall drawing approach using individual safe access checks
for i in range(ROWS):
    # Skip if row doesn't exist (defensive)
    if i >= len(maze):
        continue
        
    for j in range(len(maze[i])): # Use actual row length, not COLS
        # Safe access check
        try:
            if maze[i][j] == '#':
                x = j * TILE_SIZE * SCALE
                y = i * TILE_SIZE * SCALE

                # Draw top border if top cell isn't a wall
                top_is_wall = False
                if i > 0 and j < len(maze[i-1]):  # Check if top row exists and j is valid
                    top_is_wall = maze[i-1][j] == '#'
                if i == 0 or not top_is_wall:
                    pygame.draw.line(background, BLUE, (x, y), (x + TILE_SIZE * SCALE, y), LINE_WIDTH)

                # Draw left border if left cell isn't a wall
                left_is_wall = False
                if j > 0:  # Check if left column exists
                    left_is_wall = maze[i][j-1] == '#'
                if j == 0 or not left_is_wall:
                    pygame.draw.line(background, BLUE, (x, y), (x, y + TILE_SIZE * SCALE), LINE_WIDTH)

                # Draw bottom border if bottom cell isn't a wall
                bottom_is_wall = False
                if i + 1 < len(maze) and j < len(maze[i+1]):  # Check if bottom row exists and j is valid
                    bottom_is_wall = maze[i+1][j] == '#'
                if i == len(maze) - 1 or not bottom_is_wall:
                    pygame.draw.line(background, BLUE, (x, y + TILE_SIZE * SCALE), (x + TILE_SIZE * SCALE, y + TILE_SIZE * SCALE), LINE_WIDTH)

                # Draw right border if right cell isn't a wall
                right_is_wall = False
                if j + 1 < len(maze[i]):  # Check if right column exists
                    right_is_wall = maze[i][j+1] == '#'
                if j == len(maze[i]) - 1 or not right_is_wall:
                    pygame.draw.line(background, BLUE, (x + TILE_SIZE * SCALE, y), (x + TILE_SIZE * SCALE, y + TILE_SIZE * SCALE), LINE_WIDTH)
        except IndexError as e:
            print(f"ERROR at row={i}, col={j}: {e}")
            continue

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
        self.mouth_angle = 45
        self.mouth_speed = 5

    def update(self):
        global game_completed
        # Animate mouth
        self.mouth_angle += self.mouth_speed
        if self.mouth_angle >= 45 or self.mouth_angle <= 0:
            self.mouth_speed = -self.mouth_speed

        # Decide next move when at tile center
        if self.position == self.target_position:
            self.current_tile = self.target_tile[:]
            i, j = self.current_tile
            di, dj = self.intended_direction
            if 0 <= i + di < ROWS and 0 <= j + dj < COLS and maze[i + di][j + dj] not in ['#', 'G']:
                self.direction = self.intended_direction
            di, dj = self.direction
            if 0 <= i + di < ROWS and 0 <= j + dj < COLS and maze[i + di][j + dj] not in ['#', 'G']:
                self.target_tile = [i + di, j + dj]
                self.target_position = pygame.math.Vector2((j + dj + 0.5) * TILE_SIZE * SCALE, (i + di + 0.5) * TILE_SIZE * SCALE)
            else:
                self.target_tile = self.current_tile[:]
                self.target_position = self.position

            # Check for victory
            if self.current_tile == list(exit_pos):
                game_completed = True

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
            maze[i][j] = ' '
            eat_dot_sound.play()

    def draw(self):
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
        pygame.draw.arc(screen, YELLOW, 
                        (int(self.position.x - self.radius), int(self.position.y - self.radius), 
                         self.radius * 2, self.radius * 2),
                        start_angle, end_angle, self.radius)

# Ghost class (static with shaking)
class Ghost:
    def __init__(self, i, j, color):
        self.position = pygame.math.Vector2((j + 0.5) * TILE_SIZE * SCALE, (i + 0.5) * TILE_SIZE * SCALE)
        self.radius = TILE_SIZE * SCALE // 2
        self.color = color

    def draw(self):
        time = pygame.time.get_ticks() / 1000
        offset_x = 2 * math.sin(2 * math.pi * time + self.position.x / 10)
        offset_y = 2 * math.sin(2 * math.pi * time + self.position.y / 10)
        draw_position = self.position + pygame.math.Vector2(offset_x, offset_y)
        # Ghost body
        body_points = []
        for angle in range(0, 181, 10):
            x = int(draw_position.x + self.radius * math.cos(math.radians(angle - 90)))
            y = int(draw_position.y + self.radius * math.sin(math.radians(angle - 90)))
            body_points.append((x, y))
        for x in range(int(draw_position.x - self.radius), int(draw_position.x + self.radius) + 1, 4):
            y = int(draw_position.y + self.radius * (0.2 * math.sin(x * 0.5) + 0.8))
            body_points.append((x, y))
        pygame.draw.polygon(screen, self.color, body_points)
        # Eyes
        eye_radius = self.radius // 4
        eye_offset = self.radius // 2
        pygame.draw.circle(screen, WHITE, 
                          (int(draw_position.x - eye_offset), int(draw_position.y - eye_offset)), 
                          eye_radius)
        pygame.draw.circle(screen, BLACK, 
                          (int(draw_position.x - eye_offset), int(draw_position.y - eye_offset)), 
                          eye_radius // 2)
        pygame.draw.circle(screen, WHITE, 
                          (int(draw_position.x + eye_offset), int(draw_position.y - eye_offset)), 
                          eye_radius)
        pygame.draw.circle(screen, BLACK, 
                          (int(draw_position.x + eye_offset), int(draw_position.y - eye_offset)), 
                          eye_radius // 2)

# Game objects
pacman = Pacman(*start_pos)
ghost_colors = [RED, PINK, CYAN, ORANGE, GREEN, WHITE]
ghosts = [Ghost(i, j, ghost_colors[k % len(ghost_colors)]) for k, (i, j) in enumerate(ghost_positions)]

# Game state
game_completed = False
congratulations_timer = 0
congratulations_duration = 180  # 3 seconds
congratulations_font = pygame.font.SysFont('Arial', 48)

# Sound
try:
    eat_dot_sound = pygame.mixer.Sound(os.path.join(os.path.dirname(__file__), 'sounds', 'eat_dot.wav'))
    eat_dot_sound.set_volume(0.5)
except:
    eat_dot_sound = pygame.mixer.Sound(buffer=bytearray([0]*44))
    print("Warning: Could not load eat_dot sound file")

# Draw trophy function
def draw_trophy():
    exit_x = exit_pos[1] * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
    exit_y = exit_pos[0] * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
    pygame.draw.circle(screen, YELLOW, (int(exit_x), int(exit_y)), TILE_SIZE * SCALE // 3)

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

    if not game_completed:
        pacman.update()

    # Drawing
    screen.blit(background, (0, 0))
    for i in range(ROWS):
        if i >= len(maze):
            continue
        for j in range(COLS):
            if j < len(maze[i]):  # Check index is valid
                if maze[i][j] == '.':
                    x = j * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                    y = i * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                    pygame.draw.circle(screen, WHITE, (x, y), 2 * SCALE)
                elif maze[i][j] == 'o':
                    x = j * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                    y = i * TILE_SIZE * SCALE + TILE_SIZE * SCALE // 2
                    pygame.draw.circle(screen, WHITE, (x, y), 4 * SCALE)

    for ghost in ghosts:
        ghost.draw()

    draw_trophy()
    pacman.draw()

    if game_completed:
        if congratulations_timer < congratulations_duration:
            congratulations_timer += 1
            scale_factor = 1.0 + 0.2 * abs(math.sin(congratulations_timer * 0.05))
            text = congratulations_font.render("You found the exit!", True, GREEN)
            scaled_text = pygame.transform.scale(text, (int(text.get_width() * scale_factor), int(text.get_height() * scale_factor)))
            text_rect = scaled_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            shadow_text = congratulations_font.render("You found the exit!", True, BLACK)
            shadow_scaled = pygame.transform.scale(shadow_text, (int(text.get_width() * scale_factor), int(text.get_height() * scale_factor)))
            shadow_rect = shadow_scaled.get_rect(center=(SCREEN_WIDTH // 2 + 4, SCREEN_HEIGHT // 2 + 4))
            screen.blit(shadow_scaled, shadow_rect)
            screen.blit(scaled_text, text_rect)

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()