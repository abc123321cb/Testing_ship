import math


class Bullet:
    def __init__(self, x: float, y: float, angle: float, owner_id: int):
        self.x = x
        self.y = y
        self.speed = 9.0
        self.vx = math.cos(angle) * self.speed
        self.vy = math.sin(angle) * self.speed
        self.radius = 4
        self.owner_id = owner_id
        self.alive = True

    def update(self, screen_width: int, screen_height: int):
        self.x += self.vx
        self.y += self.vy
        if self.x < 0 or self.x > screen_width or self.y < 0 or self.y > screen_height:
            self.alive = False