import math

from Ship import BaseShipAI, ShipAction, ShipState


class Bot(BaseShipAI):
    def __init__(self):
        self.aim_angle = 0.0
        self.name = "can't win"

    def update(self, state: ShipState) -> ShipAction:
        action = ShipAction()
        self.aim_angle = (self.aim_angle + 0.05) % (2 * math.pi)
        action.scan = [self.aim_angle]
        return action
