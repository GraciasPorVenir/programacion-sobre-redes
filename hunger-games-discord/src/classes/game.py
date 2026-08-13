from datetime import datetime
from shared import Vector2, read_json, write_json
from .zone import Zone
from .tribute import Tribute


class Game:
    def __init__(self):
        self.zones: dict[Vector2, Zone] = {}
        self.locations: dict[str, Vector2] = {}
        self.is_playing: bool = False

    def set_tribute(self, id: str, new_coords: Vector2 | None = None, **kwargs):
        c_coords: Vector2 | None = self.locations.get(id, None)
        if c_coords != None:
            if new_coords == None:
                self.zones[c_coords].set_tributes(id)
                self.locations.pop(id)
                return
            tribute = self.zones[c_coords].tributes[id]
        else:
            tribute = Tribute(**kwargs)

        new_coords = new_coords if new_coords != None else (0, 0)
        if new_coords not in self.zones:
            self.zones[new_coords] = Zone.create(new_coords)

        if c_coords != None:
            self.zones[c_coords].set_tributes(id)
        if tribute.paired_with == "SYS_PENDING":
            tribute.paired_with = None
        
        self.zones[new_coords].set_tributes(id, tribute)
        self.locations[id] = new_coords

    def purge(self):
        self.zones = {}
        self.locations = {}
        self.is_playing = False

    def get_tribute(self, id: str) -> Tribute | None:
        if id not in self.locations:
            return None
        return self.zones[self.locations[id]].tributes[id]

    async def register_death(self, id: str):
        tribute = self.get_tribute(id)
        if not tribute:
            return
        killer = tribute.paired_with
        edition = datetime.now().strftime("%d/%m/%Y")
        data: dict = await read_json()

        if edition not in data:
            data[edition] = {}
        if id not in data[edition]:
            data[edition][id] = {}

        data[edition][id]["dead_hour"] = datetime.now().strftime("%H:%M:%S")
        data[edition][id]["death_reason"] = (
            f"Killed by {killer}" if killer != None else "Unknown"
        )

        if killer and killer in self.locations:
            if killer not in data[edition]:
                data[edition][killer] = {}
            kills: list = data[edition][killer].get("kills", [])
            if id not in kills:
                kills.append(id)
            data[edition][killer]["kills"] = kills
        await write_json(data)
