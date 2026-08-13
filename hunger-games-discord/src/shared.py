from discord import Interaction, Color, Embed
from contextlib import asynccontextmanager
from json import loads, dumps
from aiofiles import open as aopen
from pathlib import Path

type Vector2 = tuple[int, int]


@asynccontextmanager
async def error_handler(interaction: Interaction):
    try:
        yield
    except Exception as e:
        print(e)
        err = Embed(title="Error", description=str(e), color=Color.red())
        if interaction.response.is_done():
            await interaction.followup.send(embed=err, ephemeral=True)
        else:
            await interaction.response.send_message(embed=err, ephemeral=True)


def clamp(x: float, min_n: int = 0, max_n: int = 100) -> int:
    return max(min_n, min(max_n, round(float(x))))


def sum_vector2(v1: Vector2, v2: Vector2) -> Vector2:
    return (v1[0] + v2[0], v1[1] + v2[1])


HISTORY_PATH = Path(__file__).resolve().parent.parent / ".data" / "history.json"
HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)


async def read_json(filepath: Path = HISTORY_PATH) -> dict:
    if not filepath.exists():
        return {}
    async with aopen(filepath, mode="r", encoding="utf-8") as f:
        data = await f.read()
    return dict(loads(data)) if data else {}


async def write_json(data: dict, filepath: Path = HISTORY_PATH):
    json_data = dumps(data, ensure_ascii=False, indent=4)
    async with aopen(filepath, mode="w", encoding="utf-8") as f:
        await f.write(json_data)
