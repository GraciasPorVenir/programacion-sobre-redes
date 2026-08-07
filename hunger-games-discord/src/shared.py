from discord import Interaction, Color, Embed
from contextlib import asynccontextmanager


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


type Vector2 = tuple[int, int]


def clamp(x: float | int, min_n: int = 0, max_n: int = 100) -> int:
    return max(min_n, min(max_n, round(float(x))))


def sum_vector2(v1: Vector2, v2: Vector2) -> Vector2:
    return (v1[0] + v2[0], v1[1] + v2[1])
