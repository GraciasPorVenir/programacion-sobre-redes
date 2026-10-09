from __future__ import annotations
import random
import enum
from dataclasses import dataclass, asdict

# Corrección de tipo: list[int, int] no es válido, usamos tuple[int, int]
type Matrix = list[list["Slot"]]


class SlotType(enum.IntEnum):
    NO_SLOT = 0
    BORDER = 1
    NORMAL = 2
    GEM = 3


@dataclass(frozen=True)
class Card:
    directions: list[tuple[int, int] | None]  # Corregido a tuple
    player: str

    @classmethod
    def create(cls, player: str):
        d = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        dirs = [random.choice((d[i], None)) for i in range(4)]
        return cls(dirs, player)

    def to_dict(self):
        return asdict(self)


@dataclass
class Slot:
    type: SlotType
    card: Card | None = None

    def to_dict(self) -> dict:
        kwargs = asdict(self)
        kwargs["card"] = self.card.to_dict() if self.card else None
        return kwargs


@dataclass
class TurnReq:
    card: Card
    x: int
    y: int
    vx: int
    vy: int
    matrix: Matrix | None = None
    is_pushed: bool = False

    def get_next_pos(self) -> tuple[int, int]:
        return (self.x + self.vx, self.y + self.vy)

    def get_prev_pos(self) -> tuple[int, int]:
        return (self.x - self.vx, self.y - self.vy)

    def to_dict(self) -> dict:
        kwargs = asdict(self)
        kwargs["card"] = self.card.to_dict()
        if self.matrix:
            kwargs["matrix"] = [[col.to_dict() for col in row] for row in self.matrix]
        return kwargs

    @classmethod
    def create(cls, **kwargs):
        if kwargs.get("card"):
            kwargs["card"] = Card(**kwargs["card"])
        if "matrix" in kwargs:
            del kwargs["matrix"]
        return cls(**kwargs)


@dataclass(frozen=True, kw_only=True)
class MixIn:
    matrix: Matrix
    message: str
    turn: bool = True
    history: list[Matrix] | None = None

    @classmethod
    def _serialize_matrix(cls, matrix):  # Corregido self -> cls y self.matrix -> matrix
        return [
            [
                Slot(
                    type=SlotType(col["type"]),
                    card=Card(**col["card"]) if col.get("card") else None,
                )
                for col in row
            ]
            for row in matrix
        ]
    
    @staticmethod
    def _matrix_to_dict(matrix: Matrix):
        return [[col.to_dict() for col in row] for row in matrix]

    def _history_to_diffs(self) -> list[list[dict]] | None:
        if not self.history or len(self.history) < 2:
            return None
        diffs = []
        for i in range(1, len(self.history)):
            prev = self.history[i-1]
            curr = self.history[i]
            diff = []
            for r in range(5):
                for c in range(5):
                    if prev[r][c].card != curr[r][c].card:
                        diff.append({
                            "r": r, "c": c,
                            "card": curr[r][c].card.to_dict() if curr[r][c].card else None
                        })
            diffs.append(diff)
        return diffs


@dataclass(frozen=True, kw_only=True)
class Hand(MixIn):
    hand: list[Card]
    rhand: list[Card]

    def to_dict(self) -> dict:
        return {
            "hand": [c.to_dict() for c in self.hand],
            "rhand": [c.to_dict() for c in self.rhand],
            "matrix": self._matrix_to_dict(self.matrix),
            "turn": self.turn,
            "message": self.message,
            "history": self._history_to_diffs(),
        }

    @classmethod
    def create(cls, **kwargs):
        for h in ("hand", "rhand"):
            kwargs[h] = [Card(**c) for c in kwargs.get(h, [])]
        kwargs["matrix"] = cls._serialize_matrix(kwargs["matrix"])  # Corregido "matrix"
        if kwargs.get("history"):
            kwargs["history"] = [cls._serialize_matrix(m) for m in kwargs["history"]]
        return cls(**kwargs)


@dataclass(frozen=True, kw_only=True)
class TurnRes(MixIn):
    newcard: Card
    precard: Card

    def to_dict(self) -> dict:
        return {
            "newcard": self.newcard.to_dict(),
            "matrix": self._matrix_to_dict(self.matrix),
            "turn": self.turn,
            "message": self.message,
            "precard": self.precard.to_dict(),
            "history": self._history_to_diffs(),
        }

    @classmethod
    def create(cls, **kwargs):
        kwargs["newcard"] = Card(**kwargs["newcard"])
        kwargs["precard"] = Card(**kwargs["precard"])
        kwargs["matrix"] = cls._serialize_matrix(kwargs["matrix"])  # Corregido "matrix"
        if kwargs.get("history"):
            kwargs["history"] = [cls._serialize_matrix(m) for m in kwargs["history"]]
        return cls(**kwargs)
