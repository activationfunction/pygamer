import os
import pygame
import random
import sys

# Clear the console
os.system('cls' if os.name == 'nt' else 'clear')

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Frames per second
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Initialize the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Galaga Clone")

# Clock to control FPS
clock = pygame.time.Clock()

# Font for text
font = pygame.font.SysFont(None, 36)

# Load Images (Optional: You can replace these with your own images)
# For simplicity, we'll use simple shapes instead of images.

# Player (Spaceship) class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super(Player, self).__init__()
        self.width = 50
        self.height = 30
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = SCREEN_WIDTH // 2
        self.rect.bottom = SCREEN_HEIGHT - 10
        self.speed = 5
        self.last_shot = pygame.time.get_ticks()
        self.shoot_delay = 60  # 60 milliseconds for more frequent shooting

    def update(self):
        # Get mouse position
        mouse_x, _ = pygame.mouse.get_pos()
        self.rect.centerx = mouse_x

        # Keep the player on the screen
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH

    def shoot(self):
        now = pygame.time.get_ticks()
        if now - self.last_shot > self.shoot_delay:
            self.last_shot = now
            bullet = Bullet(self.rect.centerx, self.rect.top)
            all_sprites.add(bullet)
            bullets.add(bullet)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super(Enemy, self).__init__()
        self.width = 40
        self.height = 30
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = random.randint(0, SCREEN_WIDTH - self.width)
        self.rect.y = random.randint(-100, -40)
        self.speedy = random.randint(2, 6)
        self.speedx = random.randint(-3, 3)

    def update(self):
        self.rect.y += self.speedy
        self.rect.x += self.speedx

        # Bounce off the sides
        if self.rect.left < 0 or self.rect.right > SCREEN_WIDTH:
            self.speedx *= -1

        # Reset position if it goes off the bottom
        if self.rect.top > SCREEN_HEIGHT:
            self.kill()
            global lives
            lives -= 1
            if lives <= 0:
                game_over()

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super(Bullet, self).__init__()
        self.width = 5
        self.height = 10
        self.image = pygame.Surface((self.width, self.height))
        self.image.fill(YELLOW)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -10

    def update(self):
        self.rect.y += self.speedy
        # Kill the bullet if it moves off the screen
        if self.rect.bottom < 0:
            self.kill()

# Explosion class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, center):
        super(Explosion, self).__init__()
        self.image = pygame.Surface((50, 50), pygame.SRCALPHA)
        pygame.draw.circle(self.image, YELLOW, (25, 25), 25)
        self.rect = self.image.get_rect()
        self.rect.center = center
        self.duration = 300  # milliseconds
        self.start_time = pygame.time.get_ticks()

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.start_time > self.duration:
            self.kill()

# Game Over function
def game_over():
    game_over_text = font.render("GAME OVER", True, WHITE)
    score_text = font.render(f"Score: {score}", True, WHITE)
    screen.blit(game_over_text, (SCREEN_WIDTH//2 - game_over_text.get_width()//2, SCREEN_HEIGHT//2 - 50))
    screen.blit(score_text, (SCREEN_WIDTH//2 - score_text.get_width()//2, SCREEN_HEIGHT//2))
    pygame.display.flip()
    pygame.time.delay(3000)
    pygame.quit()
    sys.exit()

# Initialize sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
explosions = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

# Enemy spawn event
ADDENEMY = pygame.USEREVENT + 1
pygame.time.set_timer(ADDENEMY, 1000)  # Spawn enemy every 1 second

# Score and lives
score = 0
lives = 3

# Main game loop
running = True
while running:
    clock.tick(FPS)

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == ADDENEMY:
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)

    # Get the current state of keyboard
    keys = pygame.key.get_pressed()
    if keys[pygame.K_SPACE]:
        player.shoot()

    # Update all sprites
    all_sprites.update()

    # Check for bullet-enemy collisions
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for hit in hits:
        score += 10
        explosion = Explosion(hit.rect.center)
        all_sprites.add(explosion)
        explosions.add(explosion)

    # Check for enemies reaching the bottom or colliding with the player
    enemy_hits_player = pygame.sprite.spritecollide(player, enemies, True)
    if enemy_hits_player:
        lives -= 1
        if lives <= 0:
            game_over()

    # Drawing
    screen.fill(BLACK)
    all_sprites.draw(screen)

    # Draw score and lives
    score_text = font.render(f"Score: {score}", True, WHITE)
    lives_text = font.render(f"Lives: {lives}", True, WHITE)
    screen.blit(score_text, (10, 10))
    screen.blit(lives_text, (SCREEN_WIDTH - lives_text.get_width() - 10, 10))

    # Flip the display
    pygame.display.flip()

pygame.quit()
