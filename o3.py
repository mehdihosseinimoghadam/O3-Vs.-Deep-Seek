
#!/usr/bin/env python3
import math
import random
import pygame

# Initialize Pygame
pygame.init()

# Window dimensions
WIDTH, HEIGHT = 1000, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mountain Bike Adventure")

# Colors
SKY_COLOR = (135, 206, 235)
GROUND_COLOR = (80, 50, 20)
BIKE_COLOR = (255, 0, 0)
BONUS_COLOR = (255, 215, 0)
TEXT_COLOR = (0, 0, 0)

clock = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)

# ---------------------------------------------
# Terrain Generation
# ---------------------------------------------
def generate_terrain(length, step):
    """
    Generates a list of points (x, y) along the terrain.
    We use a base sine wave with random perturbations to simulate rugged mountains.
    """
    terrain = []
    amplitude = 80
    frequency = 0.005
    x = 0
    while x < length:
        # Base sine wave and some randomness for rugged features.
        y = HEIGHT - (amplitude * math.sin(frequency * x) + amplitude + random.uniform(-20, 20))
        terrain.append((x, y))
        x += step
    return terrain

# Create terrain
terrain_length = 5000  # total horizontal length of the course
terrain_step = 10      # spacing between points
terrain = generate_terrain(terrain_length, terrain_step)

# ---------------------------------------------
# Bonus (collectible) Generation
# ---------------------------------------------
def generate_bonus_points(terrain, count):
    bonus_points = []
    available_indices = random.sample(range(len(terrain)), count)
    for i in available_indices:
        # Place bonus a little above the ground
        x, ground_y = terrain[i]
        bonus_points.append((x, ground_y - 50))
    return bonus_points

BONUS_COUNT = 20
bonus_points = generate_bonus_points(terrain, BONUS_COUNT)

# ---------------------------------------------
# Bike Physics and Class
# ---------------------------------------------
class Bike:
    def __init__(self):
        # Start somewhere along the left of the terrain
        self.x = 100  
        self.y = self.get_ground_y(self.x)
        self.vx = 0.0         # horizontal velocity
        self.ax = 0.0         # horizontal acceleration
        self.angle = 0.0      # bike tilt angle (radians); 0 means upright
        self.angular_velocity = 0.0
        self.width = 50
        self.height = 20
        self.score = 0        # bonus collected
        self.distance = 0.0   # distance traveled

    def get_ground_y(self, x):
        # Find nearest terrain point for given x (linearly interpolated)
        if x < 0:
            return terrain[0][1]
        if x > terrain[-1][0]:
            return terrain[-1][1]
        index = int(x / terrain_step)
        # Ensure index is in range
        index = min(index, len(terrain) - 2)
        x1, y1 = terrain[index]
        x2, y2 = terrain[index+1]
        # Linear interpolation:
        t = (x - x1) / (x2 - x1)
        return y1 * (1 - t) + y2 * t

    def get_ground_slope(self, x):
        # Calculate approximate slope of the ground at position x
        delta = 1.0
        y1 = self.get_ground_y(x - delta)
        y2 = self.get_ground_y(x + delta)
        slope = math.atan2(y2 - y1, 2 * delta)
        return slope

    def update(self, dt, keys):
        # Accelerate / decelerate (simulate pedal force and friction)
        acceleration = 0.0
        if keys[pygame.K_UP]:
            acceleration = 100.0  # pedal to accelerate
        elif keys[pygame.K_DOWN]:
            acceleration = -80.0  # brake
            
        # Update horizontal acceleration
        self.ax = acceleration - 0.5 * self.vx  # friction drag term
        
        # Update horizontal velocity and position (simple Euler integration)
        self.vx += self.ax * dt
        if self.vx < 0:
            self.vx = 0  # no reversing
        self.x += self.vx * dt
        self.distance = self.x

        # Get ground state at current position
        ground_y = self.get_ground_y(self.x)
        ground_slope = self.get_ground_slope(self.x)

        # Vertical adjustment: we want the bike to stick to the ground.
        # Compute vertical error between the bike’s current y and the ideal ground y offset by a small suspension
        suspension_offset = -5  # bike rides slightly above ground level visually
        error = (ground_y + suspension_offset) - self.y
        
        # Simple spring-damper model for vertical motion to emulate suspension
        spring_k = 10.0
        damping = 3.0
        ay = spring_k * error - damping * 0  # ignoring vertical velocity for simplicity
        # In our simulation, we use the spring to force the y toward ground level.
        self.y += ay * dt
        
        # Adjust the bike’s angle (tilt) with control and balance physics:
        # User input tilt: left/right keys.
        tilt_input = 0.0
        if keys[pygame.K_LEFT]:
            tilt_input = 1.0   # tilt backward
        elif keys[pygame.K_RIGHT]:
            tilt_input = -1.0  # tilt forward
        
        # The ground slope provides a correcting torque to try align the bike perpendicular to the slope.
        desired_angle = -ground_slope  # being upright relative to gravity
        # Add user input effect. The input is added as an additional torque.
        torque = 5 * tilt_input + 2 * (desired_angle - self.angle)
        angular_damping = 3.0
        self.angular_velocity += torque * dt
        self.angular_velocity *= math.exp(-angular_damping * dt)  # damping effect
        self.angle += self.angular_velocity * dt

        # Gradually force the bike's vertical position to match the ground if too far off:
        if abs(error) > 50:
            self.y = ground_y + suspension_offset

    def check_bonus(self, bonus_points):
        # If bike's x position is near a bonus and the vertical difference small, collect it.
        collected = []
        for bp in bonus_points:
            bx, by = bp
            if abs(self.x - bx) < 20 and abs(self.y - by) < 30:
                self.score += 1
                collected.append(bp)
        return collected

    def draw(self, surface, scroll_x):
        # Draw the bike as a rotated rectangle
        bike_rect = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        bike_rect.fill(BIKE_COLOR)
        rotated = pygame.transform.rotate(bike_rect, math.degrees(self.angle))
        rect = rotated.get_rect()
        # Position relative to the screen coordinate system (scroll_x accounts for camera movement)
        screen_x = self.x - scroll_x
        screen_y = self.y - rect.height//2
        surface.blit(rotated, (screen_x - rect.width//2, screen_y))


# ---------------------------------------------
# Main game loop and drawing functions
# ---------------------------------------------
def draw_terrain(surface, scroll_x):
    # Draw the terrain as a polyline.
    # Adjust for scrolling (only draw points in visible region with a margin)
    points = []
    for (x, y) in terrain:
        screen_x = x - scroll_x
        if -50 <= screen_x <= WIDTH + 50:
            points.append((screen_x, y))
    if points:
        # Draw ground polygon to the bottom of the screen
        poly_points = points + [(points[-1][0], HEIGHT), (points[0][0], HEIGHT)]
        pygame.draw.polygon(surface, GROUND_COLOR, poly_points)

def draw_bonus(surface, scroll_x, bonus_points):
    for bp in bonus_points:
        bx, by = bp
        screen_x = bx - scroll_x
        pygame.draw.circle(surface, BONUS_COLOR, (int(screen_x), int(by)), 8)

def main():
    bike = Bike()
    scroll_x = 0
    running = True
    game_time = 0.0
    global bonus_points

    while running:
        dt = clock.tick(60) / 1000.0  # seconds passed this frame
        game_time += dt

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()

        # Update physics
        bike.update(dt, keys)
        collected = bike.check_bonus(bonus_points)
        for c in collected:
            bonus_points.remove(c)

        # Update camera scroll so bike is a bit to the left of center
        scroll_x = bike.x - WIDTH * 0.3
        if scroll_x < 0:
            scroll_x = 0
        if scroll_x > terrain_length - WIDTH:
            scroll_x = terrain_length - WIDTH

        # Draw everything
        screen.fill(SKY_COLOR)
        draw_terrain(screen, scroll_x)
        draw_bonus(screen, scroll_x, bonus_points)
        bike.draw(screen, scroll_x)

        # Display game stats (distance and bonus collected)
        stats_text = FONT.render(f"Distance: {int(bike.distance)}   Bonus: {bike.score}   Time: {game_time:.1f}s", True, TEXT_COLOR)
        screen.blit(stats_text, (10, 10))

        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()

