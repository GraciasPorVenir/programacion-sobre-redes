from typing import Self
from dataclasses import dataclass, field
from math import sqrt
from random import randint
from shared import Vector2, clamp, sum_vector2


@dataclass
class Item:
    weight: int
    points: int
    durabilities: list[int] = field(default_factory=list)


@dataclass
class Tribute:
    username: str
    arms: tuple[int, int] = field(default_factory=lambda: (100, 100))
    legs: tuple[int, int] = field(default_factory=lambda: (100, 100))
    health: int = 100
    torso: int = 100
    head: int = 100
    rest: int = 100
    sanity: int = 100
    resistance: int = 100
    hydration: int = 100
    satiety: int = 100
    capacity: int = 100
    temperature: int = 50
    luck: int = 50
    inventory: dict[str, dict[str, Item]] = field(default_factory=dict)


@dataclass
class Zone:
    danger: int
    temperature: int
    humidity: int
    tributes: dict[str, Tribute] = field(default_factory=dict)

    def set_tributes(self, id: str, tribute: Tribute | None = None):
        if tribute is None and code in self.tributes:
            self.tributes.pop(id)
        else:
            self.tributes[id] = tribute

    @classmethod
    def create(cls, coords: Vector2) -> Self:
        norm_dist: float = min(1.0, sqrt(coords[0] ** 2 + coords[1] ** 2) / 1000.0)
        danger: int = clamp((norm_dist**1.5) * 100 + randint(-10, 10))

        temp: int = clamp(50 + (danger - 50) * 0.8 + randint(-15, 15))
        dryness_factor: float = (danger * 0.4) + (abs(temp - 50) * 0.6)
        humidity: int = clamp(randint(20, 100) - dryness_factor)

        return cls(danger, temp, humidity)


class Game:
    def __init__(self):
        self.zones: dict[Vector2, Zone] = {}
        self.locations: dict[str, Vector2] = {}
        self.is_playing: bool = False

    def set_tribute(
        self, id: str, new_coords: Vector2 = (0, 0), username: str | None = None
    ):
        c_coords: Vector2 = self.locations.get(id, None)
        tribute = (
            self.zones[c_coords].tributes[id]
            if c_coords != None and username == None
            else Tribute(username)
        )
        if c_coords != new_coords:
            if new_coords not in self.zones:
                self.zones[new_coords] = Zone.create(new_coords)
            self.zones[c_coords].set_tributes(id)
            self.zones[n_coords].set_tributes(id, tribute)
