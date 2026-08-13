from typing import Self
from dataclasses import dataclass, field
from math import sqrt
from random import randint
from shared import Vector2, clamp, read_json
from .tribute import Tribute


@dataclass
class Zone:
    celsius: int
    humidity: int
    pressure: int
    wind: int
    tributes: dict[str, Tribute] = field(default_factory=dict)

    def set_tributes(self, id: str, tribute: Tribute | None = None):
        if tribute is None and id in self.tributes:
            self.tributes.pop(id)
        else:
            self.tributes[id] = tribute

    @classmethod
    def create(cls, coords: Vector2) -> Self:
        UNITS: float = 60.0
        norm_dist: float = min(1.0, sqrt(coords[0] ** 2 + coords[1] ** 2) / UNITS)
        pole: int = clamp(int((norm_dist**1.5) * 100 + randint(-10, 10)))

        # Mientras más lejos de (0, 0), climas más fríos/calientes
        celsius: int = clamp(
            int(20 + 0.8 * pole * (sum(coords) / UNITS) + randint(-5, 5)), -60, 60
        )

        # Celsius alto -> presión baja; Celsius bajo -> presión alta.
        pressure: int = clamp(int(60 - (celsius * 0.5) + randint(-15, 15)), 20, 100)

        # Alta temperatura + Baja presión = Poca humedad.
        heat_factor: float = max(0, celsius) / 50.0
        pressure_deficit: float = (100 - pressure) / 80.0

        # Base de humedad alta - el calor y la baja presión
        humidity: int = clamp(
            int(90 - (heat_factor * 40) - (pressure_deficit * 30) + randint(-15, 15)),
            10,
        )
        return cls(celsius, humidity, pressure, randint(20, 100))

    async def pair_tribute(self, id: str) -> None:
        if id not in self.tributes:
            return None
        if self.tributes[id].is_moving:
            return
        c_tribute = self.tributes[id]
        tributes_to_pair = []
        for key, tribute in self.tributes.items():
            if tribute.paired_with != None or key == c_tribute.id:
                continue
            if c_tribute.luck - 10 < tribute.luck < c_tribute + 10:
                tributes_to_pair.append(key)

        paired = False
        for pid in tributes_to_pair:
            if randint(0, 1) == 1 and not paired:
                paired = True
            if pid in self.tributes:
                self.tributes[pid].paired_with = c_tribute.username if paired else None
                self.tributes

        if paired:
            return
