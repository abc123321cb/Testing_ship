import sys
import math
import pygame
import Ship
import bot1
import bot2
from bullet import Bullet
from Ship import *

pygame.init()

# Setup display constants
SCREEN_WIDTH = 600
SCREEN_HEIGHT = 600
FPS = 60

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("ShipThing - AI Battle Arena")
clock = pygame.time.Clock()


class GameShip:
    def __init__(self, ship_id: int, x: float, y: float, color: tuple, ai: BaseShipAI):
        self.id = ship_id
        self.pos = [x, y]
        self.vel = [0.0, 0.0]
        self.accel = [0.0, 0.0]
        self.energy = Ship.MAX_ENERGY
        self.radius = 16
        self.color = color
        self.name = ai.name
        self.ai = ai
        self.alive = True
        
        self.last_scan_results: list[float] = []
        self.last_smartscan_results: list[SmartScanHit] = []
        self.active_scan_rays: list[tuple[float, float, float]] = []

    def step_ai_and_physics(self, enemy_ship, bullets: list[Bullet]):
        self.energy = min(Ship.MAX_ENERGY, self.energy + Ship.ENERGY_REGEN)

        #make the shipstate
        state = ShipState(
            position=(self.pos[0], self.pos[1]),
            energy=self.energy,
            velocity=(self.vel[0], self.vel[1]),
            accel=(self.accel[0], self.accel[1]),
            scan_results=tuple(self.last_scan_results),
            smartscan_results=tuple(self.last_smartscan_results)
        )

        try:
            action = self.ai.update(state)
        except Exception as e:
            action = ShipAction()

        # Reset frame scan caches
        self.last_scan_results.clear()
        self.last_smartscan_results.clear()
        self.active_scan_rays.clear()
        if (action is None):
            valid = False
        else:
            valid, reason = action.is_valid(self.energy)
        spawned_bullets = []

        if valid:
            cost = action.get_energy_cost()
            self.energy -= cost

            # Process Thrust Acceleration
            direction, power = action.thrust
            self.accel[0] = math.cos(direction) * power * 0.15
            self.accel[1] = math.sin(direction) * power * 0.15

            # Process Firing
            for f_angle in action.fire:
                spawned_bullets.append(Bullet(self.pos[0], self.pos[1], f_angle, self.id))

            # Build Raycast Targets list (excluding self)
            targets = [(enemy_ship.pos[0], enemy_ship.pos[1], enemy_ship.radius, 'enemy')]
            for b in bullets:
                if b.owner_id != self.id:
                    targets.append((b.x, b.y, b.radius, 'bullet'))

            # Process Scans
            for angle in action.scan:
                hit = cast_ray((self.pos[0], self.pos[1]), angle, SCREEN_WIDTH, SCREEN_HEIGHT, targets)
                self.last_scan_results.append(hit.distance)
                self.active_scan_rays.append((angle, hit.distance, False))

            for angle in action.smartscan:
                hit = cast_ray((self.pos[0], self.pos[1]), angle, SCREEN_WIDTH, SCREEN_HEIGHT, targets)
                self.last_smartscan_results.append(hit)
                self.active_scan_rays.append((angle, hit.distance, True))
        else:
            self.accel = [0.0, 0.0]

        # 5. Physics Update
        self.vel[0] = (self.vel[0] + self.accel[0]) * 0.96
        self.vel[1] = (self.vel[1] + self.accel[1]) * 0.96
        
        self.pos[0] += self.vel[0]
        self.pos[1] += self.vel[1]

        # Wall Clamping
        self.pos[0] = max(self.radius, min(SCREEN_WIDTH - self.radius, self.pos[0]))
        self.pos[1] = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.pos[1]))

        return spawned_bullets


# -----------------------------------------------------
# Loop
# ----------------------------------------------------------
ship1 = GameShip(1, 150, 300, (50, 150, 255), bot1.Bot())
ship2 = GameShip(2, 450, 300, (255, 80, 80), bot2.Bot())
bullets: list[Bullet] = []

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    new_bullets_1 = ship1.step_ai_and_physics(ship2, bullets)
    new_bullets_2 = ship2.step_ai_and_physics(ship1, bullets)
    bullets.extend(new_bullets_1 + new_bullets_2)

    # Move bullets & handle collisions
    for bullet in bullets:
        bullet.update(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # Check collision
        if ship1.alive and bullet.owner_id != ship1.id:
            dist1 = math.hypot(bullet.x - ship1.pos[0], bullet.y - ship1.pos[1])
            if dist1 < ship1.radius + bullet.radius:
                ship1.alive = False
                bullet.alive = False
                running = False
                print("Ship " + ship2.name + " won!")

        if ship2.alive and bullet.owner_id != ship2.id:
            dist2 = math.hypot(bullet.x - ship2.pos[0], bullet.y - ship2.pos[1])
            if dist2 < ship2.radius + bullet.radius:
                ship2.alive = False
                bullet.alive = False
                running = False
                print("Ship " + ship1.name + " won!")

    bullets = [b for b in bullets if b.alive]

    screen.fill((20, 24, 32))

    for ship in (ship1, ship2):
        for angle, dist, is_smart in ship.active_scan_rays:
            end_x = ship.pos[0] + math.cos(angle) * dist
            end_y = ship.pos[1] + math.sin(angle) * dist
            ray_color = (255, 200, 0, 80) if is_smart else (0, 255, 200, 40)
            pygame.draw.line(screen, ray_color, ship.pos, (end_x, end_y), 1)

    for bullet in bullets:
        pygame.draw.circle(screen, (255, 255, 100), (int(bullet.x), int(bullet.y)), bullet.radius)

    for ship in (ship1, ship2):
        pygame.draw.circle(screen, ship.color, (int(ship.pos[0]), int(ship.pos[1])), ship.radius)
        ep_ratio = ship.energy / Ship.MAX_ENERGY
        pygame.draw.rect(screen, (0, 150, 255), (ship.pos[0] - 20, ship.pos[1] - 22, int(40 * ep_ratio), 3))

    pygame.display.flip()
    clock.tick(FPS)

pygame.quit()
sys.exit()