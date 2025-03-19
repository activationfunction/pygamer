import pygame
import sys
import math
import random
import os
from pygame.locals import *

class Laser:
    """Laser projectile fired by the player"""
    
    def __init__(self, x, y, z, angle_h, angle_v):
        self.x = x
        self.y = y
        self.z = z
        self.angle_h = angle_h
        self.angle_v = angle_v
        self.speed = 10
        self.active = True
        self.life = 100  # Laser disappears after traveling a certain distance
        
    def update(self):
        """Update laser position"""
        # Move in the direction of player's view
        self.x += -math.sin(math.radians(self.angle_h)) * self.speed
        self.z += -math.cos(math.radians(self.angle_h)) * self.speed
        self.y += math.sin(math.radians(self.angle_v)) * self.speed
        
        # Reduce life
        self.life -= 1
        if self.life <= 0:
            self.active = False


class Player:
    """Player's spaceship"""
    
    def __init__(self):
        # Position
        self.x = 0
        self.y = 0
        self.z = 0
        
        # Orientation
        self.angle_h = 0  # Horizontal angle (yaw - left/right)
        self.angle_v = 0  # Vertical angle (pitch - up/down)
        
        # Stats
        self.score = 0
        self.rings_passed = 0
        self.asteroids_destroyed = 0
        
        # Weapon
        self.lasers = []
        self.shoot_cooldown = 0
        
    def update(self, keys):
        """Update player position and state based on input"""
        if keys[K_UP]:
            self.angle_v -= 2
        if keys[K_DOWN]:
            self.angle_v += 2
        if keys[K_LEFT]:
            self.angle_h -= 2
        if keys[K_RIGHT]:
            self.angle_h += 2
        
        # Clamp vertical angle to prevent flipping
        self.angle_v = max(-80, min(80, self.angle_v))
        
        # Normalize horizontal angle
        self.angle_h %= 360
        
        # Move forward constantly (auto-pilot style for easier controls)
        forward_speed = 2
        self.x += -math.sin(math.radians(self.angle_h)) * forward_speed
        self.z += -math.cos(math.radians(self.angle_h)) * forward_speed
        self.y += math.sin(math.radians(self.angle_v)) * forward_speed
        
        # Handle shooting
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= 1
    
    def shoot(self):
        """Fire a laser projectile"""
        if self.shoot_cooldown <= 0:
            self.lasers.append(Laser(self.x, self.y, self.z, self.angle_h, self.angle_v))
            self.shoot_cooldown = 10  # Cooldown between shots
            return True
        return False
    
    def update_lasers(self):
        """Update all active lasers"""
        for laser in self.lasers[:]:
            laser.update()
            if not laser.active:
                self.lasers.remove(laser)


class SpaceGame:
    """Main game class for the 3D space flight simulator"""
    
    # Game constants
    WIDTH, HEIGHT = 800, 600
    FOV = 60  # Field of view
    SPEED = 2
    TURN_SPEED = 2
    MAX_DISTANCE = 1000
    
    # Colors
    BLACK = (0, 0, 0)
    WHITE = (255, 255, 255)
    RED = (255, 0, 0)
    GREEN = (0, 255, 0)
    BLUE = (0, 0, 255)
    YELLOW = (255, 255, 0)
    PURPLE = (255, 0, 255)
    CYAN = (0, 255, 255)
    ORANGE = (255, 165, 0)
    
    def __init__(self):
        """Initialize the game"""
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        
        # Set up display
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("Space Explorer")
        self.clock = pygame.time.Clock()
        
        # Player
        self.player = Player()
        
        # Game objects
        self.stars = []
        self.planets = []
        self.collectibles = []
        self.rings = []
        self.asteroids = []
        
        # Planet facts
        self.planet_facts = {
            "Red Planet": "Mars is called the Red Planet because of its reddish color.",
            "Giant Planet": "Jupiter is the biggest planet in our solar system.",
            "Ringed Planet": "Saturn is famous for its beautiful rings.",
            "Blue Planet": "Earth is called the Blue Planet because it has lots of water.",
            "Hot Planet": "Venus is the hottest planet in our solar system.",
            "Cold Planet": "Neptune is very cold and has strong winds.",
            "Small Planet": "Mercury is the smallest planet in our solar system.",
            "Tilted Planet": "Uranus spins on its side unlike other planets."
        }
        
        # Sounds
        self.sounds = {}
        
        # Number words for educational counting
        self.number_words = ["one", "two", "three", "four", "five", 
                           "six", "seven", "eight", "nine", "ten",
                           "eleven", "twelve", "thirteen", "fourteen", "fifteen",
                           "sixteen", "seventeen", "eighteen", "nineteen", "twenty"]
        
        # Game state
        self.running = False
        self.show_instructions = True
        self.level = 1
        self.level_items_collected = 0
        self.level_time = 0
    
    def initialize_game(self):
        """Set up the initial game state and objects"""
        # Create initial game objects
        self.create_stars(200)
        self.create_planets(3)
        self.create_collectibles(5)
        self.create_rings(3)
        self.create_asteroids(3)
        
        # Load sounds
        self.load_sounds()
        
        # Instructions
        print("\n=== SPACE EXPLORER ===")
        print("Controls:")
        print("- Arrow keys: Move the spaceship")
        print("- Space: Shoot lasers")
        print("- ESC: Quit game")
        print("\nObjectives:")
        print("- Collect items to increase your score")
        print("- Fly through glowing rings")
        print("- Shoot asteroids with your laser")
        print("- Learn about planets as you explore")
        print("- Complete each level to unlock the next one")
        print("\nHave fun exploring space!")
    
    def create_stars(self, num_stars):
        """Create background stars"""
        for _ in range(num_stars):
            self.stars.append({
                'x': random.uniform(-self.MAX_DISTANCE, self.MAX_DISTANCE),
                'y': random.uniform(-self.MAX_DISTANCE, self.MAX_DISTANCE),
                'z': random.uniform(100, self.MAX_DISTANCE),
                'size': random.uniform(1, 3)
            })
    
    def create_planets(self, num_planets):
        """Create planets with educational facts"""
        colors = [self.RED, self.GREEN, self.BLUE, self.YELLOW, self.PURPLE, self.CYAN, self.ORANGE]
        planet_names = list(self.planet_facts.keys())
        
        # Use shuffled list to avoid repeating the same planets
        random.shuffle(planet_names)
        
        for i in range(min(num_planets, len(planet_names))):
            self.planets.append({
                'x': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'y': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'z': random.uniform(300, self.MAX_DISTANCE),
                'radius': random.uniform(50, 150),
                'color': random.choice(colors),
                'name': planet_names[i],
                'fact': self.planet_facts[planet_names[i]],
                'rotation': random.uniform(0, 360)  # For simple animation
            })
    
    def create_collectibles(self, num_collectibles):
        """Create collectible items"""
        for _ in range(num_collectibles):
            self.collectibles.append({
                'x': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'y': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'z': random.uniform(100, self.MAX_DISTANCE),
                'collected': False,
                'color': random.choice([self.YELLOW, self.CYAN, self.ORANGE]),
                'rotation': 0  # For simple animation
            })
    
    def create_rings(self, num_rings):
        """Create rings to fly through"""
        for _ in range(num_rings):
            self.rings.append({
                'x': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'y': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'z': random.uniform(200, self.MAX_DISTANCE),
                'radius': random.uniform(30, 60),
                'passed': False,
                'color': random.choice([self.GREEN, self.BLUE, self.PURPLE]),
                'pulse': 0  # For animation
            })
    
    def create_asteroids(self, num_asteroids):
        """Create asteroids to shoot"""
        for _ in range(num_asteroids):
            self.asteroids.append({
                'x': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'y': random.uniform(-self.MAX_DISTANCE/2, self.MAX_DISTANCE/2),
                'z': random.uniform(200, self.MAX_DISTANCE),
                'radius': random.uniform(10, 30),
                'hit': False,
                'color': (150, 150, 150),  # Gray
                'rotation': random.uniform(0, 360)  # For simple animation
            })
    
    def project_point(self, x, y, z):
        """Project a 3D point to 2D screen coordinates"""
        # Apply player's position and rotation
        x -= self.player.x
        y -= self.player.y
        z -= self.player.z
        
        # Rotate around the Y axis (horizontal)
        cos_h = math.cos(math.radians(self.player.angle_h))
        sin_h = math.sin(math.radians(self.player.angle_h))
        x_rotated = x * cos_h - z * sin_h
        z_rotated = z * cos_h + x * sin_h
        
        # Rotate around the X axis (vertical)
        cos_v = math.cos(math.radians(self.player.angle_v))
        sin_v = math.sin(math.radians(self.player.angle_v))
        y_rotated = y * cos_v - z_rotated * sin_v
        z_rotated = z_rotated * cos_v + y * sin_v
        
        # Perspective projection
        if z_rotated <= 0:  # Behind the camera
            return None
        
        scale = self.FOV / z_rotated
        x_projected = self.WIDTH / 2 + x_rotated * scale
        y_projected = self.HEIGHT / 2 + y_rotated * scale
        
        return (x_projected, y_projected, scale)
    
    def draw_stars(self):
        """Draw stars in the background"""
        for star in self.stars:
            projected = self.project_point(star['x'], star['y'], star['z'])
            if projected:
                x, y, scale = projected
                size = max(1, star['size'] * scale)
                if 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
                    pygame.draw.circle(self.screen, self.WHITE, (int(x), int(y)), int(size))
    
    def draw_planets(self):
        """Draw planets with names and facts"""
        # Sort planets by distance for proper rendering (furthest first)
        sorted_planets = sorted(self.planets, key=lambda p: (p['z'] - self.player.z), reverse=True)
        
        fact_displayed = False  # To avoid multiple facts displaying at the same time
        
        for planet in sorted_planets:
            projected = self.project_point(planet['x'], planet['y'], planet['z'])
            if projected:
                x, y, scale = projected
                radius = int(planet['radius'] * scale)
                
                if radius > 0 and x + radius > 0 and x - radius < self.WIDTH and y + radius > 0 and y - radius < self.HEIGHT:
                    # Draw the planet with a simple gradient for a 3D effect
                    for r in range(radius, 0, -1):
                        color = list(planet['color'])
                        # Darken the color for inner circles to create a 3D effect
                        darkness = (radius - r) / radius * 0.7
                        color = [max(0, c * (1 - darkness)) for c in color]
                        pygame.draw.circle(self.screen, color, (int(x), int(y)), r)
                    
                    # Animate planet rotation (just a simple visual effect)
                    planet['rotation'] = (planet['rotation'] + 0.1) % 360
                    rot_rad = math.radians(planet['rotation'])
                    mark_x = int(x + math.cos(rot_rad) * radius * 0.7)
                    mark_y = int(y + math.sin(rot_rad) * radius * 0.7)
                    mark_size = max(2, int(radius * 0.2))
                    pygame.draw.circle(self.screen, (50, 50, 50), (mark_x, mark_y), mark_size)
                    
                    # Display planet name and fact when close enough
                    distance = math.sqrt((planet['x'] - self.player.x)**2 + 
                                       (planet['y'] - self.player.y)**2 + 
                                       (planet['z'] - self.player.z)**2)
                    
                    if distance < 300:
                        font = pygame.font.Font(None, 24)
                        name_text = font.render(planet['name'], True, self.WHITE)
                        self.screen.blit(name_text, (int(x - name_text.get_width()/2), int(y - radius - 30)))
                        
                        # Show fact when very close
                        if distance < 200 and not fact_displayed:
                            fact_displayed = True
                            fact_font = pygame.font.Font(None, 20)
                            fact_text = fact_font.render(planet['fact'], True, self.YELLOW)
                            self.screen.blit(fact_text, (self.WIDTH//2 - fact_text.get_width()//2, self.HEIGHT - 50))
    
    def draw_collectibles(self):
        """Draw collectible items"""
        for collectible in self.collectibles:
            if not collectible['collected']:
                projected = self.project_point(collectible['x'], collectible['y'], collectible['z'])
                if projected:
                    x, y, scale = projected
                    size = int(10 * scale)
                    
                    if size > 0 and 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
                        # Animate rotation
                        collectible['rotation'] = (collectible['rotation'] + 3) % 360
                        
                        # Draw a star shape for collectibles
                        if size > 5:
                            points = []
                            for i in range(10):
                                angle = math.radians(collectible['rotation'] + i * 36)
                                r = size if i % 2 == 0 else size * 0.5
                                point_x = x + math.cos(angle) * r
                                point_y = y + math.sin(angle) * r
                                points.append((point_x, point_y))
                            pygame.draw.polygon(self.screen, collectible['color'], points)
                        else:
                            # If too small, draw as a circle
                            pygame.draw.circle(self.screen, collectible['color'], (int(x), int(y)), size)
                        
                        # Check for collision with player
                        distance = math.sqrt((collectible['x'] - self.player.x)**2 + 
                                           (collectible['y'] - self.player.y)**2 + 
                                           (collectible['z'] - self.player.z)**2)
                        if distance < 20:  # Collision threshold
                            collectible['collected'] = True
                            self.play_sound("collect")
                            self.player.score += 1
                            # Educational counting
                            if 1 <= self.player.score <= len(self.number_words):
                                print(f"You collected {self.number_words[self.player.score-1]} item{'s' if self.player.score > 1 else ''}!")
    
    def draw_rings(self):
        """Draw rings to fly through"""
        for ring in self.rings:
            if not ring['passed']:
                projected = self.project_point(ring['x'], ring['y'], ring['z'])
                if projected:
                    x, y, scale = projected
                    radius = int(ring['radius'] * scale)
                    
                    if radius > 0 and 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
                        # Animate pulsing
                        ring['pulse'] = (ring['pulse'] + 0.05) % (2 * math.pi)
                        pulse_factor = 0.2 * math.sin(ring['pulse']) + 1.0
                        
                        # Draw ring with some thickness
                        for thickness in range(5, 0, -1):
                            r = int(radius * pulse_factor)
                            if r > 0:
                                pygame.draw.circle(self.screen, ring['color'], (int(x), int(y)), r, 
                                                 max(1, int(thickness * scale)))
                        
                        # Check if player passed through the ring
                        distance = math.sqrt((ring['x'] - self.player.x)**2 + 
                                           (ring['y'] - self.player.y)**2 + 
                                           (ring['z'] - self.player.z)**2)
                        
                        # Check if player is within the ring's radius
                        if distance < ring['radius']:
                            # Check if player is moving in the direction of the ring
                            player_direction = (-math.sin(math.radians(self.player.angle_h)), 
                                              math.sin(math.radians(self.player.angle_v)), 
                                              -math.cos(math.radians(self.player.angle_h)))
                            
                            ring_normal = (0, 0, 1)  # Assuming rings face forward for simplicity
                            
                            # Dot product to determine if facing the right direction (simplification)
                            dot_product = (player_direction[0] * ring_normal[0] + 
                                         player_direction[1] * ring_normal[1] + 
                                         player_direction[2] * ring_normal[2])
                            
                            if dot_product > 0:
                                ring['passed'] = True
                                self.play_sound("ring")
                                self.player.rings_passed += 1
                                self.player.score += 5
                                print(f"You flew through a ring! (+5 points)")
    
    def draw_asteroids(self):
        """Draw asteroids to shoot"""
        for asteroid in self.asteroids:
            if not asteroid['hit']:
                projected = self.project_point(asteroid['x'], asteroid['y'], asteroid['z'])
                if projected:
                    x, y, scale = projected
                    radius = int(asteroid['radius'] * scale)
                    
                    if radius > 0 and 0 <= x < self.WIDTH and 0 <= y < self.HEIGHT:
                        # Simple asteroid drawing (gray circle with craters)
                        pygame.draw.circle(self.screen, asteroid['color'], (int(x), int(y)), radius)
                        
                        # Add some craters for detail
                        asteroid['rotation'] = (asteroid['rotation'] + 0.5) % 360
                        for i in range(3):
                            angle = math.radians(asteroid['rotation'] + i * 120)
                            crater_x = int(x + math.cos(angle) * radius * 0.6)
                            crater_y = int(y + math.sin(angle) * radius * 0.6)
                            crater_radius = max(1, int(radius * 0.3))
                            pygame.draw.circle(self.screen, (100, 100, 100), (crater_x, crater_y), crater_radius)
                        
                        # Check for laser collision
                        for laser in self.player.lasers:
                            laser_distance = math.sqrt((asteroid['x'] - laser.x)**2 + 
                                                     (asteroid['y'] - laser.y)**2 + 
                                                     (asteroid['z'] - laser.z)**2)
                            if laser_distance < asteroid['radius']:
                                asteroid['hit'] = True
                                laser.active = False
                                self.play_sound("explosion")
                                self.player.asteroids_destroyed += 1
                                self.player.score += 10
                                print(f"You destroyed an asteroid! (+10 points)")
                                break
    
    def draw_lasers(self):
        """Draw player's laser projectiles"""
        for laser in self.player.lasers:
            # Draw laser as a line from its current position to a point behind it
            start_point = self.project_point(laser.x, laser.y, laser.z)
            end_point = self.project_point(
                laser.x + math.sin(math.radians(laser.angle_h)) * 10,
                laser.y - math.sin(math.radians(laser.angle_v)) * 10,
                laser.z + math.cos(math.radians(laser.angle_h)) * 10
            )
            
            if start_point and end_point:
                pygame.draw.line(self.screen, self.RED, 
                               (int(start_point[0]), int(start_point[1])),
                               (int(end_point[0]), int(end_point[1])),
                               2)
    
    def draw_hud(self):
        """Draw heads-up display with game information"""
        # Create font
        font = pygame.font.Font(None, 24)
        
        # Score
        score_text = font.render(f"Score: {self.player.score}", True, self.WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Rings passed
        rings_text = font.render(f"Rings: {self.player.rings_passed}", True, self.GREEN)
        self.screen.blit(rings_text, (10, 35))
        
        # Asteroids destroyed
        asteroids_text = font.render(f"Asteroids: {self.player.asteroids_destroyed}", True, self.RED)
        self.screen.blit(asteroids_text, (10, 60))
        
        # Level
        level_text = font.render(f"Level: {self.level}", True, self.CYAN)
        self.screen.blit(level_text, (10, 85))
        
        # Instructions (if in instruction mode)
        if self.show_instructions:
            instruction_font = pygame.font.Font(None, 20)
            instructions = [
                "Arrow keys: Move spaceship",
                "Space: Shoot lasers",
                "ESC: Quit game",
                "Press any key to continue..."
            ]
            
            bg_rect = pygame.Rect(self.WIDTH//2 - 150, self.HEIGHT//2 - 60, 300, 120)
            pygame.draw.rect(self.screen, (0, 0, 0, 180), bg_rect)
            pygame.draw.rect(self.screen, self.WHITE, bg_rect, 2)
            
            for i, text in enumerate(instructions):
                instruction = instruction_font.render(text, True, self.WHITE)
                self.screen.blit(instruction, (self.WIDTH//2 - instruction.get_width()//2, 
                                             self.HEIGHT//2 - 50 + i * 25))
    
    def load_sounds(self):
        """Load game sounds"""
        try:
            self.sounds["shoot"] = pygame.mixer.Sound("sounds/laser.wav")
            self.sounds["collect"] = pygame.mixer.Sound("sounds/collect.wav")
            self.sounds["ring"] = pygame.mixer.Sound("sounds/ring.wav")
            self.sounds["explosion"] = pygame.mixer.Sound("sounds/explosion.wav")
            self.sounds["level_up"] = pygame.mixer.Sound("sounds/level_up.wav")
        except:
            print("Could not load sound files. Continuing without sound.")
    
    def play_sound(self, sound_name):
        """Play a sound if it exists"""
        if sound_name in self.sounds:
            try:
                self.sounds[sound_name].play()
            except:
                pass  # Silently fail if sound doesn't play
    
    def check_level_completion(self):
        """Check if current level is completed and advance if needed"""
        collectibles_collected = sum(1 for c in self.collectibles if c['collected'])
        rings_passed = sum(1 for r in self.rings if r['passed'])
        asteroids_destroyed = sum(1 for a in self.asteroids if a['hit'])
        
        total_items = len(self.collectibles) + len(self.rings) + len(self.asteroids)
        items_completed = collectibles_collected + rings_passed + asteroids_destroyed
        
        # Level is completed when 75% of all items are collected/passed/destroyed
        if items_completed >= total_items * 0.75:
            self.level += 1
            print(f"\nLevel {self.level - 1} completed! Advancing to Level {self.level}...")
            self.play_sound("level_up")
            
            # Add more objects for the next level
            self.create_stars(50)  # Add more stars
            self.create_planets(2)
            self.create_collectibles(self.level + 2)
            self.create_rings(self.level)
            self.create_asteroids(self.level)
            
            # Reset level time
            self.level_time = 0
            
            # Some educational feedback
            if self.level <= 5:
                print(f"Fun fact: Level {self.level} in Roman numerals is {['I', 'II', 'III', 'IV', 'V'][self.level-1]}!")
    
    def draw_instructions(self):
        """Draw game instructions screen"""
        # Fill background
        self.screen.fill(self.BLACK)
        
        # Create title
        title_font = pygame.font.Font(None, 48)
        title = title_font.render("Space Explorer", True, self.CYAN)
        self.screen.blit(title, (self.WIDTH//2 - title.get_width()//2, 50))
        
        # Create instructions text
        instruction_font = pygame.font.Font(None, 28)
        instructions = [
            "Arrow keys: Move spaceship",
            "Space: Shoot lasers",
            "ESC: Quit game",
            "",
            "- Collect stars for points",
            "- Fly through glowing rings",
            "- Shoot asteroids with your laser",
            "- Learn about planets as you explore",
            "",
            "Press any key to start your adventure!"
        ]
        
        for i, text in enumerate(instructions):
            instruction = instruction_font.render(text, True, self.WHITE)
            self.screen.blit(instruction, (self.WIDTH//2 - instruction.get_width()//2, 150 + i * 30))
        
        # Update the display
        pygame.display.flip()
        
        # Wait for a key press to continue
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == QUIT:
                    pygame.quit()
                    sys.exit()
                elif event.type == KEYDOWN:
                    waiting = False
                    self.show_instructions = False
                    self.running = True
    
    def run(self):
        """Main game loop"""
        # Show instructions first
        if self.show_instructions:
            self.draw_instructions()
        
        # Set game as running
        self.running = True
        
        # Main game loop
        while self.running:
            # Handle events
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False
                    elif event.key == K_SPACE:
                        if self.player.shoot():
                            self.play_sound("shoot")
            
            # Get pressed keys
            keys = pygame.key.get_pressed()
            
            # Update player
            self.player.update(keys)
            self.player.update_lasers()
            
            # Update game time
            self.level_time += 1
            
            # Check for level completion
            self.check_level_completion()
            
            # Clear screen
            self.screen.fill(self.BLACK)
            
            # Draw game objects (from furthest to nearest)
            self.draw_stars()
            self.draw_planets()
            self.draw_rings()
            self.draw_collectibles()
            self.draw_asteroids()
            self.draw_lasers()
            
            # Draw HUD
            self.draw_hud()
            
            # Update display
            pygame.display.flip()
            
            # Cap frame rate
            self.clock.tick(60)
        
        # Clean up
        pygame.quit()


# Run the game if this script is executed
if __name__ == "__main__":
    game = SpaceGame()
    game.initialize_game()
    game.run()