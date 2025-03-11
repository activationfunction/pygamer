import pygame
import sys
import random
import math
import os

# Initialize pygame
pygame.init()
pygame.mixer.init()

# Set up display
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Little Pilot Adventure!")

# Colors - Vibrant, child-friendly colors
SKY_BLUE = (135, 206, 250)  # Lighter blue
WHITE = (255, 255, 255)
YELLOW = (255, 255, 0)
RED = (255, 50, 50)  # Brighter red
BLUE = (30, 144, 255)  # Dodger blue
GREEN = (60, 220, 60)  # Brighter green
ORANGE = (255, 165, 0)
PURPLE = (180, 60, 220)  # Brighter purple
PINK = (255, 105, 180)  # Hot pink
BLACK = (0, 0, 0)

# Create simple shapes for game objects
def create_airplane():
    surface = pygame.Surface((100, 60), pygame.SRCALPHA)
    # Body
    pygame.draw.ellipse(surface, RED, (30, 10, 60, 30))
    # Wings
    pygame.draw.polygon(surface, BLUE, [(40, 25), (10, 40), (30, 40)])
    pygame.draw.polygon(surface, BLUE, [(60, 25), (90, 40), (70, 40)])
    # Tail
    pygame.draw.polygon(surface, YELLOW, [(80, 20), (95, 5), (80, 30)])
    # Cockpit
    pygame.draw.ellipse(surface, BLUE, (40, 15, 20, 15))
    # Windows
    pygame.draw.circle(surface, WHITE, (45, 22), 5)
    pygame.draw.circle(surface, WHITE, (55, 22), 5)
    
    return surface

def create_cloud():
    surface = pygame.Surface((80, 50), pygame.SRCALPHA)
    pygame.draw.ellipse(surface, WHITE, (0, 10, 40, 30))
    pygame.draw.ellipse(surface, WHITE, (20, 0, 40, 30))
    pygame.draw.ellipse(surface, WHITE, (40, 10, 40, 30))
    return surface

def create_star():
    surface = pygame.Surface((40, 40), pygame.SRCALPHA)
    points = []
    center = (20, 20)
    outer_radius = 20
    inner_radius = 10
    for i in range(10):
        radius = outer_radius if i % 2 == 0 else inner_radius
        angle = math.pi / 5 * i
        points.append((center[0] + radius * math.sin(angle),
                       center[1] - radius * math.cos(angle)))
    pygame.draw.polygon(surface, YELLOW, points)
    return surface

def create_balloon(color=None):
    surface = pygame.Surface((40, 60), pygame.SRCALPHA)
    if color is None:
        colors = [RED, BLUE, GREEN, YELLOW, ORANGE, PURPLE, PINK]
        color = random.choice(colors)
    pygame.draw.ellipse(surface, color, (0, 0, 40, 40))
    pygame.draw.line(surface, WHITE, (20, 40), (20, 60), 2)
    return surface

def create_rainbow():
    surface = pygame.Surface((80, 40), pygame.SRCALPHA)
    colors = [RED, ORANGE, YELLOW, GREEN, BLUE, PURPLE]
    for i, color in enumerate(colors):
        pygame.draw.arc(surface, color, (0, 0, 80, 80), math.pi, 0, (6 - i) * 3)
    return surface

def create_sun():
    surface = pygame.Surface((60, 60), pygame.SRCALPHA)
    pygame.draw.circle(surface, YELLOW, (30, 30), 30)
    for i in range(8):
        angle = math.pi / 4 * i
        x1 = 30 + 30 * math.cos(angle)
        y1 = 30 + 30 * math.sin(angle)
        x2 = 30 + 45 * math.cos(angle)
        y2 = 30 + 45 * math.sin(angle)
        pygame.draw.line(surface, YELLOW, (x1, y1), (x2, y2), 3)
    return surface

# Game assets
try:
    # Try to load images if available
    airplane_img = pygame.image.load("airplane.png")
    airplane_img = pygame.transform.scale(airplane_img, (100, 60))
    cloud_img = pygame.image.load("cloud.png")
    cloud_img = pygame.transform.scale(cloud_img, (80, 50))
    star_img = pygame.image.load("star.png")
    star_img = pygame.transform.scale(star_img, (40, 40))
    rainbow_img = pygame.image.load("rainbow.png")
    rainbow_img = pygame.transform.scale(rainbow_img, (80, 40))
    sun_img = pygame.image.load("sun.png")
    sun_img = pygame.transform.scale(sun_img, (60, 60))
    
    # Create balloon images with different colors
    balloon_imgs = []
    for _ in range(5):
        try:
            balloon_img = pygame.image.load("balloon.png")
            balloon_img = pygame.transform.scale(balloon_img, (40, 60))
            balloon_imgs.append(balloon_img)
        except:
            balloon_imgs.append(create_balloon())
except:
    # Use generated assets
    airplane_img = create_airplane()
    cloud_img = create_cloud()
    star_img = create_star()
    rainbow_img = create_rainbow()
    sun_img = create_sun()
    
    # Create balloon images with different colors
    balloon_imgs = []
    for color in [RED, BLUE, GREEN, YELLOW, PURPLE]:
        balloon_imgs.append(create_balloon(color))

# Load sounds - handle missing files gracefully
try:
    engine_sound = pygame.mixer.Sound("engine.wav")
except:
    engine_sound = None
    
try:
    collect_sound = pygame.mixer.Sound("collect.wav")
except:
    collect_sound = None
    
try:
    cheer_sound = pygame.mixer.Sound("cheer.wav")
except:
    cheer_sound = None
    
try:
    pygame.mixer.music.load("background_music.mp3")
    pygame.mixer.music.play(-1)
except:
    pass

# Game font
try:
    # Try to use a more child-friendly font if available
    font = pygame.font.Font("comic.ttf", 48)
    small_font = pygame.font.Font("comic.ttf", 36)
except:
    font = pygame.font.SysFont(None, 48)
    small_font = pygame.font.SysFont(None, 36)

# Game classes
class Airplane:
    def __init__(self):
        self.image = airplane_img
        self.rect = self.image.get_rect(center=(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2))
        self.speed = 5
        self.trail_timer = 0
        self.trail = []
        self.flying_up = False
        self.flying_down = False
        self.engine_playing = False
        
    def update(self, keys):
        # Simple movement for young children
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.rect.x += self.speed
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            self.rect.y -= self.speed
            self.flying_up = True
        else:
            self.flying_up = False
            
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            self.rect.y += self.speed
            self.flying_down = True
        else:
            self.flying_down = False
            
        # Play engine sound if any key is pressed
        any_key_pressed = any([keys[pygame.K_LEFT], keys[pygame.K_a], 
                               keys[pygame.K_RIGHT], keys[pygame.K_d],
                               keys[pygame.K_UP], keys[pygame.K_w],
                               keys[pygame.K_DOWN], keys[pygame.K_s]])
        
        if any_key_pressed and not self.engine_playing and engine_sound:
            engine_sound.play(-1)
            self.engine_playing = True
        elif not any_key_pressed and self.engine_playing and engine_sound:
            engine_sound.stop()
            self.engine_playing = False
            
        # Add trail effect
        self.trail_timer += 1
        if self.trail_timer >= 5:  # Add a trail point every 5 frames
            self.trail_timer = 0
            self.trail.append((self.rect.centerx - 20, self.rect.centery))
            if len(self.trail) > 5:  # Keep only 5 trail points
                self.trail.pop(0)
            
        # Keep airplane on screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top < 0:
            self.rect.top = 0
        if self.rect.bottom > SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
    
    def draw(self):
        # Draw trail
        for i, pos in enumerate(self.trail):
            size = 8 - i  # Trail gets smaller as it goes back
            pygame.draw.circle(screen, WHITE, pos, size)
            
        # Draw airplane with slight tilt based on movement
        rotated_img = self.image
        if self.flying_up:
            rotated_img = pygame.transform.rotate(self.image, 10)
        elif self.flying_down:
            rotated_img = pygame.transform.rotate(self.image, -10)
            
        # Center the rotated image
        rotated_rect = rotated_img.get_rect(center=self.rect.center)
        screen.blit(rotated_img, rotated_rect)

class Cloud:
    def __init__(self):
        self.image = cloud_img
        self.rect = self.image.get_rect()
        self.reset()
        
    def reset(self):
        self.rect.x = SCREEN_WIDTH + random.randint(0, 100)
        self.rect.y = random.randint(0, SCREEN_HEIGHT - self.rect.height)
        self.speed = random.uniform(0.5, 2.0)
        
    def update(self):
        self.rect.x -= self.speed
        if self.rect.right < 0:
            self.reset()
            
    def draw(self):
        screen.blit(self.image, self.rect)

class Collectible:
    def __init__(self, collectible_type=None):
        if collectible_type is None:
            self.type = random.choice(["star", "balloon", "rainbow"])
        else:
            self.type = collectible_type
            
        if self.type == "star":
            self.image = star_img
            self.value = 10
        elif self.type == "balloon":
            self.image = random.choice(balloon_imgs)
            self.value = 5
        else:  # rainbow
            self.image = rainbow_img
            self.value = 20
            
        self.rect = self.image.get_rect()
        self.reset()
        self.collected = False
        self.float_counter = random.uniform(0, 2 * math.pi)
        
    def reset(self):
        self.rect.x = SCREEN_WIDTH + random.randint(0, 200)
        self.rect.y = random.randint(100, SCREEN_HEIGHT - 100)
        self.speed = random.uniform(1.0, 3.0)
        self.collected = False
        
    def update(self):
        self.rect.x -= self.speed
        
        # Add floating movement
        self.float_counter += 0.05
        self.rect.y += math.sin(self.float_counter) * 0.7
        
        if self.rect.right < 0:
            self.reset()
            
    def draw(self):
        if not self.collected:
            screen.blit(self.image, self.rect)
            
            # Add subtle glow effect for stars and rainbows
            if self.type in ["star", "rainbow"] and random.random() > 0.7:
                glow_size = 5 if self.type == "star" else 10
                glow_color = YELLOW if self.type == "star" else WHITE
                pygame.draw.circle(screen, glow_color, 
                                  (self.rect.centerx, self.rect.centery), 
                                  self.rect.width // 2 + glow_size, 2)
        
    def collect(self):
        if not self.collected:
            self.collected = True
            if collect_sound:
                collect_sound.play()
            return self.value
        return 0

class Sun:
    def __init__(self):
        self.image = sun_img
        self.rect = self.image.get_rect(topleft=(SCREEN_WIDTH - 80, 20))
        self.angle = 0
        
    def update(self):
        self.angle += 0.5
        if self.angle >= 360:
            self.angle = 0
            
    def draw(self):
        rotated_img = pygame.transform.rotate(self.image, self.angle)
        rotated_rect = rotated_img.get_rect(center=self.rect.center)
        screen.blit(rotated_img, rotated_rect)

# Game class
class Game:
    def __init__(self):
        self.airplane = Airplane()
        self.clouds = [Cloud() for _ in range(5)]
        self.collectibles = [Collectible() for _ in range(3)]
        self.sun = Sun()
        self.score = 0
        self.high_score = 0
        self.game_active = False
        self.game_over = False
        self.celebration_timer = 0
        self.level = 1
        self.collect_count = 0
        self.level_target = 10
        self.message = ""
        self.message_timer = 0
        
    def start_game(self):
        self.airplane = Airplane()
        self.clouds = [Cloud() for _ in range(5)]
        self.collectibles = [Collectible() for _ in range(3)]
        self.sun = Sun()
        self.score = 0
        self.game_active = True
        self.game_over = False
        self.celebration_timer = 0
        self.level = 1
        self.collect_count = 0
        self.level_target = 10
        self.message = "Let's fly!"
        self.message_timer = 90  # Show for 1.5 seconds
        
    def check_collisions(self):
        for collectible in self.collectibles:
            if not collectible.collected and self.airplane.rect.colliderect(collectible.rect):
                points = collectible.collect()
                self.score += points
                self.collect_count += 1
                
                # Show message based on collectible type
                if collectible.type == "star":
                    self.message = "Twinkle star! +10"
                elif collectible.type == "balloon":
                    self.message = "Balloon! +5"
                else:  # Rainbow
                    self.message = "Rainbow! +20"
                    
                self.message_timer = 60  # Show for 1 second
                
                # Check for level up
                if self.collect_count >= self.level_target:
                    self.level_up()
                    
                # Reset collectible
                collectible.reset()
                
    def level_up(self):
        self.level += 1
        self.collect_count = 0
        self.level_target = min(10 + self.level * 2, 30)  # Increases but caps at 30
        
        # Play celebration sound
        if cheer_sound:
            cheer_sound.play()
            
        # Show celebration message
        self.message = f"Level {self.level}! Well done!"
        self.message_timer = 120  # Show for 2 seconds
        
        # Celebration visual effect
        self.celebration_timer = 180  # 3 seconds of celebration
        
    def draw_background(self):
        # Draw sky with gradient for more visual interest
        for i in range(0, SCREEN_HEIGHT, 4):
            # Gradually change color from top to bottom
            shade = max(0, min(255, 135 - i // 10))
            pygame.draw.rect(screen, (shade, 206 - i // 20, 250), [0, i, SCREEN_WIDTH, 4])
            
        # Draw ground
        ground_height = 30
        pygame.draw.rect(screen, GREEN, [0, SCREEN_HEIGHT - ground_height, SCREEN_WIDTH, ground_height])
        
        # Add some simple grass tufts
        for i in range(0, SCREEN_WIDTH, 40):
            pygame.draw.polygon(screen, (60, 240, 60), 
                              [(i, SCREEN_HEIGHT - ground_height),
                               (i + 10, SCREEN_HEIGHT - ground_height - 10),
                               (i + 20, SCREEN_HEIGHT - ground_height)])
                               
        # Draw sun
        self.sun.draw()
        
    def draw_ui(self):
        # Draw score
        score_text = small_font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (20, 20))
        
        # Draw level
        level_text = small_font.render(f"Level: {self.level}", True, WHITE)
        screen.blit(level_text, (20, 60))
        
        # Draw collection progress
        progress_width = 200
        progress_height = 20
        progress_x = SCREEN_WIDTH - progress_width - 20
        progress_y = 20
        
        # Draw progress background
        pygame.draw.rect(screen, (50, 50, 50), [progress_x, progress_y, progress_width, progress_height])
        
        # Draw progress bar
        progress = min(1.0, self.collect_count / self.level_target)
        pygame.draw.rect(screen, YELLOW, 
                       [progress_x, progress_y, int(progress_width * progress), progress_height])
        
        # Draw progress text
        progress_text = small_font.render(f"{self.collect_count}/{self.level_target}", True, WHITE)
        screen.blit(progress_text, (progress_x + progress_width // 2 - progress_text.get_width() // 2, 
                                  progress_y + 25))
                                  
        # Draw message if active
        if self.message_timer > 0:
            self.message_timer -= 1
            message_text = font.render(self.message, True, WHITE)
            # Add a simple shadow effect for better visibility
            shadow_text = font.render(self.message, True, (0, 0, 0))
            shadow_pos = (SCREEN_WIDTH // 2 - message_text.get_width() // 2 + 2,
                        SCREEN_HEIGHT // 2 - message_text.get_height() // 2 + 2)
            screen.blit(shadow_text, shadow_pos)
            screen.blit(message_text, (SCREEN_WIDTH // 2 - message_text.get_width() // 2,
                                     SCREEN_HEIGHT // 2 - message_text.get_height() // 2))
        
    def draw_celebration(self):
        if self.celebration_timer > 0:
            self.celebration_timer -= 1
            
            # Create random colored fireworks/stars
            for _ in range(5):
                color = random.choice([RED, BLUE, GREEN, YELLOW, PURPLE, ORANGE, PINK])
                x = random.randint(0, SCREEN_WIDTH)
                y = random.randint(0, SCREEN_HEIGHT // 2)
                size = random.randint(3, 10)
                pygame.draw.circle(screen, color, (x, y), size)
                
                # Add some sparkle lines
                for i in range(4):
                    angle = math.pi / 2 * i + random.uniform(0, math.pi / 4)
                    length = random.randint(5, 15)
                    end_x = x + math.cos(angle) * length
                    end_y = y + math.sin(angle) * length
                    pygame.draw.line(screen, color, (x, y), (end_x, end_y), 2)
        
    def draw_start_screen(self):
        # Clear screen with sky blue background
        screen.fill(SKY_BLUE)
        
        # Draw clouds moving in background
        for cloud in self.clouds:
            cloud.update()
            cloud.draw()
            
        # Draw title
        title_text = font.render("Little Pilot Adventure!", True, BLUE)
        screen.blit(title_text, (SCREEN_WIDTH // 2 - title_text.get_width() // 2, 100))
        
        # Draw airplane image
        airplane_large = pygame.transform.scale(airplane_img, (200, 120))
        screen.blit(airplane_large, (SCREEN_WIDTH // 2 - airplane_large.get_width() // 2, 200))
        
        # Draw instruction
        if self.game_over:
            msg = "GOOD JOB! Play Again?"
        else:
            msg = "Press SPACE to Start!"
            
        instruction_text = font.render(msg, True, RED)
        screen.blit(instruction_text, 
                  (SCREEN_WIDTH // 2 - instruction_text.get_width() // 2, 350))
        
        # Draw controls
        controls_text = small_font.render("Use Arrow Keys to Fly!", True, BLACK)
        screen.blit(controls_text, 
                  (SCREEN_WIDTH // 2 - controls_text.get_width() // 2, 430))
        
        # Draw high score
        if self.high_score > 0:
            high_score_text = small_font.render(f"High Score: {self.high_score}", True, ORANGE)
            screen.blit(high_score_text, 
                      (SCREEN_WIDTH // 2 - high_score_text.get_width() // 2, 500))
        
    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            # Process events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE and not self.game_active:
                        self.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        # Easy way for parents to exit the game
                        running = False
                        
            keys = pygame.key.get_pressed()
            
            if self.game_active:
                # Update game objects
                self.airplane.update(keys)
                
                for cloud in self.clouds:
                    cloud.update()
                
                for collectible in self.collectibles:
                    collectible.update()
                    
                self.sun.update()
                
                # Check for collisions with collectibles
                self.check_collisions()
                
                # Draw game elements
                self.draw_background()
                
                for cloud in self.clouds:
                    cloud.draw()
                    
                for collectible in self.collectibles:
                    collectible.draw()
                    
                self.airplane.draw()
                
                # Draw UI elements
                self.draw_ui()
                
                # Draw celebration effects if active
                self.draw_celebration()
                
            else:
                # Show start/game over screen
                self.draw_start_screen()
            
            # Update display and cap the framerate
            pygame.display.flip()
            clock.tick(60)
        
        pygame.quit()
        sys.exit()

# Run the game
if __name__ == "__main__":
    game = Game()
    game.run()