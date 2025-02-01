import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Game constants
WIDTH, HEIGHT = 1200, 600
TERRAIN_SEGMENT_LENGTH = 50
GRAVITY = 0.5
FRICTION = 0.96
BIKE_ACCEL = 0.3
TILT_SPEED = 1.5
CAMERA_SMOOTHNESS = 0.1

# Colors
SKY_BLUE = (135, 206, 235)
EARTH_BROWN = (139, 69, 19)
BIKE_COLOR = (255, 0, 0)
BONUS_COLOR = (255, 215, 0)

class Terrain:
    def __init__(self):
        self.points = []
        self.current_x = 0
        self.generate_initial_terrain()
        
    def generate_initial_terrain(self):
        y = HEIGHT // 2
        for _ in range(WIDTH // TERRAIN_SEGMENT_LENGTH + 2):
            self.points.append((self.current_x, y))
            self.current_x += TERRAIN_SEGMENT_LENGTH
            y += random.randint(-50, 50)
            y = max(200, min(HEIGHT - 100, y))
            
    def update_terrain(self, bike_x):
        while self.points[-1][0] < bike_x + WIDTH:
            last_x, last_y = self.points[-1]
            new_y = last_y + random.randint(-50, 50)
            new_y = max(200, min(HEIGHT - 100, new_y))
            self.points.append((last_x + TERRAIN_SEGMENT_LENGTH, new_y))
            
class Bike:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.speed = 0
        self.tilt = 0
        self.balance = 0
        self.score = 0
        
    def update(self, terrain_points, dt):
        # Apply gravity and friction
        self.speed *= FRICTION
        self.y += GRAVITY
        
        # Move bike horizontally
        self.x += self.speed
        
        # Get current terrain segment
        current_segment = self.get_current_segment(terrain_points)
        terrain_height = self.get_terrain_height(current_segment)
        
        # Maintain bike on terrain
        self.y = terrain_height - 20
        self.balance = current_segment[1][1] - current_segment[0][1]
        
        # Auto-balancing
        self.tilt += (-self.balance * 0.1 - self.tilt) * 0.1
        
    def get_current_segment(self, points):
        for i in range(len(points)-1):
            if points[i][0] <= self.x <= points[i+1][0]:
                return (points[i], points[i+1])
        return (points[0], points[1])
    
    def get_terrain_height(self, segment):
        x1, y1 = segment[0]
        x2, y2 = segment[1]
        t = (self.x - x1) / (x2 - x1)
        return y1 * (1 - t) + y2 * t

class Bonus:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.collected = False

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.terrain = Terrain()
        self.bike = Bike(100, HEIGHT//2)
        self.camera_x = 0
        self.bonuses = self.generate_bonuses()
        
    def generate_bonuses(self):
        bonuses = []
        for _ in range(20):
            x = random.randint(500, 5000)
            y = random.randint(200, HEIGHT - 200)
            bonuses.append(Bonus(x, y))
        return bonuses
    
    def handle_input(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_UP]:
            self.bike.speed += BIKE_ACCEL
        if keys[pygame.K_DOWN]:
            self.bike.speed -= BIKE_ACCEL
        if keys[pygame.K_LEFT]:
            self.bike.tilt -= TILT_SPEED
        if keys[pygame.K_RIGHT]:
            self.bike.tilt += TILT_SPEED
        
    def update_camera(self):
        target_x = self.bike.x - WIDTH//2
        self.camera_x += (target_x - self.camera_x) * CAMERA_SMOOTHNESS
        
    def draw_terrain(self):
        points = self.terrain.points
        for i in range(len(points)-1):
            x1 = points[i][0] - self.camera_x
            y1 = points[i][1]
            x2 = points[i+1][0] - self.camera_x
            y2 = points[i+1][1]
            if x2 < 0 or x1 > WIDTH:
                continue
            pygame.draw.line(self.screen, EARTH_BROWN, (x1, y1), (x2, y2), 5)
            
    def draw_bike(self):
        bike_x = self.bike.x - self.camera_x
        bike_y = self.bike.y
        
        # Draw bike body
        length = 40
        angle = math.radians(self.bike.tilt)
        end_x = bike_x + math.cos(angle) * length
        end_y = bike_y + math.sin(angle) * length
        pygame.draw.line(self.screen, BIKE_COLOR, 
                        (bike_x, bike_y), (end_x, end_y), 5)
        
    def draw_bonuses(self):
        for bonus in self.bonuses:
            if not bonus.collected:
                bx = bonus.x - self.camera_x
                by = bonus.y
                if 0 < bx < WIDTH:
                    pygame.draw.circle(self.screen, BONUS_COLOR, (bx, by), 10)
                    
    def check_bonus_collection(self):
        for bonus in self.bonuses:
            if not bonus.collected and abs(self.bike.x - bonus.x) < 30:
                bonus.collected = True
                self.bike.score += 10
        
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            self.handle_input()
            self.terrain.update_terrain(self.bike.x)
            self.bike.update(self.terrain.points, dt)
            self.update_camera()
            self.check_bonus_collection()
            
            # Drawing
            self.screen.fill(SKY_BLUE)
            self.draw_terrain()
            self.draw_bonuses()
            self.draw_bike()
            
            # Display score
            font = pygame.font.Font(None, 36)
            text = font.render(f"Score: {self.bike.score}", True, (0, 0, 0))
            self.screen.blit(text, (10, 10))
            
            pygame.display.flip()

        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
