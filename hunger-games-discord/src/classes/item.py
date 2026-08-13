from typing import Self
from dataclasses import dataclass, field


@dataclass
class Item:
    points: int
    weight: int = 1
    ratio: int = 0
    uses: list[int] = field(default_factory=list)

    @classmethod
    def create(cls, **kwargs) -> Self:
        uses = kwargs.pop("uses")
        item = cls(**kwargs)
        item.add_item(uses)
        return item

    def add_item(self, use: int):
        self.uses.append(use)
