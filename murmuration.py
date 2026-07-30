import pygame
import random
import math

# --- Configuration ---
WIDTH, HEIGHT = 1200, 800
NUM_BIRDS = 150
BIRD_RADIUS = 3
# The "Rule of Seven": Number of neighbors each bird tracks
NEIGHBOR_COUNT = 7
# Max speed and max force for smooth movement
MAX_SPEED = 4
MAX_FORCE = 0.15
# Weighting for the three core behaviors
ALIGNMENT_WEIGHT = 1.0
COHESION_WEIGHT = 1.0
SEPARATION_WEIGHT = 1.5

class Bird:
    def __init__(self):
        self.position = pygame.Vector2(random.uniform(0, WIDTH), random.uniform(0, HEIGHT))
        self.velocity = pygame.Vector2(random.uniform(-MAX_SPEED, MAX_SPEED), 
                                       random.uniform(-MAX_SPEED, MAX_SPEED))
        self.velocity.set_length(random.uniform(2, MAX_SPEED))
        self.acceleration = pygame.Vector2(0, 0)

    def apply_force(self, force):
        self.acceleration += force

    def update(self):
        self.velocity += self.acceleration
        if self.velocity.length() > MAX_SPEED:
            self.velocity.scale_to_length(MAX_SPEED)
        
        self.position += self.velocity
        self.acceleration *= 0  # Reset acceleration each frame

        # Screen wrap-around (Torus world)
        if self.position.x < 0: self.position.x = WIDTH
        if self.position.x > WIDTH: self.position.x = 0
        if self.position.y < 0: self.position.y = HEIGHT
        if self.position.y > HEIGHT: self.position.y = 0

    def flock(self, birds):
        # 1. Find the N nearest neighbors (Topological Distance)
        # We calculate squared distance to avoid unnecessary sqrt() calls
        distances = []
        for other in birds:
            if other is not self:
                d_sq = self.position.distance_squared_to(other.position)
                distances.append((d_sq, other))
        
        # Sort by distance and take the top NEIGHBOR_COUNT
        distances.sort(key=lambda x: x[0])
        neighbors = [item[1] for item in distances[:NEIGHBOR_COUNT]]

        # 2. Calculate behaviors based ONLY on these neighbors
        alignment = pygame.Vector2(0, 0)
        cohesion = pygame.Vector2(0, 0)
        separation = pygame.Vector2(0, 0)
        
        if not neighbors:
            return

        for neighbor in neighbors:
            # Alignment: Steer towards the average velocity of neighbors
            alignment += neighbor.velocity
            
            # Cohesion: Steer towards the center of mass of neighbors
            cohesion += neighbor.position
            
            # Separation: Steer away from neighbors that are too close
            dist = self.position.distance_to(neighbor.position)
            if dist < 20: # Safety radius
                diff = self.position - neighbor.position
                diff.normalize_ip()
                diff /= (dist + 0.1) # Stronger repulsion when closer
                separation += diff

        # Finalize Alignment
        alignment /= len(neighbors)
        if alignment.length() > 0:
            alignment = (alignment.normalize() * MAX_SPEED) - self.velocity
            if alignment.length() > MAX_FORCE:
                alignment.scale_to_length(MAX_FORCE)

        # Finalize Cohesion
        cohesion /= len(neighbors)
        cohesion -= self.position
        if cohesion.length() > 0:
            cohesion = (cohesion.normalize() * MAX_SPEED) - self.velocity
            if cohesion.length() > MAX_FORCE:
                cohesion.scale_to_length(MAX_FORCE)

        # Finalize Separation
        if separation.length() > 0:
            separation = (separation.normalize() * MAX_SPEED) - self.velocity
            if separation.length() > MAX_FORCE:
                separation.scale_to_length(MAX_FORCE)

        # Apply weighted forces
        self.apply_force(alignment * ALIGNMENT_WEIGHT)
        self.apply_force(cohesion * COHESION_WEIGHT)
        self.apply_force(separation * SEPARATION_WEIGHT)

    def draw(self, screen):
        # Draw a small triangle pointing in the direction of velocity
        angle = math.atan2(self.velocity.y, self.velocity.x)
        p1 = self.position + pygame.Vector2(BIRD_RADIUS, 0).rotate_rad(angle)
        p2 = self.position + pygame.Vector2(-BIRD_RADIUS*2, -BIRD_RADIUS).rotate_rad(angle)
        p3 = self.position + pygame.Vector2(-BIRD_RADIUS*2, BIRD_RADIUS).rotate_rad(angle)
        pygame.draw.polygon(screen, (200, 200, 255), [p1, p2, p3])

def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Starling Murmuration Simulation (Topological Rule of 7)")
    clock = pygame.time.Clock()

    birds = [Bird() for _ in range(NUM_BIRDS)]

    running = True
    while running:
        screen.fill((20, 20, 30)) # Dark night sky
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update and Draw
        for bird in birds:
            bird.flock(birds)
        
        for bird in birds:
            bird.update()
            bird.draw(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
