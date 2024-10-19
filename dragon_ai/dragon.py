import os
import pygame
import sys
import random

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dragon Game")

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Load images
dragon_right = pygame.image.load("dragon_right.png").convert_alpha()
dragon_left = pygame.image.load("dragon_left.png").convert_alpha()
fireball_img = pygame.image.load("fireball.png").convert_alpha()
bad_dragon_img = pygame.image.load("bad_dragon.png").convert_alpha()  # Load villain image

# Scale images if needed
dragon_right = pygame.transform.scale(dragon_right, (100, 100))
dragon_left = pygame.transform.scale(dragon_left, (100, 100))
fireball_img = pygame.transform.scale(fireball_img, (30, 30))
bad_dragon_img = pygame.transform.scale(bad_dragon_img, (100, 100))  # Scale villain image

# Load sound
explosion_sound = pygame.mixer.Sound("explosion-01.wav")  # Replace with your explosion sound file

class Dragon(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = dragon_right
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT // 2)  # Position dragon at the left side of the screen
        self.facing_right = True
        self.speed = 5
        self.fire_cooldown = 0

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.rect.x -= self.speed
            self.facing_right = False
            self.image = dragon_left
        if keys[pygame.K_RIGHT]:
            self.rect.x += self.speed
            self.facing_right = True
            self.image = dragon_right
        if keys[pygame.K_UP]:
            self.rect.y -= self.speed
        if keys[pygame.K_DOWN]:
            self.rect.y += self.speed

        # Keep dragon on screen
        self.rect.clamp_ip(screen.get_rect())

        # Handle continuous firing
        if keys[pygame.K_SPACE] and self.fire_cooldown == 0:
            self.fire()
            self.fire_cooldown = 10  # Set a cooldown to prevent too rapid firing
        elif self.fire_cooldown > 0:
            self.fire_cooldown -= 1

    def fire(self):
        if self.facing_right:
            fireball = Fireball(self.rect.midright, 1)
        else:
            fireball = Fireball(self.rect.midleft, -1)
        all_sprites.add(fireball)
        fireballs.add(fireball)

class Fireball(pygame.sprite.Sprite):
    def __init__(self, start_pos, direction):
        super().__init__()
        self.image = fireball_img
        self.rect = self.image.get_rect()
        self.rect.center = start_pos
        self.direction = direction
        self.speed = 10
        # Play system sound when fireball is created
        pygame.mixer.Sound("fireball-whoosh-5.mp3").play()  # Replace with a system sound

    def update(self):
        self.rect.x += self.speed * self.direction
        if self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class Villain(pygame.sprite.Sprite):  # Create a Villain class
    def __init__(self, position):
        super().__init__()
        self.original_image = bad_dragon_img
        self.image = self.original_image.copy()
        self.rect = self.image.get_rect()
        self.rect.center = position
        self.health = 20  # Each villain now has 20 health points
        self.darkness = 0  # New attribute to track darkness level

    def hit(self):
        self.health -= 1
        explosion_sound.play()  # Play explosion sound on each hit
        self.darkness += 255 // 20  # Increase darkness by 1/20th of 255
        self.update_image()
        if self.health <= 0:
            self.kill()

    def update_image(self):
        self.image = self.original_image.copy()
        dark = pygame.Surface(self.image.get_size()).convert_alpha()
        dark.fill((0, 0, 0, self.darkness))
        self.image.blit(dark, (0, 0))

def main():
    global all_sprites, fireballs
    clock = pygame.time.Clock()
    
    all_sprites = pygame.sprite.Group()
    fireballs = pygame.sprite.Group()
    villains = pygame.sprite.Group()  # New group for villains
    
    dragon = Dragon()
    
    # Create three instances of the Villain
    villain_positions = [
        (WIDTH - 100, HEIGHT // 3),
        (WIDTH - 100, HEIGHT // 2),
        (WIDTH - 100, HEIGHT * 2 // 3)
    ]
    
    for position in villain_positions:
        villain = Villain(position)
        villains.add(villain)
        all_sprites.add(villain)
    
    all_sprites.add(dragon)

    running = True
    last_destroyed_position = None
    enemies_destroyed = 0
    font = pygame.font.Font(None, 74)
    win_text = font.render("You Won!", True, WHITE)
    win_rect = win_text.get_rect(center=(WIDTH//2, HEIGHT//2))
    continue_text = font.render("Press c to continue", True, WHITE)
    continue_rect = continue_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
    level_won = False

    def reset_game():
        nonlocal enemies_destroyed, last_destroyed_position, level_won
        enemies_destroyed = 0
        last_destroyed_position = None
        level_won = False
        all_sprites.empty()
        fireballs.empty()
        villains.empty()
        all_sprites.add(dragon)
        for position in villain_positions:
            villain = Villain(position)
            villains.add(villain)
            all_sprites.add(villain)

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_c and level_won:
                    reset_game()

        # Check for collisions between fireballs and the villains
        for fireball in fireballs:
            hit_villains = pygame.sprite.spritecollide(fireball, villains, False)
            for villain in hit_villains:
                last_destroyed_position = villain.rect.center
                villain.hit()  # Reduce villain's health, play sound, and darken image
                fireball.kill()  # Remove the fireball
                if villain.health <= 0:
                    enemies_destroyed += 1

        # If all villains are destroyed, spawn a new one
        if len(villains) == 0 and enemies_destroyed < 5:
            available_positions = [pos for pos in villain_positions if pos != last_destroyed_position]
            new_position = random.choice(available_positions)
            new_villain = Villain(new_position)
            villains.add(new_villain)
            all_sprites.add(new_villain)

        all_sprites.update()

        screen.fill(BLACK)
        all_sprites.draw(screen)

        if enemies_destroyed >= 5:
            level_won = True
            screen.blit(win_text, win_rect)
            screen.blit(continue_text, continue_rect)
        
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    os.system("cls")
    main()