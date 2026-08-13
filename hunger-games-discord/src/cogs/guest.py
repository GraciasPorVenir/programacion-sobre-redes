from discord.ext import commands
from discord import app_commands, Interaction
from bot import Bot
from shared import error_handler


class Guest(commands.Cog):
    def __init__(self, bot):
        self.bot: Bot = bot

    @app_commands.command(name="sign", description="Anotarte a los juegos")
    async def sign(self, interaction: Interaction):
        async with error_handler(interaction):
            if self.bot.game.is_playing:
                raise Exception("No puedes anotarte cuando los juegos empezaron.")
            user = interaction.user
            if user.id in self.bot.game.locations:
                raise Exception("Ya estás anotado.")
            self.bot.game.set_tribute(user.id, (0, 0), username=user.name)
            await interaction.response.send_message(
                "Te anotaste a los juegos.", ephemeral=True
            )

    @app_commands.command(
        name="unsign", description="Dar de baja inscripción a los juegos"
    )
    async def unsign(self, interaction: Interaction):
        async with error_handler(interaction):
            if self.bot.game.is_playing:
                raise Exception("No puedes salir cuando los juegos empezaron.")
            self.bot.game.set_tribute(interaction.user.id)
            await interaction.response.send_message(
                "Ya no estás en los juegos.", ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(Guest(bot))
