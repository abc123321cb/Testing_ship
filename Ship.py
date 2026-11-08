from dataclasses import dataclass
from typing import NamedTuple, Optional
from abc import ABC, abstractmethod
import math

# ---------------------------------------------------------
# RANDOM GAME BALANCE CONSTANTS
# ----------------------------------------------------------
MAX_ENERGY = 200.0
FIRE_COST = 100.0
THRUST_COST_MULT = 2.0  # cost = power * 2
SCAN_COST = 0.1
SMARTSCAN_COST = 5.0
ENERGY_REGEN = 1.0
MAX_THRUST_POWER = 10.0 # no going light speed lol


# ------------------------------------------------------
class SmartScanHit(NamedTuple):
    """Result object returned by smart scans."""
    distance: float
    entity_type: str  # 'wall', 'enemy', 'bullet'


@dataclass(frozen=True)
class ShipState:
    position: tuple[float, float]
    energy: float
    velocity: tuple[float, float]
    accel: tuple[float, float]
    
    # Results from scans from last frame
    scan_results: tuple[float, ...] = ()
    smartscan_results: tuple[SmartScanHit, ...] = ()


class ShipAction:
    def __init__(self):
        self.fire: list[float] = []        # Angles in radians
        self.thrust: tuple[float, float] = (0.0, 0.0)  # (direction_radians, power)
        self.scan: list[float] = []        # Angles in radians
        self.smartscan: list[float] = []   # Angles in radians

    def get_energy_cost(self) -> float:
        """Calculates total energy required for all queued commands."""
        fire_cost = len(self.fire) * FIRE_COST
        
        # Power cannot be negative for cost calculations
        power = max(0.0, float(self.thrust[1])) if len(self.thrust) == 2 else 0.0
        thrust_cost = power * THRUST_COST_MULT
        
        scan_cost = len(self.scan) * SCAN_COST
        smartscan_cost = len(self.smartscan) * SMARTSCAN_COST
        
        return fire_cost + thrust_cost + scan_cost + smartscan_cost

    def is_valid(self, current_energy: float) -> tuple[bool, str]:
        """
        Validates structure, parameter bounds, and energy affordability.
        Returns (is_valid, reason_if_invalid). I know so cool we even have error messages
        """

        # 1. Validate thrust tuple structure
        if not isinstance(self.thrust, (tuple, list)) or len(self.thrust) != 2:
            return False, "Thrust must be a tuple of (direction, power)."
        
        direction, power = self.thrust
        if not isinstance(direction, (int, float)) or not isinstance(power, (int, float)):
            return False, "Thrust direction and power must be numbers."
            
        if power < 0.0:
            return False, "Thrust power cannot be negative." #haha no going backwards to generate power because the cost function is dumb

        # 2. Validate all the others I used a cool way to write error messages
        for angle_list, name in [(self.fire, "fire"), (self.scan, "scan"), (self.smartscan, "smartscan")]:
            if not isinstance(angle_list, list):
                return False, f"Action attribute '{name}' must be a list of floats."
            if not all(isinstance(a, (int, float)) for a in angle_list):
                return False, f"All elements in '{name}' must be numeric angles in radians."

        # 3. Check total energy affordability
        total_cost = self.get_energy_cost()
        if total_cost > current_energy:
            return False, f"Insufficient energy: Required {total_cost:.1f}, available {current_energy:.1f}."

        return True, "Action is valid."


# ---------------------------------------------------------
# PLAYER INTERFACE
# ---------------------------------------------------------
class BaseShipAI(ABC):
    name = "You forgot to give a name your poor creation );"
    @abstractmethod
    def update(self, state: ShipState) -> ShipAction:
        """Override this method to return desired actions each tick."""
        pass


def cast_ray(origin: tuple[float, float], angle: float, width: float, height: float, targets: list[tuple[float, float, float, str]]) -> SmartScanHit:
    """
    Casts a ray from origin along angle and finds the closest intersection.
    targets: list of (x, y, radius, entity_type)
    """
    dx = math.cos(angle)
    dy = math.sin(angle)
    
    eps = 1e-9
    if abs(dx) < eps: dx = eps if dx >= 0 else -eps
    if abs(dy) < eps: dy = eps if dy >= 0 else -eps

    t_min = float('inf')
    closest_type = 'wall'

    # Check wall boundaries
    t_left = (0 - origin[0]) / dx
    if t_left > 0 and 0 <= origin[1] + t_left * dy <= height:
        if t_left < t_min: t_min = t_left

    t_right = (width - origin[0]) / dx
    if t_right > 0 and 0 <= origin[1] + t_right * dy <= height:
        if t_right < t_min: t_min = t_right

    t_top = (0 - origin[1]) / dy
    if t_top > 0 and 0 <= origin[0] + t_top * dx <= width:
        if t_top < t_min: t_min = t_top

    t_bottom = (height - origin[1]) / dy
    if t_bottom > 0 and 0 <= origin[0] + t_bottom * dx <= width:
        if t_bottom < t_min: t_min = t_bottom

    for tx, ty, radius, etype in targets:
        fx = origin[0] - tx
        fy = origin[1] - ty
        b = 2 * (fx * dx + fy * dy)
        c = (fx * fx + fy * fy) - radius * radius
        discriminant = b * b - 4 * c
        
        if discriminant >= 0:
            t_sol = (-b - math.sqrt(discriminant)) / 2.0
            if 0 < t_sol < t_min:
                t_min = t_sol
                closest_type = etype

    return SmartScanHit(distance=t_min, entity_type=closest_type)