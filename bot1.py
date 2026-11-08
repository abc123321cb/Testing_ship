import math

import Ship
from Ship import BaseShipAI, ShipAction, ShipState


class Bot(BaseShipAI):
    def __init__(self):
        self.sweep_angle = 0.0
        self.name = "Really dumb"

    def update(self, state: ShipState) -> ShipAction:
        action = ShipAction()

        if state.energy > 150:
            self.sweep_angle += (2 * math.pi) * 0.01
            action.smartscan = [self.sweep_angle]

        for hit in state.smartscan_results:
            if hit.entity_type == 'enemy' and hit.distance < 400:
                action.thrust = (self.sweep_angle, 4.0)
                if state.energy >= Ship.FIRE_COST:
                    action.fire.append(self.sweep_angle)
            elif hit.entity_type == 'wall' and hit.distance < 50:
                action.thrust = (self.sweep_angle + math.pi, 3.0)

        return action
