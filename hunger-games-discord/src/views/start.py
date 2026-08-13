from bot import Bot
from discord import ui, Interaction, ButtonStyle, Color


class StartView(ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)
        self.bot: Bot = bot

    @discord.ui.button(label="Empezar", style=ButtonStyle.green, custom_id="btn_start")
    async def menu_button(self, interaction: Interaction, button: ui.Button):
        id = interaction.user.id
        game = self.bot.game

        if id not in game.locations:
            await interaction.response.send_message(
                "No estás anotado en los juegos.", ephemeral=True
            )
            return

        embed = discord.Embed(
            title="🎮 Menú de los Juegos",
            description="Aquí tienes tus opciones actuales:",
            color=Color.blue(),
        )
        embed.add_field(
            name="Acciones", value="Opción A, Opción B, Opción C", inline=False
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)
