from .item import Item
from dataclasses import dataclass, field
from shared import Vector2, read_json
from random import choice


@dataclass
class Tribute:
    username: str
    paired_with: str | None = None
    is_moving: bool = True
    arms: Vector2 = field(default_factory=lambda: (100, 100))
    legs: Vector2 = field(default_factory=lambda: (100, 100))
    health: int = 100
    torso: int = 100
    head: int = 100
    rest: int = 100
    resistance: int = 100
    hydration: int = 100
    satiety: int = 100
    capacity: int = 100
    celsius: int = 35
    luck: int = 0
    inventory: dict[str, dict[str, Item]] = field(default_factory=dict)

    async def get_random_item(self) -> tuple[str, Item] | None:
        catalog: dict = await read_json()
        items_for_odd = {}
        for category, items in catalog.items():
            for name, data in items.items():
                min_luck = data.get("min_luck")
                max_luck = data.get("max_luck")
                meets_min = min_luck is not None and self.luck > min_luck
                meets_max = max_luck is not None and self.luck < max_luck
                if meets_min or meets_max:
                    if category not in items_for_odd:
                        items_for_odd[category] = {}
                    items_for_odd[category][name] = data

        if not items_for_odd:
            return None

        chosen_category = choice(list(items_for_odd.keys()))
        chosen_item = choice(list(items_for_odd[chosen_category].keys()))
        item_data = items_for_odd[chosen_category][chosen_item]["data"]
        if chosen_category not in self.inventory:
            self.inventory[chosen_category] = {}
        if chosen_item not in self.inventory[chosen_category]:
            self.inventory[chosen_category][chosen_item] = Item.create(**item_data)
        else:
            self.inventory[chosen_category][chosen_item].add_item(item_data["uses"])

        return (chosen_item, self.inventory[chosen_category][chosen_item])
