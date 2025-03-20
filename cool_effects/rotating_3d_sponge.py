import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math

def generate_menger(level, x, y, z, s, cubes, s_initial, colorA, colorB):
    """Generate the Menger sponge recursively by adding cubes to the list."""
    if level == 0:
        # Compute distance from origin for color gradient
        d = math.sqrt(x**2 + y**2 + z**2)
        t = d / (s_initial / 2)
        # Interpolate between colorA and colorB
        color = [colorA[c] + t * (colorB[c] - colorA[c]) for c in range(3)]
        cubes.append((x, y, z, s, color))
    else:
        # Subdivide into 27 cubes, keep those with at least two non-zero offsets
        for i in [-1, 0, 1]:
            for j in [-1, 0, 1]:
                for k in [-1, 0, 1]:
                    if (abs(i) == 1) + (abs(j) == 1) + (abs(k) == 1) >= 2:
                        generate_menger(
                            level - 1,
                            x + i * s / 3,
                            y + j * s / 3,
                            z + k * s / 3,
                            s / 3,
                            cubes,
                            s_initial,
                            colorA,
                            colorB
                        )

def draw_cube(x, y, z, size, color):
    """Draw a cube at (x, y, z) with given size and color."""
    glColor3f(*color)  # Use direct color instead of materials
    glBegin(GL_QUADS)
    # Front face
    glNormal3f(0, 0, 1)
    glVertex3f(x - size / 2, y - size / 2, z + size / 2)
    glVertex3f(x + size / 2, y - size / 2, z + size / 2)
    glVertex3f(x + size / 2, y + size / 2, z + size / 2)
    glVertex3f(x - size / 2, y + size / 2, z + size / 2)
    # Back face
    glNormal3f(0, 0, -1)
    glVertex3f(x - size / 2, y - size / 2, z - size / 2)
    glVertex3f(x - size / 2, y + size / 2, z - size / 2)
    glVertex3f(x + size / 2, y + size / 2, z - size / 2)
    glVertex3f(x + size / 2, y - size / 2, z - size / 2)
    # Left face
    glNormal3f(-1, 0, 0)
    glVertex3f(x - size / 2, y - size / 2, z - size / 2)
    glVertex3f(x - size / 2, y - size / 2, z + size / 2)
    glVertex3f(x - size / 2, y + size / 2, z + size / 2)
    glVertex3f(x - size / 2, y + size / 2, z - size / 2)
    # Right face
    glNormal3f(1, 0, 0)
    glVertex3f(x + size / 2, y - size / 2, z - size / 2)
    glVertex3f(x + size / 2, y + size / 2, z - size / 2)
    glVertex3f(x + size / 2, y + size / 2, z + size / 2)
    glVertex3f(x + size / 2, y - size / 2, z + size / 2)
    # Top face
    glNormal3f(0, 1, 0)
    glVertex3f(x - size / 2, y + size / 2, z - size / 2)
    glVertex3f(x - size / 2, y + size / 2, z + size / 2)
    glVertex3f(x + size / 2, y + size / 2, z + size / 2)
    glVertex3f(x + size / 2, y + size / 2, z - size / 2)
    # Bottom face
    glNormal3f(0, -1, 0)
    glVertex3f(x - size / 2, y - size / 2, z - size / 2)
    glVertex3f(x + size / 2, y - size / 2, z - size / 2)
    glVertex3f(x + size / 2, y - size / 2, z + size / 2)
    glVertex3f(x - size / 2, y - size / 2, z + size / 2)
    glEnd()

def main():
    # Initialize PyGame and set up OpenGL context
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    
    # Set clear color - must be before glClear calls
    glClearColor(0.2, 0.2, 0.2, 1.0)  # Medium gray background
    
    # Set up perspective projection
    gluPerspective(45, display[0] / display[1], 0.1, 500.0)
    glTranslatef(0, 0, -100)  # Move everything back 100 units
    
    # Simplify sponge generation - use level 1 instead of 3
    s_initial = 50  # Smaller initial size
    n = 1  # Much less complex
    colorA = [1, 0, 0]  # Red at center
    colorB = [0, 0, 1]  # Blue at edges
    cubes = []
    generate_menger(n, 0, 0, 0, s_initial, cubes, s_initial, colorA, colorB)
    
    # Add a test cube regardless of sponge generation
    cubes.append((0, 0, 0, 20, [0, 1, 0]))  # Green cube at origin
    
    # Turn off lighting initially to rule it out as a problem
    glDisable(GL_LIGHTING)
    
    # Main loop
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    quit()
        
        # Clear the screen
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # Simple rotation
        glRotatef(1, 1, 1, 1)  # Rotate a bit each frame
        
        # Draw test shapes
        glColor3f(1.0, 0.0, 0.0)  # Red
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 50, 0)
        glVertex3f(-50, -50, 0)
        glVertex3f(50, -50, 0)
        glEnd()
        
        # Draw our cubes without lighting effects
        for cube in cubes:
            x, y, z, size, color = cube
            glColor3f(*color)
            draw_cube(x, y, z, size, color)
        
        # Display
        pygame.display.flip()
        pygame.time.wait(10)  # Slow down to see what's happening

if __name__ == "__main__":
    main()