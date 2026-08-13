from discord.ext import commands
from discord import app_commands, Interaction
from asyncio import sleep
from shared import error_handler
from bot import Bot


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @app_commands.command(name="start")
    @app_commands.checks.has_permissions(administrator=True)
    async def start(self, interaction: Interaction):
        async with error_handler(interaction):
            count: int = 10
            fmt: str = "Los juegos empezarán en: {}"

            await interaction.response.send_message(fmt.format(count))
            while count > 0:
                await interaction.edit_original_response(content=fmt.format(count))
                await sleep(1)
                count -= 1

            await interaction.edit_original_response(
                content="Buena suerte. Usa /explore para empezar a moverte"
            )
            self.bot.game.is_playing = True


async def setup(bot):
    await bot.add_cog(Admin(bot))
