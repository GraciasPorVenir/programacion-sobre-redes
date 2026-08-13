from discord.ext import commands
from discord import app_commands, Interaction
from bot import Bot
from shared import Vector2
from random import randint
from shared import error_handler, sum_vector2


class Tribute(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @property
    def game(self):
        return self.bot.game

    @app_commands.command(name="explore", description="Explorar")
    async def explore(self, interaction: Interaction):
        async with error_handler(interaction):
            id = interaction.user.id
            tribute = self.game.get_tribute(id)
            if not self.game.is_playing or not tribute:
                raise Exception("Comando solo para tributos en juego.")

            nc: Vector2 = (randint(-1, 1), randint(-1, 1))

            randitem = await tribute.get_random_item()
            if randitem is None:
                await interaction.response.send_message(f"Nada de nada", ephemeral=True)
            else:
                nameitem, dataitem = randitem

            self.game.set_tribute(id, sum_vector2(self.game.locations[id], nc))


async def setup(bot):
    await bot.add_cog(Tribute(bot))
