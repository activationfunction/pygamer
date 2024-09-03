import os
import pygame
import sys

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

class Dragon(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = dragon_right
        self.rect = self.image.get_rect()
        self.rect.center = (100, HEIGHT // 2)  # Position dragon at the left side of the screen
        self.facing_right = True
        self.speed = 5

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
    def __init__(self):
        super().__init__()
        self.image = bad_dragon_img
        self.rect = self.image.get_rect()
        self.rect.center = (WIDTH - 100, HEIGHT // 2)  # Position villain near the right edge

def main():
    clock = pygame.time.Clock()
    
    all_sprites = pygame.sprite.Group()
    fireballs = pygame.sprite.Group()
    
    dragon = Dragon()
    
    # Create three instances of the Villain
    villain1 = Villain()
    villain2 = Villain()
    villain3 = Villain()
    
    # Position the villains at different locations
    villain1.rect.center = (WIDTH - 100, HEIGHT // 3)  # Top villain
    villain2.rect.center = (WIDTH - 100, HEIGHT // 2)  # Middle villain
    villain3.rect.center = (WIDTH - 100, HEIGHT * 2 // 3)  # Bottom villain
    
    all_sprites.add(dragon)
    all_sprites.add(villain1)  # Add first villain to the sprite group
    all_sprites.add(villain2)  # Add second villain to the sprite group
    all_sprites.add(villain3)  # Add third villain to the sprite group

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if dragon.facing_right:
                        fireball = Fireball(dragon.rect.midright, 1)
                    else:
                        fireball = Fireball(dragon.rect.midleft, -1)
                    all_sprites.add(fireball)
                    fireballs.add(fireball)

        # Check for collisions between fireballs and the villains
        for fireball in fireballs:
            if pygame.sprite.collide_rect(fireball, villain1) or \
               pygame.sprite.collide_rect(fireball, villain2) or \
               pygame.sprite.collide_rect(fireball, villain3):
                fireball.kill()  # Remove the fireball
                villain1.kill() if pygame.sprite.collide_rect(fireball, villain1) else None
                villain2.kill() if pygame.sprite.collide_rect(fireball, villain2) else None
                villain3.kill() if pygame.sprite.collide_rect(fireball, villain3) else None

        all_sprites.update()

        screen.fill(BLACK)
        all_sprites.draw(screen)
        pygame.display.flip()

        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    os.system("cls")
    main()